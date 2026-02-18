"""
BOOTH スクレイピングエンジン
VRChat関連アイテムをBOOTHから収集する。

BOOTHの2026年1月27日改定ガイドラインに準拠:
- User-Agent明記
- リクエスト間3秒以上待機
- 1日1回のみ実行
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# === マナー設定 ===
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REQUEST_DELAY = 3  # seconds between requests
MAX_PAGES = 5

# BOOTH search URLs for VRChat items
SEARCH_URLS = [
    "https://booth.pm/ja/search/VRChat?sort=popular&page={}",
    "https://booth.pm/ja/browse/3D%E8%A1%A3%E8%A3%85?q=VRChat&sort=popular&page={}",
    "https://booth.pm/ja/browse/3D%E3%82%AD%E3%83%A3%E3%83%A9%E3%82%AF%E3%82%BF%E3%83%BC?q=VRChat&sort=popular&page={}",
    # 3Dアクセサリー (URL修正)
    "https://booth.pm/ja/browse/3D%E5%B0%8F%E7%89%A9?q=VRChat&sort=popular&page={}",
]

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
}


def fetch_page(url: str, session: requests.Session) -> Optional[BeautifulSoup]:
    """1ページ取得。マナー設定に従い待機時間を挿入。"""
    try:
        logger.info(f"Fetching: {url}")
        response = session.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        time.sleep(REQUEST_DELAY)
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def parse_item(item_element) -> Optional[dict]:
    """商品要素から情報を抽出する。"""
    try:
        # 商品リンク
        link_el = item_element.select_one("a[href*='/items/']")
        if not link_el:
            return None
        booth_url = link_el.get("href", "")
        if not booth_url.startswith("http"):
            booth_url = "https://booth.pm" + booth_url

        # 商品ID
        item_id = ""
        if "/items/" in booth_url:
            item_id = "booth-" + booth_url.split("/items/")[-1].split("?")[0].split("/")[0]

        # 商品名
        name_el = item_element.select_one("[class*='item-card__title'], .shop-item-card__item-name, h2, h3")
        name = name_el.get_text(strip=True) if name_el else ""

        # 価格
        price_el = item_element.select_one("[class*='price'], .shop-item-card__price")
        price_text = price_el.get_text(strip=True) if price_el else "0"
        price = int("".join(c for c in price_text if c.isdigit()) or "0")

        # サムネイル
        img_el = item_element.select_one("img")
        thumbnail_url = ""
        if img_el:
            original_url = img_el.get("data-src") or img_el.get("src") or ""
            if original_url:
                # wsrv.nl経由で取得（Referer回避＆WebP変換）
                thumbnail_url = f"https://wsrv.nl/?url={original_url}&output=webp"

        # ショップ名
        shop_el = item_element.select_one("[class*='shop-name'], .shop-item-card__shop-name")
        shop_name = shop_el.get_text(strip=True) if shop_el else ""

        # いいね数
        likes_el = item_element.select_one("[class*='wish-list-counter'], [class*='like'], .js-like-count")
        likes_text = likes_el.get_text(strip=True) if likes_el else "0"
        likes = int("".join(c for c in likes_text if c.isdigit()) or "0")

        # R18チェック
        is_r18 = False
        r18_el = item_element.select_one("[class*='adult'], [class*='r18'], .badge-adult")
        if r18_el:
            is_r18 = True
        # テキストにR-18やR18が含まれているか
        full_text = item_element.get_text()
        if "R-18" in full_text or "R18" in full_text or "成人向け" in full_text:
            is_r18 = True

        if not name or not item_id:
            return None

        return {
            "id": item_id,
            "name": name,
            "price": price,
            "shopName": shop_name,
            "boothUrl": booth_url,
            "thumbnailUrl": thumbnail_url,
            "likes": likes,
            "isR18": is_r18,
            "description": "",  # 詳細ページから取得する場合に使用
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.warning(f"Failed to parse item: {e}")
        return None


def fetch_item_detail(booth_url: str, session: requests.Session) -> dict:
    """商品詳細ページから追加情報（説明文）を取得する。"""
    soup = fetch_page(booth_url, session)
    if not soup:
        return {}

    detail = {}

    # 説明文
    desc_el = soup.select_one("[class*='description'], .js-market-item-detail-description")
    if desc_el:
        detail["description"] = desc_el.get_text(strip=True)[:500]  # 500文字まで

    # いいね数（詳細ページからの方が正確）
    likes_el = soup.select_one("[class*='wish-list-counter'], .js-like-count")
    if likes_el:
        likes_text = likes_el.get_text(strip=True)
        likes = int("".join(c for c in likes_text if c.isdigit()) or "0")
        detail["likes"] = likes

    return detail


def scrape_booth(fetch_details: bool = False, dry_run: bool = False) -> list[dict]:
    """
    BOOTHからVRChat関連アイテムを収集する。

    Args:
        fetch_details: 商品詳細ページも取得するか（負荷注意）
        dry_run: True の場合、HTTPリクエストを行わずサンプルデータを返す

    Returns:
        収集されたアイテムのリスト
    """
    if dry_run:
        logger.info("=== DRY RUN MODE ===")
        return _get_sample_data()

    session = requests.Session()
    all_items = []
    seen_ids = set()

    for i, search_url_base in enumerate(SEARCH_URLS):
        category_label = [
            "VRChat全般",
            "3D衣装",
            "3Dキャラクター",
            "3D小物"
        ][i]
        
        logger.info(f"\n--- カテゴリ: {category_label} ---")

        for page in range(1, MAX_PAGES + 1):
            page_url = search_url_base.format(page)

            soup = fetch_page(page_url, session)
            if not soup:
                break

            # アイテムカードを検索
            item_elements = soup.select(
                "[class*='item-card'], .shop-item-card, [data-tracking-name='items']"
            )

            if not item_elements:
                logger.warning(f"  ページ {page}: アイテムなし")
                if soup.title:
                    logger.info(f"  Page Title: {soup.title.string.strip()}")
                logger.info(f"  Page Preview: {soup.prettify()[:500]}")
                break

            logger.info(f"  ページ {page}: {len(item_elements)} アイテム検出")

            for el in item_elements:
                item = parse_item(el)
                if item and item["id"] not in seen_ids:
                    seen_ids.add(item["id"])

                    # 詳細ページからの追加情報
                    if fetch_details and item["boothUrl"]:
                        detail = fetch_item_detail(item["boothUrl"], session)
                        item.update(detail)

                    all_items.append(item)

    logger.info(f"\n=== 合計 {len(all_items)} アイテム収集完了 ===")
    return all_items


def _get_sample_data() -> list[dict]:
    """ドライラン用サンプルデータ。"""
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "id": "booth-1234567",
            "name": "【VRChat向け】サイバーパンクジャケット",
            "price": 2500,
            "shopName": "CyberWear Studio",
            "boothUrl": "https://booth.pm/ja/items/1234567",
            "thumbnailUrl": "https://wsrv.nl/?url=https://booth.pximg.net/sample1.jpg&output=webp",
            "likes": 350,
            "isR18": False,
            "description": "VRChat対応のサイバーパンク風ジャケット。対応アバター：舞夜、桔梗、セレスティア。",
            "fetchedAt": now,
        },
        {
            "id": "booth-2345678",
            "name": "和風モダンドレス for 舞夜",
            "price": 3000,
            "shopName": "WaStyle",
            "boothUrl": "https://booth.pm/ja/items/2345678",
            "thumbnailUrl": "https://booth.pximg.net/sample2.jpg",
            "likes": 200,
            "isR18": False,
            "description": "舞夜対応の和風モダンドレスです。改変歓迎。",
            "fetchedAt": now,
        },
        {
            "id": "booth-3456789",
            "name": "ストリートスニーカー VRChat",
            "price": 1500,
            "shopName": "VR Kicks",
            "boothUrl": "https://booth.pm/ja/items/3456789",
            "thumbnailUrl": "https://booth.pximg.net/sample3.jpg",
            "likes": 150,
            "isR18": False,
            "description": "ストリート系スニーカー。ボーン対応済み。",
            "fetchedAt": now,
        },
        {
            "id": "booth-4567890",
            "name": "量産型リボンヘッドドレス",
            "price": 800,
            "shopName": "RyouSan Lab",
            "boothUrl": "https://booth.pm/ja/items/4567890",
            "thumbnailUrl": "https://booth.pximg.net/sample4.jpg",
            "likes": 500,
            "isR18": False,
            "description": "量産型コーデにぴったりのリボンヘッドドレス。対応アバター多数。",
            "fetchedAt": now,
        },
        {
            "id": "booth-5678901",
            "name": "地雷系チョーカーセット",
            "price": 600,
            "shopName": "JiraiAccessory",
            "boothUrl": "https://booth.pm/ja/items/5678901",
            "thumbnailUrl": "https://booth.pximg.net/sample5.jpg",
            "likes": 180,
            "isR18": False,
            "description": "地雷系コーデに合うチョーカー5種セット。",
            "fetchedAt": now,
        },
        {
            "id": "booth-6789012",
            "name": "ファンタジー騎士アーマー【男女兼用】",
            "price": 4000,
            "shopName": "Fantasy Forge",
            "boothUrl": "https://booth.pm/ja/items/6789012",
            "thumbnailUrl": "https://booth.pximg.net/sample6.jpg",
            "likes": 420,
            "isR18": False,
            "description": "ファンタジー風騎士の鎧。PBR対応、Quest対応済み。",
            "fetchedAt": now,
        },
        {
            "id": "booth-7890123",
            "name": "キッズサイズ ふわもこパジャマ",
            "price": 1200,
            "shopName": "Small World",
            "boothUrl": "https://booth.pm/ja/items/7890123",
            "thumbnailUrl": "https://booth.pximg.net/sample7.jpg",
            "likes": 130,
            "isR18": False,
            "description": "スモールアバター向けふわもこパジャマ。マヌカ、ルシナ対応。",
            "fetchedAt": now,
        },
        {
            "id": "booth-8901234",
            "name": "R-18 セクシーランジェリー",
            "price": 1000,
            "shopName": "AdultVRC",
            "boothUrl": "https://booth.pm/ja/items/8901234",
            "thumbnailUrl": "https://booth.pximg.net/sample8.jpg",
            "likes": 300,
            "isR18": True,
            "description": "成人向けランジェリーセット。",
            "fetchedAt": now,
        },
        {
            "id": "booth-9012345",
            "name": "ゴシックロリータドレス",
            "price": 3500,
            "shopName": "GothicVRC",
            "boothUrl": "https://booth.pm/ja/items/9012345",
            "thumbnailUrl": "https://booth.pximg.net/sample9.jpg",
            "likes": 280,
            "isR18": False,
            "description": "ゴシックロリータ風ドレス。桔梗・セレスティア対応。",
            "fetchedAt": now,
        },
        {
            "id": "booth-0123456",
            "name": "VRChatアバターテクスチャ改変素材集",
            "price": 500,
            "shopName": "TexMaster",
            "boothUrl": "https://booth.pm/ja/items/0123456",
            "thumbnailUrl": "https://booth.pximg.net/sample10.jpg",
            "likes": 90,
            "isR18": False,
            "description": "テクスチャ改変用素材集。肌・服・目のテクスチャが入っています。",
            "fetchedAt": now,
        },
        {
            "id": "booth-1111111",
            "name": "ネオン系グローアクセサリーパック",
            "price": 1800,
            "shopName": "NeonVRC",
            "boothUrl": "https://booth.pm/ja/items/1111111",
            "thumbnailUrl": "https://booth.pximg.net/sample11.jpg",
            "likes": 220,
            "isR18": False,
            "description": "光るネオン系アクセサリー詰め合わせ。サイバーパンクコーデに。",
            "fetchedAt": now,
        },
        {
            "id": "booth-2222222",
            "name": "カジュアルパーカー＆デニムセット",
            "price": 2000,
            "shopName": "CasualVRC",
            "boothUrl": "https://booth.pm/ja/items/2222222",
            "thumbnailUrl": "https://booth.pximg.net/sample12.jpg",
            "likes": 310,
            "isR18": False,
            "description": "カジュアルなパーカーとデニムパンツのセット。男性アバター対応。",
            "fetchedAt": now,
        },
    ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    items = scrape_booth(dry_run=True)
    print(json.dumps(items, ensure_ascii=False, indent=2))
