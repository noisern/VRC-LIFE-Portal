
from bs4 import BeautifulSoup
import sys

def test_parse():
    try:
        with open("booth_debug_v2.html", "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        print("booth_debug_v2.html not found.")
        return

    soup = BeautifulSoup(html, "html.parser")
    
    # Same selector as in scraping script
    item_elements = soup.select(
        "[class*='item-card'], .shop-item-card, [data-tracking-name='items']"
    )

    print(f"Found {len(item_elements)} item elements.")

    count = 0
    for i, item_element in enumerate(item_elements):
        if count >= 5: break # Check first 5 items

        # Logic from booth_scraper.py
        
        # 1. Check link first (mimicking parse_item)
        link_el = item_element.select_one("a[href*='/items/']")
        if not link_el:
            # print(f"Element {i}: No link found. Skipping.")
            continue
            
        print(f"Element {i} (Class: {item_element.get('class')}):")
        
        # 2. Extract thumbnail
        thumb_el = item_element.select_one(".js-thumbnail-image")
        thumbnail_url = ""
        original_url = ""

        if thumb_el:
            original_url = thumb_el.get("data-original") or thumb_el.get("data-src") or ""
            print(f"  [Method 1 .js-thumbnail-image] Found! URL: {original_url}")
        else:
            print(f"  [Method 1 .js-thumbnail-image] Not found.")

        if not original_url:
            img_el = item_element.select_one("img")
            if img_el:
                original_url = img_el.get("data-src") or img_el.get("src") or ""
                print(f"  [Method 2 img tag] Found! URL: {original_url}")
            else:
                print(f"  [Method 2 img tag] Not found.")

        if original_url:
            if "shops/badges" not in original_url:
                thumbnail_url = f"https://wsrv.nl/?url={original_url}&output=webp"
                print(f"  -> Final Thumbnail URL: {thumbnail_url}")
            else:
                 print("  -> Rejected: VRChat badge detected.")
        else:
             print("  -> FAILED to extract any URL.")
        
        count += 1

if __name__ == "__main__":
    test_parse()
