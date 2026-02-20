# MASTER_INSTRUCTION.md: VRC-LIFE Portal - WORLD Section

## 1. Project Vision
**"Virtual Curated Gallery"**
VRChat等の仮想空間を単なるデータとしてではなく、一つの「作品」として展示するエディトリアル（雑誌風）アーカイブ。情報の機能性よりも、空間の空気感や没入感を予感させる「静寂な美学」を最優先する。

---

## 2. Core Design Principles
- **Minimalism & Elegance**: 装飾を削ぎ落とし、余白（Negative Space）によって情報の格を高める。
- **Typography Contrast**: 伝統的なセリフ体と、モダンなサンセリフ体を対比させ、洗練された印象を作る。
- **Tactile Digital**: デジタル特有の「冷たさ」を排除するため、紙のような質感や、アナログ的なノイズ感を微かに取り入れる。
- **Intentional Friction**: 全てを一度に見せるのではなく、スクロールやホバーを通じて「発見」させる。

---

## 3. Visual Identity (Design Tokens)

### 3.1 Color Palette
- **COLOR_BG**: `#FDFCF5` (メイン背景。古い画用紙のような温かみのある白)
- **COLOR_TEXT_MAIN**: `#2A2A2A` (本文・タイトル。コントラストを抑えた墨色)
- **COLOR_TEXT_MUTE**: `#999999` (補足情報・メタデータ用)
- **COLOR_ACCENT**: `#9D8A61` (控えめなシャンパンゴールド)
- **COLOR_LINE**: `rgba(0,0,0,0.05)` (ヘアライン/極細線)

### 3.2 Typography
- **Primary Serif**: `Playfair Display` (Italic)
    - 用途: メイン見出し、装飾的なキーワード。
- **Standard Sans**: `Zen Kaku Gothic New` / `Noto Sans JP` (Weight: 300, 400)
    - 用途: 本文、ナビゲーション、ボタン。
- **Interface Mono**: `Inter` (Tracking: 0.3em+)
    - 用途: キャプション、タグ、日付等のメタデータ。

---

## 4. Component Specifications

### 4.1 Global Navigation
- **Height**: `80px`
- **Effect**: `backdrop-blur-md` (80% opacity)
- **Border**: `border-b border-black/5`
- **Interaction**: アクティブなメニューには控えめなアンダーライン（1px）。

### 4.2 Hero / Title Section
- **Layout**: セントラル・アライメント。
- **Styling**: `World / Archive` （Worldはセリフ斜体、/は極細サンセリフ、Archiveはサンセリフ）。
- **Spacing**: 上下 `py-20` 以上の十分なマージンを確保。

### 4.3 Filter Navigation
- **Style**: 枠線なし、リンクの羅列形式。
- **Spacing**: 項目間に `gap-8` 以上の余白。
- **Active State**: `Primary Text` カラーに変更 + `30% width` の細いアンダーライン。

### 4.4 Gallery Grid
- **Grid System**: 
    - Desktop: 3 columns (Max-width: 1600px)
    - Tablet: 2 columns
    - Mobile: 1 column
- **Card Design**: 
    - Image Ratio: `16:9` (シネマティックな印象)
    - Hover: `scale(1.05)` ＋ 微細なオーバーレイ（輝度-5%）。
    - Metadata: 画像の下にTitleとTagを配置。文字サイズは極小（10~12px）。

---

## 5. Implementation Guidelines

### 5.1 CSS & Tailwind Strategy
- **Hairlines**: `1px` の境界線は不透明度を `5%` 以下に落とし、主張させすぎない。
- **Tracking**: 英字のサブタイトルやタグには必ず `tracking-[0.3em]` を適用。
- **Anti-aliasing**: `-webkit-font-smoothing: antialiased;` をグローバルに適用。

### 5.2 Animations
- **Page Load**: `opacity` と `translate-y` を組み合わせたスタッガー（順次）表示。
- **Duration**: `400ms` 〜 `1200ms`（ゆっくりとした動き）。
- **Easing**: `cubic-bezier(0.165, 0.84, 0.44, 1)`。

### 5.3 Assets
- **Texture**: 画面最背面に `2%` 程度のグレイン（粒状感）ノイズを重ねる。
- **Images**: ワールド写真は「広角」かつ「無人」のものを推奨し、静寂さを強調。
