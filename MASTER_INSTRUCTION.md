# VRC-LIFE Portal 開発マスター指示書

## 1. サイト概要
VRChatに関連する情報（Unity、ファッション、ワールド等）を集約するポータルサイト。
洗練された、無駄のない黒ベースのミニマル・ラグジュアリーなデザインを維持する。

## 2. 現在の技術スタック
- HTML5 / CSS (Tailwind CSS ユーティリティクラス使用)
- デザイン: ダークモード（背景 #000000 / 文字 #FFFFFF）
- フォント: Inter, Noto Sans JP
- ロゴ処理: `filter: invert(1); mix-blend-mode: screen;` を使用

## 3. 実装ルール（厳守事項）
- **一貫性:** 常に `index.html` のデザイン（5セクションのグリッド）を正解とする。
- **ホバー演出:** 画像のカラー化、拡大、テキスト反転、説明文のフェードイン。
- **ウェルカム画面:** `js/home.js` による全画面ロゴ表示を維持する。

## 4. ページ構成
- KNOWLEDGE: `knowledge/index.html`
- FASHION: `fashion/index.html`
- WORLD: `world/index.html`
- TREND: 未実装
- CONNECTION: 未実装

## 5. AIへの重要指示
指示が曖昧になったり、過去のデザイン案を忘れそうになった場合は、必ずこの `MASTER_INSTRUCTION.md` と `index.html` のソースコードを再読み込みして、現状の仕様に整合させてから提案すること。
