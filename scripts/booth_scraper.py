"""
BOOTH スクレイピングエンジン
VRChat関連アイテムをBOOTHから収集する。

BOOTHの2026年1月27日改定ガイドラインに準拠:
- User-Agent明記
- リクエスト間3秒以上待機
- 1日1回のみ実行
"""

import requests
from bs4 import BeautifulSoup, Tag
import json
import re
import time
import random
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# === マナー設定 ===
USER_AGENT = "VRC-LIFE Portal Bot"
# REQUEST_DELAY will be randomized

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
        
        # Random sleep 1-3 seconds
        time.sleep(1 + 2 * __import__("random").random())
        
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def parse_item(item_element: Tag) -> Optional[dict]:
    """
    HTML要素からアイテム情報を抽出する。
    User Request V2: Use specific data attributes and robust regex.
    """
    try:
        # 1. Get Basic Info from Attributes (Reliable)
        # item_element is likely 'li.item-card'
        name = item_element.get("data-product-name")
        price_str = item_element.get("data-product-price")
        item_id = item_element.get("data-product-id")
        shop_name = item_element.get("data-product-brand")
        
        # Fallback if attributes missing (e.g. structure changed, but attributes are requested primary)
        if not name:
             title_el = item_element.select_one(".item-card__title, .js-mount-point-shop-item-card-title")
             if title_el: name = title_el.get_text(strip=True)
        
        if not item_id:
             # Try ID from URL
             link = item_element.select_one("a[href*='/items/']")
             if link:
                 href = link.get("href")
                 match = re.search(r'/items/(\d+)', href)
                 if match: item_id = match.group(1)

        # Price parsing
        price = 0
        if price_str:
            try:
                price = int(float(price_str))
            except:
                pass
        else:
             price_el = item_element.select_one(".price, .item-card__price")
             if price_el:
                 p_text = price_el.get_text(strip=True).replace(",", "").replace("¥", "")
                 match = re.search(r'\d+', p_text)
                 if match: price = int(match.group(0))

        # URL & Thumbnail
        booth_url = ""
        thumbnail_url = ""
        
        link_el = item_element.select_one("a[data-original-url]")
        if link_el:
             booth_url = link_el.get("href") # usually relative or absolute? check
             if booth_url and not booth_url.startswith("http"):
                 booth_url = f"https://booth.pm{booth_url}"
        else:
             # Standard link check
             link_el = item_element.select_one("a[href*='/items/']")
             if link_el:
                 booth_url = link_el.get("href")
                 if not booth_url.startswith("http"):
                     booth_url = f"https://booth.pm{booth_url}"

        thumb_el = item_element.select_one("img[src*='user_assets'], img.item-card__thumbnail-image")
        if thumb_el:
            thumbnail_url = thumb_el.get("data-original") or thumb_el.get("src") or ""

        # 2. Get Likes (Priority Targets)
        likes = 0
        
        # Method A: .count-number text
        count_el = item_element.select_one(".count-number")
        if count_el:
            text = count_el.get_text(strip=True)
            # Regex: matches "1,234" etc.
            match = re.search(r'(\d+[\d,.]*)', text)
            if match:
                num_str = match.group(1).replace(",", "")
                likes = int(float(num_str))

        # Method B: aria-label (fallback or primary if A fails)
        if likes == 0:
            # Find button/span with aria-label containing keywords
            candidates = item_element.select("button[aria-label], span[aria-label], a[aria-label]")
            for el in candidates:
                label = el.get("aria-label", "")
                if any(k in label for k in ["スキ", "Loves", "Like"]):
                    # Extract number: "スキ！ 1,234" -> 1234
                    match = re.search(r'(\d+[\d,.]*)', label)
                    if match:
                         num_str = match.group(1).replace(",", "")
                         likes = int(float(num_str))
                         break
        
        # 3. Debug Parsing
        if likes == 0:
            # Log first 3 buttons' aria-labels
            buttons = item_element.select("button, .js-like-btn")[:3]
            debug_labels = []
            for btn in buttons:
                l = btn.get("aria-label")
                if l: debug_labels.append(l)
            
            if debug_labels:
                logger.warning(f"  [DEBUG] Likes=0 for {item_id or 'unknown'}. Found buttons: {debug_labels}")
            else:
                 logger.warning(f"  [DEBUG] Likes=0 for {item_id or 'unknown'}. No buttons with aria-label found.")

        # R18チェック
        is_r18 = False
        r18_el = item_element.select_one(".badge-adult, .is-adult, .r18-badge")
        if r18_el: is_r18 = True
        
        if not is_r18:
            full_text = item_element.get_text()
            if "R-18" in full_text or "成人向け" in full_text:
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
            "description": "",
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.warning(f"Failed to parse item: {e}")
        return None


# Deleted fetch_item_detail as we are reverting to search page scraping 


def scrape_booth(min_likes: int = 0, fetch_details: bool = False, dry_run: bool = False) -> list[dict]:
    """
    BOOTHからVRChat関連アイテムを収集する（全ページ走査）。
    min_likes > 0 の場合、検索結果から取得したスキ数でフィルタリングを行う。
    """
    if dry_run:
        logger.info("=== DRY RUN MODE ===")
        return _get_sample_data()

    session = requests.Session()
    all_items = []
    seen_ids = set()

    # BOOTH search URLs for VRChat items - Forced to 'popular' sort
    SEARCH_URLS = [
        {"url": "https://booth.pm/ja/search/VRChat?sort=popular", "label": "VRChat全般"},
        # Limit categories for debug speed if needed, but keeping full list for now
        {"url": "https://booth.pm/ja/search/3D%E8%A1%A3%E8%A3%85?sort=popular", "label": "3D衣装"},
        {"url": "https://booth.pm/ja/search/3D%E3%82%AD%E3%83%A3%E3%83%A9%E3%82%AF%E3%82%BF%E3%83%BC?sort=popular", "label": "3Dキャラクター"},
        {"url": "https://booth.pm/ja/search/3D%E5%B0%8F%E7%89%A9?sort=popular", "label": "3D小物"},
    ]

    for category in SEARCH_URLS:
        logger.info(f"\n--- カテゴリ: {category['label']} ---")
        page = 1
        
        while True:
            page_url = f"{category['url']}&page={page}"
            soup = fetch_page(page_url, session)
            
            if not soup:
                break

            # アイテムカードを検索
            item_elements = soup.select(
                "li.item-card, .shop-item-card, [data-tracking-name='items']"
            )

            if not item_elements:
                logger.info(f"  ページ {page}: アイテムなし (終了)")
                break

            processed_count_in_page = 0
            
            for el in item_elements:
                item = parse_item(el)
                
                if not item:
                    continue

                # --- 厳格なフィルタリング ---
                # 1. R18除外
                if item["isR18"]:
                    # logger.info(f"Skipping R18: {item['name']}")
                    continue
                
                # 重複チェック
                if item["id"] not in seen_ids:
                    
                    # 2. いいね数フィルタ (検索結果ページの値を使用)
                    current_likes = item.get("likes", 0)
                    if min_likes > 0 and current_likes < min_likes:
                         # Log why it was skipped to help debugging (sample first few failures)
                         # logger.info(f"Skipping low likes ({current_likes}): {item['name']}")
                         continue

                    # 採用
                    seen_ids.add(item["id"])
                    all_items.append(item)
                    processed_count_in_page += 1

            logger.info(f"  ページ {page}: 有効アイテム {processed_count_in_page}件 / 候補 {len(item_elements)}件 (累計: {len(all_items)}件)")
            
            # Limit to 50 pages
            if page > 50:
                 logger.info("  ページ上限到達 (50ページ)")
                 break

            page += 1

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
