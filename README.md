# ビズフォーム公式サイト

`bizform.contentsx.jp` 用の静的サイトです。公開成果物は `dist/` に置きます。

## 構成

- 主要8ページ: トップ、サービス、料金、文面サンプル、活用シーン、FAQ、資料、導入相談
- 営業ガイド: 基礎、代行、ツール比較、例文、料金相場、注意点、やり方
- 補助ページ: 送信方針、送信停止窓口、運営会社

## 制作・更新ルール

料金・件数・契約条件、サンプルと実例の区別、共通ヘッダー・追従CTA、スマートフォンの表示・操作、公開前確認事項は [docs/CONTENT-RULES.md](docs/CONTENT-RULES.md) を参照してください。

ページごとの狙うキーワード、記事を書くときの禁止事項、canonical・構造化データの方針、記事をWordPressで管理しない理由は [docs/SEO-STRATEGY.md](docs/SEO-STRATEGY.md) を参照してください。**新しいページを追加する前に、主キーワードが既存ページと重複しないかをこの表で確認してください。**

`/guide/` の記事は他サービスと違い共用WordPress（cms.contentsx.jp）に載せず、このリポジトリで直接管理します。判断の経緯と再検討の条件は上記mdに記載しています。

## 公開

- GitHub Pagesは `.github/workflows/pages.yml` から `dist/` を公開する。
- 公開ブランチは `main` とする。
- 独自ドメインは `bizform.contentsx.jp`。正本は `dist/CNAME` とする。
- `main` への反映前に、内部リンク、画像参照、JavaScript、サイトマップを検証する。
