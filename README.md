# ビズフォーム公式サイト

`bizform.contentsx.jp` 用の静的サイトです。公開成果物は `dist/` に置きます。

## 構成

- 主要8ページ: トップ、サービス、料金、文面サンプル、活用シーン、FAQ、資料、導入相談
- 営業ガイド: 基礎、代行、ツール比較、例文、料金相場、注意点、やり方
- 補助ページ: 送信方針、送信停止窓口、運営会社

## 制作・更新ルール

料金・件数・契約条件、サンプルと実例の区別、共通ヘッダー・追従CTA、スマートフォンの表示・操作、問い合わせフォームの送信と表示、公開前確認事項は [docs/CONTENT-RULES.md](docs/CONTENT-RULES.md) を参照してください。

HTMLの整形は `python scripts/format_html.py`、整形済みかの確認は `python scripts/format_html.py --check` で行います（Python 3.10以上、追加パッケージ不要）。本文やインライン要素間の空白を維持し、ブロック構造をスペース2つで揃えます。

## 外部連携

導入相談フォーム（`/contact/`）の送信処理は `dist/assets/app.js` にある。HubSpot を主、Contents X CRM を従として両方へ送る（BizManga・ContentsX・イチオシ採用と同じ構成）。画面の受付完了・失敗は HubSpot の応答だけで決め、CRM への送信が失敗しても送信者には見せない。表示と文言のルールは [docs/CONTENT-RULES.md](docs/CONTENT-RULES.md) の「問い合わせと停止窓口」を参照。

| 送信先 | 内容 |
|---|---|
| HubSpot | Portal `48367061` / Form `b6da14d0-d60d-4357-89fc-0015ed32b704`（BizManga・ContentsX と同じフォーム）。`pageName` は `ビズフォーム - お問い合わせ`。部署の項目は無いので `busyo` は送らない |
| Contents X CRM | `https://contentsx-crm.vercel.app/api/inbound/web` に `site: 'bizform'` で送る。受信箱 `/inbox` に入り、人が承認するまで顧客データにはならない |

- **CRM のトークン（`CRM_TOKEN`）は5箇所で同じ値にする**: CRM 側の設定／BizManga `contact.html`／ContentsX `js/contact.js`／イチオシ採用 `js/main.js`／ビズフォーム `dist/assets/app.js`。1箇所でもずれるとそのサイトだけ CRM に届かなくなるが、HubSpot は動くので気づきにくい。ビズフォームは ContentX_HP とは別リポジトリのため、ContentX_HP の `crm-token-sync` フックでは検知されない。
  - このトークンはブラウザから見える前提の値で、機密ではない。新しい値を作るのは CRM 側の担当者の判断で、変えるときは5箇所を同時に直す。
- CRM 側でこのサイトからの送信を受け付ける設定が必要（CRM リポジトリで管理）。CRM 側の受付方式が変わると、送信にキーの追加などが要ることがある。CRM に届かなくても HubSpot には届くので、変更時は CRM 側の担当者と受信箱で届いたかを確認する。
- `/stop/`（送信停止窓口）はどちらにもつないでいない。
- 今はどのページにも CSP が無い。CSP を足すときは `connect-src` に `https://api.hsforms.com` と `https://contentsx-crm.vercel.app` を必ず入れる（漏れると送信が失敗表示になる）。
- CRM に独自ドメイン `crm.contentsx.jp` が割り当てられたら、`app.js` の `CRM_ENDPOINT`（と CSP があればその送信先）を差し替える。
- HubSpot のトラッキングコード（Cookie）は読み込んでいない。入れる場合は先にプライバシーポリシーの「10. Cookie・アクセス解析」を改定する。

## 公開

- GitHub Pagesは `.github/workflows/pages.yml` から `dist/` を公開する。
- 公開ブランチは `main` とする。
- 独自ドメインは `bizform.contentsx.jp`。正本は `dist/CNAME` とする。
- `main` への反映前に、内部リンク、画像参照、JavaScript、サイトマップを検証する。
