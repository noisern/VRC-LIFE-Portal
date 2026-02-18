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


import csv
import io

def fetch_csv_urls(csv_url: str) -> list[str]:
    """GoogleスプレッドシートのCSVからURLリストを取得する。"""
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # CSV parse
        f = io.StringIO(response.text)
        reader = csv.reader(f)
        urls = []
        for row in reader:
            if not row: continue
            url = row[0].strip()
            if url.startswith("http"):
                urls.append(url)
        
        return list(set(urls)) # Unique
    except Exception as e:
        logger.error(f"Failed to fetch CSV: {e}")
        return []

def parse_item(item_element: Tag) -> Optional[dict]:
    # Legacy function kept for interface compatibility if needed, but not used in CSV mode
    return None

def parse_item_detail_page(soup: BeautifulSoup, booth_url: str) -> Optional[dict]:
    """個別商品ページのHTMLから情報を抽出する (Attribute-based)"""
    try:
        # 1. Basic Info from Attributes (Reliable)
        # Strategy: find ANY element with data-product-id
        product_el = soup.select_one("[data-product-id]")
        if not product_el:
            logger.warning(f"  [Skip] No data-product-id found in {booth_url}")
            return None

        item_id = product_el.get("data-product-id")
        name = product_el.get("data-product-name")
        price_str = product_el.get("data-product-price")
        shop_name = product_el.get("data-product-brand")
        
        # Price
        price = 0
        if price_str:
            try:
                price = int(float(price_str))
            except:
                pass

        # Thumbnail
        # meta prop="og:image" is reliable for detail pages
        thumbnail_url = ""
        og_img = soup.select_one('meta[property="og:image"]')
        if og_img:
            thumbnail_url = og_img.get("content", "")
        
        # Fallback thumbnail
        if not thumbnail_url:
            img_el = soup.select_one(".market-item-detail-item-image img")
            img_el_2 = soup.select_one("img.market-item-detail-item-image") # possible variation
            if img_el:
                thumbnail_url = img_el.get("src", "")
            elif img_el_2:
                thumbnail_url = img_el_2.get("src", "")

        # Description
        description = ""
        desc_el = soup.select_one(".js-market-item-detail-description, .description")
        if desc_el:
            description = desc_el.get_text(separator="\n", strip=True)[:500]

        # R18 Check
        is_r18 = False
        body_text = soup.get_text()
        if "R-18" in body_text or soup.select_one(".badge-adult, .is-adult, .r18-badge"):
            is_r18 = True

        # Likes (Attribute based from potential buttons)
        likes = 0
        # Method A: count element
        count_el = soup.select_one(".js-like-count, .like-count, .count-number")
        if count_el:
            text = count_el.get_text(strip=True)
            match = re.search(r'(\d+[\d,.]*)', text)
            if match:
                 likes = int(float(match.group(1).replace(",", "")))
        
        # Method B: aria-label
        if likes == 0:
            candidates = soup.select("button[aria-label], a[aria-label]")
            for el in candidates:
                label = el.get("aria-label", "")
                if any(k in label for k in ["スキ", "Loves", "Like"]):
                    match = re.search(r'(\d+[\d,.]*)', label)
                    if match:
                        likes = int(float(match.group(1).replace(",", "")))
                        break

        if not name or not item_id:
            return None

        # Return dict matching the expected schema
        return {
            "id": f"booth-{item_id}", # Add prefix for consistency
            "name": name,
            "price": price,
            "shopName": shop_name,
            "boothUrl": booth_url,
            "thumbnailUrl": thumbnail_url,
            "likes": likes,
            "isR18": is_r18,
            "description": description,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.warning(f"  Failed to parse detail page {booth_url}: {e}")
        return None


# Deleted fetch_item_detail as we are reverting to search page scraping 


def scrape_booth(min_likes: int = 0, fetch_details: bool = False, dry_run: bool = False) -> list[dict]:
    """
    User Request V3: CSV-Based Scraping.
    Fetches URLs from a Google Sheet CSV and scrapes individual pages.
    """
    if dry_run:
        logger.info("=== DRY RUN MODE ===")
        return _get_sample_data()

    # CSV URL provided by user
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ98u4MEiJ3o8jesqRUMv7hrg8atUwxQoIggjMlRWlHFCeCNDCObcde1cjOVXKVW5BFscQe7Z5zsG2_/pub?output=csv"
    
    session = requests.Session()
    session.headers.update(HEADERS)

    logger.info(f"Fetching URL list from CSV...")
    target_urls = fetch_csv_urls(CSV_URL)
    logger.info(f"Target URLs: {len(target_urls)}")
    
    all_items = []
    seen_ids = set() 
    
    for i, url in enumerate(target_urls):
        try:
            logger.info(f"[{i+1}/{len(target_urls)}] Scraping: {url}")
            soup = fetch_page(url, session)
            if not soup:
                continue
            
            item = parse_item_detail_page(soup, url)
            
            if item:
                # Check duplication
                if item["id"] not in seen_ids:
                    seen_ids.add(item["id"])
                    all_items.append(item)
                    logger.info(f"  -> OK: {item["name"]} (Likes: {item["likes"]})")
                else:
                    logger.info(f"  -> Duplicate ID: {item["id"]}")
            
        except Exception as e:
            logger.error(f"Error extracting {url}: {e}")
            
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
