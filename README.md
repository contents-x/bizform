# ビズアプローチ公式サイト（旧ビズフォーム）

`bizform.contentsx.jp` 用の静的サイトです。公開成果物は `dist/` に置きます。

2026-10-21 にサービス名を「ビズフォーム」から「ビズアプローチ」に変えました。ドメイン・リポジトリ名・資料PDFはまだ旧名のままです（下の「名称変更の残り」）。

## 構成

- 主要8ページ: トップ、サービス、料金、文面サンプル、活用シーン、FAQ、資料、導入相談
- 営業ガイド: 基礎、代行、ツール比較、例文、料金相場、注意点、やり方
- 補助ページ: 送信方針、送信停止窓口、運営会社
- CSS は `dist/assets/css/`（全ページ共通の `site.css` とページ別のファイル）、JavaScript は `dist/assets/js/`（全ページの `site.js` と `analytics.js`、フォームのある2ページの `forms.js`、FAQ の `faq.js`）。詳しくは [docs/CONTENT-RULES.md](docs/CONTENT-RULES.md) の「CSS・JavaScriptの構成」
- `docs/` でリポジトリに入るのは `CONTENT-RULES.md` と `HISTORY.md` だけ。ほかの調査・作業メモは `.gitignore` で手元に留める

## 制作・更新ルール

料金・件数・契約条件、サンプルと実例の区別、共通ヘッダー・追従CTA、スマートフォンの表示・操作、問い合わせフォームの送信と表示、公開前確認事項は [docs/CONTENT-RULES.md](docs/CONTENT-RULES.md) を参照してください。ルールが生まれた経緯は [docs/HISTORY.md](docs/HISTORY.md) にあります。

スクリプトは Python 3.10 以上で動き、`layout_check.py` のほかは追加パッケージ不要です。`check_site.py` の JavaScript の構文の確認には Node.js を使います（無い環境ではその確認だけを飛ばして NOTE を出し、GitHub Actions では必ず確認します）。HTMLの整形は、本文やインライン要素間の空白を維持し、ブロック構造をスペース2つで揃えます。

| スクリプト | 使うとき |
|---|---|
| `python scripts/format_html.py` | HTMLを変えたあと。整形する（`--check` で整形済みかだけを確認） |
| `python scripts/stamp_assets.py` | `dist/assets/css`・`dist/assets/js` を変えたあと。HTMLの `?v=` を内容のハッシュに更新する |
| `python scripts/check_site.py` | push の前。リンク・画像・サイトマップ・料金・色トークン・`?v=`・整形などを確認する（GitHub Actions でも公開前に実行し、失敗したら公開しない） |
| `python scripts/layout_check.py` | 見た目を変えたあと。全ページを多数の画面幅・文字サイズ・機種で表示し、はみ出しや折り返しを確認する（Playwright が必要） |

手元で表示するには `python -m http.server 8000 --bind 127.0.0.1 --directory dist` を実行し、`http://127.0.0.1:8000/` を開きます（ルートからのパスで書いているため、HTMLファイルを直接開くと画像やCSSが読み込まれません）。手元で開いたページからフォームを送信すると、共用の HubSpot フォームに実際に届きます（CRM は手元からの送信を受け付けません）。動作確認では送信しないでください。

## 外部連携

導入相談フォーム（`/contact/`）と資料ダウンロードのフォーム（`/resources/#download`）の送信処理は `dist/assets/js/forms.js` にある。

- **導入相談**: HubSpot を主、Contents X CRM を従として両方へ送る（BizManga・ContentsX・イチオシ採用と同じ構成）。画面の受付完了・失敗は HubSpot の応答だけで決め、CRM への送信が失敗しても送信者には見せない。
- **資料ダウンロード**: HubSpot と CRM（受信箱の「資料DL」の箱）へ写しを送り、どの応答も待たずにPDFのダウンロードを始める。CRM 側の設定＞プラグイン＞ホームページ連携で「資料ダウンロード」がオンになっていないと、CRM は受け付けない（ダウンロード自体は動く）。

表示と文言のルールは [docs/CONTENT-RULES.md](docs/CONTENT-RULES.md) の「問い合わせと停止窓口」「資料ダウンロード」を参照。

| 送信先 | 内容 |
|---|---|
| HubSpot | Portal `48367061` / Form `b6da14d0-d60d-4357-89fc-0015ed32b704`（BizManga・ContentsX と同じフォーム。送信先は `forms.js` 冒頭の `HUBSPOT_ENDPOINT`）。`pageName` は `ビズアプローチ - お問い合わせ` / `ビズアプローチ - 資料ダウンロード`（2026-10-21 の改名までは `ビズフォーム - …`。本文末尾の `[ビズフォーム経由の…]` も同じ）。⚠️ **HubSpot 側で部署 `busyo` が必須**（空欄も拒否＝`REQUIRED_FIELD`。2026-09-29 に確認）。両フォームとも部署は任意なので、空なら `未入力` を送る（`forms.js` の `hubspotDepartment`）。資料ダウンロードは電話番号と資料名を `message` に入れる |
| Contents X CRM | CRM の埋め込みスクリプト `https://contentsx-crm.vercel.app/embed/inbound-v1.js` を、フォームのある `dist/contact/index.html` と `dist/resources/index.html` の `</body>` 直前で1回ずつ読み込み（公開キー `data-source-key`・`data-auto="false"`）、`forms.js` が入力チェック後に `BizcarteInbound.sendForm(form)` を呼ぶ。資料ダウンロードのフォームには `data-crm-form="download"` と `data-crm-document`（資料名）を付けてある。受信箱 `/inbox` に入り、人が承認するまで顧客データにはならない |

- **公開キーは秘密ではない**（ブラウザに出る前提の値）。CRM 側はこのキーに登録したドメイン（`https://bizform.contentsx.jp`）からの送信だけを受け付ける。ドメインが変わる・別ドメインで開かれるようになったら、コードではなく CRM 側の許可ドメインを足してもらう。localhost からの送信は拒否されるのが正常。
- `data-auto="false"` は外さない。外すと入力チェックで止まった送信まで拾う。同じページにスクリプトを2行入れない（二重に届く）。
- 項目は欄の名前とラベルから自動で判別される（会社名・氏名・メール・相談内容＝件名・詳しい内容＝本文）。判別を指定したい欄だけ `data-crm-field` を付ける。ハニーポット `#website`（`name="website"`・`tabindex="-1"`）は自動で認識され、値が入っていれば CRM 側で捨てられる。
- CRM への送信はスクリプトが応答を待たずに行う。`forms.js` は呼び出しを `try`／`catch` で囲み、HubSpot への送信（資料ダウンロードではダウンロード）を始めてから呼ぶので、スクリプトが例外を出しても送信とダウンロードは止まらない。CRM に届かなくても HubSpot には届くので、変更時は受信箱で届いたかを確認する。
- `/stop/`（送信停止窓口）はどちらにもつないでいない。
- 今はどのページにも CSP が無い。CSP を足すときは `connect-src` に `https://api.hsforms.com` と `https://contentsx-crm.vercel.app`、`script-src` に `https://contentsx-crm.vercel.app` を必ず入れる（漏れると HubSpot 送信が失敗表示になる、または CRM に届かなくなる）。Google アナリティクスのため、`script-src` に `https://*.googletagmanager.com`、`connect-src` に `https://*.google-analytics.com`・`https://*.analytics.google.com`・`https://*.googletagmanager.com`、`img-src` に `https://*.google-analytics.com`・`https://*.googletagmanager.com` も入れる（漏れると計測が止まる）。
- CRM に独自ドメイン `crm.contentsx.jp` が割り当てられたら、`dist/contact/index.html` と `dist/resources/index.html` のスクリプトの読み込み元（と CSP があればその送信先）、`scripts/check_site.py` の `CRM_EMBED`、`scripts/layout_check.py` の名前解決させないホストを差し替える（`forms.js` はパス `/embed/inbound-v1.js` でスクリプトを探すので、パスが変わらなければそのまま）。
- HubSpot のトラッキングコード（Cookie）は読み込んでいない。入れる場合は先にプライバシーポリシーの「10. Cookie・アクセス解析」を改定する。

## Search Console

- URLプレフィックスのプロパティは `https://bizform.contentsx.jp/`（2026-10-08 に所有権確認済み）。
- 仕事用アカウント `s.yamaguchi@contentsx.jp` でも所有権確認済み。所有権確認には `dist/index.html` の2つの `google-site-verification` メタタグを使う。確認状態を維持するため削除しない。
- サイトマップは `https://bizform.contentsx.jp/sitemap.xml`。Search Consoleへ送信済み。`dist/robots.txt` にも同じURLを記載している。
- 2026-10-08 22:35の公開URLテストではサイトマップの取得成功・クロール許可を確認。一覧は「取得できませんでした」の表示が残っており、再送信済み。サイトマップ処理の成功は未確認。

## Google アナリティクス

- 会社用アカウント `391407567` のGA4プロパティ「ビズフォーム」`558125303`。ウェブストリームは `16068302797`、測定IDは `G-1CXY4Z85C6`（2026-10-08 作成）。
- 全ページのheadでGoogleタグと `dist/assets/js/analytics.js` を読み込む（公開前チェックが、全ページにあることと測定IDが `analytics.js` と同じことを確かめる）。公開ホスト `bizform.contentsx.jp` だけで計測し、ローカルプレビューは計測しない。
- Google シグナル・広告パーソナライズはコードで無効化。拡張計測のフォーム操作・サイト内検索も無効。フォームの入力内容をGA4へ送らない。
- Cookieのドメインを `bizform.contentsx.jp` に限定。プライバシーポリシーの「10. Cookie・アクセス解析」に利用目的・送信情報・停止方法を記載。
- GA4側のインストールテストで公開サイトのGoogleタグ検出を確認。Search Consoleの同サイトのプロパティともリンク済み。

## 名称変更の残り（ビズフォーム → ビズアプローチ）

サイトの文言・ロゴ・`pageName` は 2026-10-21 に変えた。次はコードの外の作業か、素材や判断を待っているもの。

- **資料PDF**: `dist/assets/docs/bizform-service-guide-202609.pdf` はスライドの画像にもタイトル情報にも旧名が入っている。改訂した営業資料から作り直し（[docs/CONTENT-RULES.md](docs/CONTENT-RULES.md) の「資料ダウンロード」）、フォームの `data-download-url` と `data-crm-document`（今は中身に合わせて旧名の資料名）を変える。旧PDFは1回の公開のあいだ残す。
- **ロゴ**: `asset_logo.webp` は旧ロゴのマークと Noto Sans JP で作った仮のもの。正式なロゴを受け取ったら差し替える。
- **HubSpot**: `pageName` と本文末尾の「[… 経由の…]」が新しい名前になる。旧名で絞り込むワークフロー・リスト・レポートがあれば、公開前に新旧どちらも拾うよう直す。
- **Contents X CRM**: 受信元の名前「ビズフォーム」を CRM の設定で変える（通知メールの件名【ビズフォーム】に出る）。CRM リポジトリの `.agents/skills/jou-crm-contact-web/SKILL.md` と `docs/planning/INBOUND-FORMS-PLAN.md` のサイト一覧も直す。
- **GA4**: プロパティ名「ビズフォーム」を変える（表示名だけ。計測には影響しない）。
- **送信停止のメール**: 件名を「ビズアプローチ送信停止」にした。旧件名「ビズフォーム送信停止」のメールも同じ扱いで受け付ける。
- **旧画像**: `asset_logo_bizform.webp`・`asset_role_bizform.webp` はキャッシュに残った古いページのために置いてある。次の公開で削除する。
- **ドメイン・リポジトリ名を変える場合**: コードは `dist/CNAME`、`dist/sitemap.xml`、`dist/robots.txt`、全ページの `canonical` と `og:url`、TOP の構造化データ、`dist/assets/js/analytics.js` の公開ホストと Cookie のドメイン、`scripts/check_site.py` の `SITE`、この README。外は DNS、GitHub Pages の独自ドメインと HTTPS、旧ドメインの転送（GitHub Pages は 301 を返せないので、リクルートX → イチ推し採用の `recruitx-redirect` と同じ meta refresh の転送用リポジトリ）、Search Console の新プロパティとサイトマップ、GA4 のウェブストリームの URL、**CRM の許可ドメイン**（足さないと CRM に届かなくなる。HubSpot には届くので気づきにくい）。

## 公開

- GitHub Pagesは `.github/workflows/pages.yml` から `dist/` を公開する。
- 公開ブランチは `main` とする。
- 独自ドメインは `bizform.contentsx.jp`。正本は `dist/CNAME` とする。
- 公開の前に `scripts/check_site.py` が走り、失敗すると公開されない。`layout-check.yml` は表示崩れの確認を参考として実行する（公開は止めない）。
