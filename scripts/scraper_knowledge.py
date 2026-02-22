"""
KNOWLEDGE Scraper for VRC-LIFE Portal
Source: Google Spreadsheet (Sheet: KNOWLEDGE)
Syncs valid URLs from Sheet to knowledge.json.
"""

import requests
import json
import logging
from datetime import datetime, timezone

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
# We will use the pubhtml endpoint and parse the HTML table, as it usually contains all sheets
# if we don't specify gid, or we can look for the tab name "KNOWLEDGE"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ98u4MEiJ3o8jesqRUMv7hrg8atUwxQoIggjMlRWlHFCeCNDCObcde1cjOVXKVW5BFscQe7Z5zsG2_/pubhtml"
OUTPUT_FILE = "docs/data/knowledge.json"
USER_AGENT = "VRC-LIFE Portal Bot"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def fetch_sheet_data(url: str, target_sheet_name="KNOWLEDGE") -> list[dict]:
    try:
        logger.info(f"Fetching from {url}")
        response = requests.get(url, headers=HEADERS)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Google Sheets pubhtml structure:
        # <ul id="sheet-menu"> contains <li> elements with sheet names
        # <div id="sheets-viewport"> contains <div> elements for each sheet's content
        
        # 1. Find the GID for the target sheet name
        sheet_menu = soup.find('ul', id='sheet-menu')
        target_gid = None
        if sheet_menu:
            for li in sheet_menu.find_all('li'):
                a_tag = li.find('a')
                if a_tag and target_sheet_name in a_tag.get_text():
                    # The id looks like "sheet-button-123456"
                    li_id = li.get('id', '')
                    target_gid = li_id.replace('sheet-button-', '')
                    logger.info(f"Found KNOWLEDGE sheet with GID: {target_gid}")
                    break
                    
        # 2. Find the corresponding table
        target_table = None
        if target_gid:
            # Sheets are in divs like <div id="123456">...<table>...
            sheet_div = soup.find('div', id=target_gid)
            if sheet_div:
                target_table = sheet_div.find('table')
        else:
            # Fallback: just grab the first table if it's single sheet export
            logger.warning(f"Could not find specific sheet tab for {target_sheet_name}. Trying fallback.")
            target_table = soup.find('table', class_='waffle') or soup.find('table')

        if not target_table:
            logger.error("No table found in Sheet HTML matching the criteria.")
            return []

        rows = target_table.find_all('tr')
        items = []
        
        # KNOWLEDGE columns:
        # id | status | category | title | subtitle | publish_date | thumbnail_url | image_url | excerpt | tags | content
        
        # Find header index mapping
        header_row = None
        headers = []
        
        # Assume first non-empty row is header
        for row in rows:
            cells = row.find_all('td')
            row_texts = [c.get_text(strip=True) for c in cells]
            if any(row_texts) and 'id' in [t.lower() for t in row_texts]:
                header_row = row
                headers = [t.lower() for t in row_texts]
                break
                
        if not header_row:
             logger.error("Could not find header row with 'id'")
             return []
             
        # Helper index finder
        def get_idx(name):
            try:
                return headers.index(name)
            except ValueError:
                return -1

        idx_id = get_idx('id')
        idx_status = get_idx('status')
        idx_category = get_idx('category')
        idx_title = get_idx('title')
        idx_subtitle = get_idx('subtitle')
        idx_publish_date = get_idx('publish_date')
        idx_thumbnail_url = get_idx('thumbnail_url')
        idx_image_url = get_idx('image_url')
        idx_excerpt = get_idx('excerpt')
        idx_tags = get_idx('tags')
        idx_content = get_idx('content')

        for i, row in enumerate(rows):
            if row == header_row:
                continue
                
            cells = row.find_all('td')
            if not cells:
                continue
                
            def get_text(idx):
                if idx >= 0 and idx < len(cells):
                    return cells[idx].get_text(strip=True)
                return ""

            item_id = get_text(idx_id)
            if not item_id:
                continue

            status = get_text(idx_status).lower()
            if status != 'published':
                continue

            # Check if title has markdown links or raw text, usually just raw text
            title = get_text(idx_title)
            
            # Content might have line breaks, bs4 get_text() lumps them if we aren't careful.
            # Replace <br> with \n before getting text for content
            if idx_content >= 0 and idx_content < len(cells):
                content_cell = cells[idx_content]
                # Replace <br> and <p> with newlines for basic markdown safety
                for br in content_cell.find_all("br"):
                    br.replace_with("\n")
                for p in content_cell.find_all("p"):
                    p.insert_after("\n")
                content = content_cell.get_text()
            else:
                content = ""

            tags_raw = get_text(idx_tags)
            tags = [t.strip() for t in tags_raw.split(',')] if tags_raw else []

            items.append({
                "id": str(item_id),
                "category": get_text(idx_category),
                "title": title,
                "subtitle": get_text(idx_subtitle),
                "publish_date": get_text(idx_publish_date),
                "thumbnail_url": get_text(idx_thumbnail_url),
                "image_url": get_text(idx_image_url),
                "excerpt": get_text(idx_excerpt),
                "tags": tags,
                "content": content,
                "fetchedAt": datetime.now(timezone.utc).isoformat()
            })
            
        return items
    except Exception as e:
        logger.error(f"Failed to fetch Sheet Data: {e}")
        return []

def main():
    logger.info("Starting KNOWLEDGE Scraper...")
    source_items = fetch_sheet_data(SHEET_URL)
    logger.info(f"Fetched {len(source_items)} valid items")
    
    # Sort by publish date (descending)
    source_items.sort(key=lambda x: x.get('publish_date', ''), reverse=True)
    
    # Save JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(source_items, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Saved {len(source_items)} articles to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
