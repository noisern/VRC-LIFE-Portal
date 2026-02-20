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
    - 本文
