# MASTER_INSTRUCTION.md: VRC-LIFE Portal (Integrated Design & System)

## 1. Project Concept
**"Digital Archive for Virtual Lifestyle"**
VRChat等の仮想空間における生活、ファッション、知識を、洗練された「ライフスタイル誌」のようなトーンでアーカイブするポータルサイト。デジタルな題材を、アナログで上質な紙媒体の美学（エディトリアルデザイン）で表現する。

---

## 2. System Architecture (Data Pipeline)

### 2.1 Data Source & Management
- **CMS**: Google Spreadsheets (GSS)
- **Data Flow**: 
    1. 管理者がスプレッドシートに情報を入力。
    2. GAS (Google Apps Script) または Sheets API を介して JSON 形式でデータを取得。
    3. `js/world.js` や `js/fashion.js` が非同期通信 (`fetch`) を行い、データを取得・解析。
    4. ページ内の特定のコンテナ (`#worlds-grid` 等) に HTML を動的にインジェクション。

### 2.2 Data Schema (Sheet Structure)
各シートは以下のカラム構造を維持すること。

| Section | Mandatory Columns | Note |
| :--- | :--- | :--- |
| **WORLD** | `id`, `date`, `title`, `author`, `tags`, `imageUrl`, `vrcUrl` | 空間の空気感を伝える横長画像。 |
| **FASHION** | `id`, `date`, `brand`, `itemName`, `tags`, `imageUrl`, `storeUrl` | 質感や詳細がわかる縦長画像。 |

---

## 3. Visual Identity (Design Tokens)

### 3.1 Color Palette
- **BASE_BG**: `#FDFCF5` (画用紙のような温かみのある白)
- **TEXT_MAIN**: `#2A2A2A` (コントラストを抑えた墨色)
- **TEXT_MUTE**: `#999999` (メタデータ、注釈用)
- **ACCENT**: `#9D8A61` (シャンパンゴールド。ボタン等に微量使用)
- **DIVIDER**: `rgba(0,0,0,0.05)` (極薄の境界線)

### 3.2 Typography System
- **Heading (Serif)**: `Playfair Display` (Italic 300)
    - ページタイトル、メインキャッチに使用。
- **Body (JP)**: `Zen Kaku Gothic New` (Light 300)
    - 本文、説明文に使用。
- **Meta/Nav (Sans)**: `Inter` (Tracking: 0.3em)
    - 英語ナビ、タグ、日付に使用。大文字＋広字間を基本とする。

---

## 4. UI Component Specifications

### 4.1 Global Navigation
- **Height**: 80px / ガラス質感 (`backdrop-blur-md`) / 下部に極細線。
- **Links**: 小文字英語、10px、字間 0.3em。アクティブ時に繊細なアンダーライン。

### 4.2 Dynamic Gallery Grid
- **WORLD Grid**: 16:9比率 / 最大3〜4列。
- **FASHION Grid**: 3:4比率 / 縦長レイアウトで詳細を強調。
- **Loading State**: データ取得中は "COLLECTING FRAGMENTS..." 等の洗練されたプレースホルダーを表示。

---

## 5. Interaction & Motion

- **Easing**: `cubic-bezier(0.165, 0.84, 0.44, 1)` (滑らかな減速)
- **Entrance**: ページ読み込み時、要素を時間差（Stagger）で下から上にフェードイン。
- **Image Hover**: 1.2秒かけて `scale(1.05)`。急激な変化は避け、静的な美しさを維持。

---

## 6. Maintenance & Performance
- **Image Optimization**: `imageUrl` に指定する画像は、事前に圧縮（WebP推奨）されたものを使用。
- **Filtering Logic**: スプシから取得した `tags` 文字列をパースし、フロントエンド側で動的にフィルタリングを実施。
- **Anti-aliasing**: `-webkit-font-smoothing: antialiased;` を全要素に適用。
