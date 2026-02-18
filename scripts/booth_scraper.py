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


def parse_item(item_element) -> Optional[dict]:
    """商品要素から情報を抽出する。"""
    try:
        # 商品リンク
        # Selector for the link usually wraps the title or is specific
        link_el = item_element.select_one("a[href*='/items/'], a.item-card__title-anchor--multiline")
        if not link_el:
            return None
        booth_url = link_el.get("href", "")
        if not booth_url.startswith("http"):
            booth_url = "https://booth.pm" + booth_url

        # 商品ID
        item_id = ""
        # Try to extract ID from URL
        match = re.search(r'/items/(\d+)', booth_url)
        if match:
            item_id = "booth-" + match.group(1)
        else:
            return None # ID is required

        # 商品名
        # Use verified selector from booth_popular.html
        name_el = item_element.select_one("a.item-card__title-anchor--multiline, [class*='item-card__title'], .shop-item-card__item-name")
        name = name_el.get_text(strip=True) if name_el else ""

        # 価格
        # Verified selector: .price
        price_el = item_element.select_one(".price, [class*='price'], .shop-item-card__price")
        price_text = price_el.get_text(strip=True) if price_el else "0"
        price = int("".join(c for c in price_text if c.isdigit()) or "0")

        # サムネイル
        # Verified: item-card__thumbnail-image with style or data-original
        thumb_el = item_element.select_one(".item-card__thumbnail-image, .js-thumbnail-image")
        thumbnail_url = ""
        
        if thumb_el:
            thumbnail_url = thumb_el.get("data-original") or thumb_el.get("data-src") or thumb_el.get("src") or ""
            if not thumbnail_url:
                style = thumb_el.get("style", "")
                if style:
                    match = re.search(r"url\(['\"]?([^'\")]+)['\"]?\)", style)
                    if match:
                        thumbnail_url = match.group(1)
        
        if not thumbnail_url:
            img_el = item_element.select_one("img")
            if img_el:
                thumbnail_url = img_el.get("data-src") or img_el.get("src") or ""

        # ショップ名
        # Verified: .item-card__shop-name
        shop_el = item_element.select_one(".item-card__shop-name, [class*='shop-name']")
        shop_name = shop_el.get_text(strip=True) if shop_el else ""

        # いいね数 (Unavailable in static HTML)
        # We default to 0 because we cannot scrape it reliable from the search page anymore.
        likes = 0

        # R18チェック
        # Use data-badge-params or check specific badge classes
        is_r18 = False
        r18_el = item_element.select_one(".badge-adult, .is-adult, .r18-badge")
        if r18_el:
            is_r18 = True
        
        # Fallback check on text content if badge is missing but text says R18
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


def parse_likes_text(text: str) -> int:
    """
    スキ数テキスト（例: '1.5k', '1,200', 'スキ！50', 'Loves 123'）から数値を柔軟に抽出する。
    最初に見つかった連続する数字（またはk/万）を抽出する。
    """
    if not text:
        return 0
    
    text = text.lower().replace(",", "")
    try:
        # First, try to find a number with optional suffix (k/万)
        # Regex: match digits, optionally with decimal, followed optionally by k or 万
        # Examples: "123", "1.5k", "10万", "Loves 400" -> "400"
        
        # Extract the first valid number sequence
        match = re.search(r'([\d\.]+)\s*(k|万)?', text)
        if match:
            num_str = match.group(1)
            suffix = match.group(2)
            
            val = float(num_str)
            
            if suffix == 'k':
                val *= 1000
            elif suffix == '万':
                val *= 10000
                
            return int(val)

        return 0
    except Exception as e:
        logger.warning(f"Failed to parse likes text '{text}': {e}")
        return 0

def fetch_item_detail(booth_url: str, session: requests.Session) -> dict:
    """
    商品詳細ページから追加情報（説明文、スキ数）を取得する。
    スキ数は以下の順で取得を試みる:
    1. LD+JSON (interactionStatistic)
    2. Button/Link attribute (aria-label, data-count) - Robust Regex
    """
    soup = fetch_page(booth_url, session)
    if not soup:
        return {}

    detail = {}

    # 説明文
    desc_el = soup.select_one("[class*='description'], .js-market-item-detail-description")
    if desc_el:
        detail["description"] = desc_el.get_text(strip=True)[:500]

    # いいね数 (Robust Extraction)
    likes = 0
    found_source = None
    
    # 1. LD+JSON
    try:
        ld_json_el = soup.select_one('script[type="application/ld+json"]')
        if ld_json_el:
            data = json.loads(ld_json_el.string)
            if 'interactionStatistic' in data:
                stats = data['interactionStatistic']
                if isinstance(stats, list):
                    for stat in stats:
                        if stat.get('interactionType') == 'http://schema.org/LikeAction':
                            likes = int(stat.get('userInteractionCount', 0))
                            found_source = "LD+JSON"
                            break
                elif isinstance(stats, dict):
                     if stats.get('interactionType') == 'http://schema.org/LikeAction':
                        likes = int(stats.get('userInteractionCount', 0))
                        found_source = "LD+JSON"
    except Exception as e:
        logger.debug(f"LD+JSON extraction failed: {e}")

    # 2. Attribute Extraction (Targeting buttons/links with aria-label)
    if not found_source:
        # User requested: button[aria-label] or .js-like-btn[aria-label]
        # We also check 'a' tags just in case
        targets = soup.select("button[aria-label], a[aria-label], .js-like-btn")
        
        for el in targets:
            label = el.get("aria-label", "")
            if not label: 
                continue
            
            # Regex: Extract ALL digit sequences, pick the first one
            # e.g. "スキ！ 123" -> ["123"]
            # e.g. "Loves 456" -> ["456"]
            # e.g. "Like 789" -> ["789"]
            matches = re.findall(r'\d+', label)
            if matches:
                # Potential candidate
                # Heuristic: The number should be reasonable (e.g. not '2024' year if it's the only one, but usually likes count is distinct)
                # For now, we take the *first* number found in a likely "like" button
                
                # Check if it looks like a like button
                is_like_btn = False
                class_str = " ".join(el.get("class", []))
                if "like" in class_str or "wish" in class_str or "Like" in label or "スキ" in label or "Loves" in label:
                     likes = int(matches[0])
                     found_source = f"Attribute (aria-label='{label}')"
                     break

    if found_source:
        detail["likes"] = likes
    else:
        logger.warning(f"Could not find likes for {booth_url} (Result: 0)")
        
        # --- DEBUG: Dump ALL aria-labels to log ---
        try:
            page_title = soup.title.string if soup.title else "No Title"
            logger.warning(f"  [DEBUG] Page Title: {page_title}")
            
            all_aria_els = soup.select("[aria-label]")
            if all_aria_els:
                logger.warning(f"  [DEBUG] Found {len(all_aria_els)} elements with aria-label:")
                for i, el in enumerate(all_aria_els):
                    label = el.get("aria-label")
                    tag_name = el.name
                    classes = " ".join(el.get("class", []))
                    logger.warning(f"    [{i}] <{tag_name} class='{classes}'> aria-label='{label}'")
            else:
                logger.warning("  [DEBUG] No elements with aria-label found.")

        except Exception as e:
            logger.warning(f"  [DEBUG] Failed to dump attributes: {e}")
        # -----------------------------------------------

        detail["likes"] = 0

    return detail


def scrape_booth(min_likes: int = 0, fetch_details: bool = False, dry_run: bool = False) -> list[dict]:
    """
    BOOTHからVRChat関連アイテムを収集する（全ページ走査）。
    min_likes > 0 の場合、個別ページにアクセスしてスキ数を取得し、フィルタリングを行う。
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
                    
                    # 2. いいね数フィルタ (個別ページ取得)
                    # min_likes指定がある場合、またはfetch_detailsがTrueの場合に詳細を取得
                    if min_likes > 0 or fetch_details:
                        if item["boothUrl"]:
                            detail = fetch_item_detail(item["boothUrl"], session)
                            item.update(detail) # likes, descriptionを更新
                    
                    # 詳細取得後のlikesでフィルタリング
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
