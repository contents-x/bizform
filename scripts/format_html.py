"""Indent structural HTML without rewriting text, attributes or inline spacing.

Run with Python 3.10+; no third-party dependencies are required.
"""
import argparse
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
STRUCTURAL = set('''html head body main header footer section article aside nav div p
    h1 h2 h3 h4 h5 h6 ul ol li dl dt dd blockquote figure figcaption table caption
    colgroup thead tbody tfoot tr th td form fieldset legend details summary title
    meta link script style hr'''.split())
PRESERVE = {'script', 'style', 'pre', 'textarea'}


@dataclass
class Element:
    tag: str
    opening: str
    closing: str = ''
    children: list = field(default_factory=list)
    attrs: dict = field(default_factory=dict)


def raw(node):
    if isinstance(node, str):
        return node
    return node.opening + ''.join(raw(child) for child in node.children) + node.closing


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Element('', '')
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Element(tag, self.get_starttag_text(), attrs=dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Element(tag, self.get_starttag_text(), attrs=dict(attrs)))

    def handle_endtag(self, tag):
        if self.stack[-1].tag != tag:
            raise ValueError(f'Unmatched </{tag}> at {self.getpos()}')
        self.stack.pop().closing = f'</{tag}>'

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def handle_entityref(self, name):
        self.handle_data(f'&{name};')

    def handle_charref(self, name):
        self.handle_data(f'&#{name};')

    def handle_comment(self, data):
        self.handle_data(f'<!--{data}-->')

    def handle_decl(self, decl):
        self.handle_data(f'<!{decl}>')


def render(node, depth=0):
    indent = '  ' * depth
    if isinstance(node, str):
        return indent + node.strip()
    is_field = 'field' in node.attrs.get('class', '').split()
    def structural(child):
        return (isinstance(child, Element) and
                (child.tag in STRUCTURAL or node.tag == 'form' or is_field)) or (
                    isinstance(child, str) and child.lstrip().startswith('<!'))

    # Keep prose and whitespace-sensitive elements intact. Adjacent inline
    # siblings remain one group, so formatting never inserts spaces between them.
    has_text = any(isinstance(c, str) and c.strip() and not c.lstrip().startswith('<!')
                   for c in node.children)
    if node.tag in PRESERVE or has_text or not any(map(structural, node.children)):
        return indent + raw(node)
    child_depth = depth + 1 if node.tag else depth
    lines = []
    inline = []

    def flush_inline():
        content = ''.join(raw(c) for c in inline).strip()
        if content:
            lines.append('  ' * child_depth + content)
        inline.clear()

    for child in node.children:
        if structural(child):
            flush_inline()
            lines.append(render(child, child_depth))
        else:
            inline.append(child)
    flush_inline()
    content = '\n'.join(lines)
    if not node.tag:
        return content
    return f'{indent}{node.opening}\n{content}\n{indent}{node.closing}'


def signature(node):
    """Only structural whitespace may differ after formatting."""
    if isinstance(node, str):
        return node if node.strip() else None
    return (node.opening, node.closing, [signature(c) for c in node.children
                                       if not isinstance(c, str) or c.strip()])


def parse(text):
    parser = Tree()
    parser.feed(text)
    parser.close()
    if len(parser.stack) != 1:
        raise ValueError(f'Unclosed <{parser.stack[-1].tag}>')
    return parser.root


def format_html(text):
    original = parse(text)
    formatted = render(original).rstrip('\r\n') + '\n'
    if signature(original) != signature(parse(formatted)):
        raise ValueError('Formatting would change HTML content')
    return formatted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Report differences without writing files')
    args = parser.parse_args()
    changes = []
    # Validate every page before writing any of them.
    paths = sorted((ROOT / 'dist').rglob('*.html'))
    for path in paths:
        original = path.read_text(encoding='utf-8')
        formatted = format_html(original)
        if original != formatted:
            changes.append((path, formatted))
    for path, formatted in changes:
        if not args.check:
            path.write_text(formatted, encoding='utf-8', newline='\n')
        print(path.relative_to(ROOT).as_posix())
    print(f'{len(paths)} HTML files checked; {len(changes)} formatting changes'
          + (' needed.' if args.check else ' written.'))
    return 1 if args.check and changes else 0


if __name__ == '__main__':
    raise SystemExit(main())
