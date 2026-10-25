# AGENTS.md — bizform

> AIエージェント（Codex・Claude Code など）共通の入口。Claude Code は `CLAUDE.md`（`@AGENTS.md` だけ）経由で読む。
> BizForm 公式サイト（bizform.contentsx.jp）。このリポジトリの内容と作業方法は [README.md](README.md) を正本とする（固有の規約はまだ無い）。

## 全社タスク管理（GitHub Issue）

- **タスク（GitHub Issue）を登録・着手・更新・完了する前に**、全社タスク管理の正本 [Project #1 の README](https://github.com/orgs/contents-x/projects/1) を `gh project view 1 --owner contents-x --format json --jq .readme` で読む。タスクにする Issue にだけラベル `task:track` を付ける（メモ・調査の Issue には付けない・Issue を作り直さない）。README を読めない・Project を確認できないときは、登録・更新できたと報告しない
