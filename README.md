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
| Contents X CRM | CRM の埋め込みスクリプト `https://contentsx-crm.vercel.app/embed/inbound-v1.js` を `dist/contact/index.html` の `</body>` 直前で読み込み（公開キー `data-source-key`・`data-auto="false"`）、`app.js` が入力チェック後・HubSpot 送信の直前に `BizcarteInbound.sendForm(form)` を呼ぶ。受信箱 `/inbox` の受信元カードに入り、人が承認するまで顧客データにはならない |

- **公開キーは秘密ではない**（ブラウザに出る前提の値）。CRM 側はこのキーに登録したドメイン（`https://bizform.contentsx.jp`）からの送信だけを受け付ける。ドメインが変わる・別ドメインで開かれるようになったら、コードではなく CRM 側の許可ドメインを足してもらう。localhost からの送信は拒否されるのが正常。
- `data-auto="false"` は外さない。外すと入力チェックで止まった送信まで拾う。
- 項目は欄の名前とラベルから自動で判別される（会社名・氏名・メール・相談内容＝件名・詳しい内容＝本文）。判別を指定したい欄だけ `data-crm-field` を付ける。ハニーポット `#bfWebsite`（`name="website"`・`tabindex="-1"`）は自動で認識され、値が入っていれば CRM 側で捨てられる。
- CRM への送信はスクリプトが応答を待たずに行い、失敗しても例外を出さない。CRM に届かなくても HubSpot には届くので、変更時は受信箱で届いたかを確認する。
- `/stop/`（送信停止窓口）はどちらにもつないでいない。
- 今はどのページにも CSP が無い。CSP を足すときは `connect-src` に `https://api.hsforms.com` と `https://contentsx-crm.vercel.app`、`script-src` に `https://contentsx-crm.vercel.app` を必ず入れる（漏れると HubSpot 送信が失敗表示になる、または CRM に届かなくなる）。
- CRM に独自ドメイン `crm.contentsx.jp` が割り当てられたら、`dist/contact/index.html` のスクリプトの読み込み元（と CSP があればその送信先）を差し替える。
- HubSpot のトラッキングコード（Cookie）は読み込んでいない。入れる場合は先にプライバシーポリシーの「10. Cookie・アクセス解析」を改定する。

## 公開

- GitHub Pagesは `.github/workflows/pages.yml` から `dist/` を公開する。
- 公開ブランチは `main` とする。
- 独自ドメインは `bizform.contentsx.jp`。正本は `dist/CNAME` とする。
- `main` への反映前に、内部リンク、画像参照、JavaScript、サイトマップを検証する。
