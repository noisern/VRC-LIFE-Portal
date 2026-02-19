"""
World Scraper for VRC-LIFE Portal
Source: Google Spreadsheet (Sheet: WORLD)
Syncs valid URLs from Sheet to worlds.json.
Scrapes og:image from VRChat.com as auxiliary data.
"""

import requests
import csv
import io
import json
import re
import time
import logging
from datetime import datetime, timezone
from typing import Optional

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
# NOTE: This URL should point to the "WORLD" sheet CSV export.
# If using "Publish to Web", ensure the GID matches the WORLD sheet.
# For now, using the same base, User might need to update this or I will check if I can derive it.
# Update URL to the specific sheet's pubhtml endpoint which returns a table
# gid=162444085 is for the WORLD sheet
WORLD_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ98u4MEiJ3o8jesqRUMv7hrg8atUwxQoIggjMlRWlHFCeCNDCObcde1cjOVXKVW5BFscQe7Z5zsG2_/pubhtml/sheet?headers=false&gid=162444085"

OUTPUT_FILE = "docs/data/worlds.json"
USER_AGENT = "VRC-LIFE Portal Bot"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def clean_google_url(url: str) -> str:
    """Extract actual URL from Google redirect wrapper if present."""
    if "google.com/url" in url:
        try:
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            if 'q' in qs:
                return qs['q'][0]
        except:
            pass
    return url

def fetch_sheet_data(url: str) -> list[dict]:
    """
    Fetch and parse data from Google Sheets (HTML format).
    HTML Table Columns (based on inspection):
    0: Name
    1: URL (Link)
    2: Category (Tag)
    3: Date (YYYY-MM-DD)
    4: Author (Link + Text)
    5: Status (Ignored)
    6: Description
    """
    try:
        logger.info(f"Fetching from {url}")
        response = requests.get(url, headers=HEADERS)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # The table usually has class 'waffle'
        table = soup.find('table', class_='waffle') or soup.find('table')
        
        if not table:
            logger.error("No table found in Sheet HTML")
            # Log snippet for debugging
            logger.error(f"Response snippet: {response.text[:500]}")
            return []

        rows = table.find_all('tr')
        items = []
        
        # Skip header rows. 
        # Usually row 0 is headers, row 1 is freeze bar, row 2+ is data?
        # In the sample: Row 0 is Headers. Row 1 is empty (shim). Row 2 is data.
        # We can iterate and check content.
        
        for i, row in enumerate(rows):
            cells = row.find_all('td')
            if len(cells) < 3: # Need at least Name, URL, Category
                continue
                
            # Helper to get text safe
            def get_cell(idx):
                return cells[idx] if idx < len(cells) else None
                
            def get_text(idx):
                c = get_cell(idx)
                return c.get_text(strip=True) if c else ""

            # Check if this is a header row (heuristic: "ワールド名" in first cell)
            first_text = get_text(0)
            if "ワールド名" in first_text or not first_text:
                continue

            world_name = get_text(0)
            
            # URL is in cell 1 'a' tag
            c1 = get_cell(1)
            world_url_raw = c1.find('a')['href'] if c1 and c1.find('a') else get_text(1)
            world_url = clean_google_url(world_url_raw)

            if not world_url.startswith("http"):
                continue

            category = get_text(2)
            date_created = get_text(3)
            
            # Author: Cell 4
            c4 = get_cell(4)
            author = get_text(4)
            author_url = ""
            if c4:
                link = c4.find('a')
                if link and link.get('href'):
                    author_url = clean_google_url(link.get('href'))

            # Skip cell 5 (Status)
            description = get_text(6)
            
            # Custom Image: Not present in this HTML view, explicit empty
            custom_image_url = ""

            items.append({
                "name": world_name,
                "url": world_url,
                "category": category,
                "date_created": date_created,
                "author": author,
                "description": description,
                "custom_image_url": custom_image_url,
                "author_url": author_url
            })
            
        return items
    except Exception as e:
        logger.error(f"Failed to fetch Sheet Data: {e}")
        return []

def scrape_vrchat_image(url: str) -> str:
    """Scrape og:image from VRChat world URL."""
    try:
        # Rate limit
        time.sleep(1) 
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Failed to access {url}: status {response.status_code}")
            return ""
            
        html = response.text
        # Regex for og:image
        match = re.search(r'<meta property="og:image" content="(.*?)">', html)
        if match:
            return match.group(1)
        
        # Try twitter:image
        match = re.search(r'<meta name="twitter:image" content="(.*?)">', html)
        if match:
            return match.group(1)
            
        return ""
    except Exception as e:
        logger.warning(f"Error scraping {url}: {e}")
        return ""

def main():
    logger.info("Starting World Scraper...")
    
    # 1. Fetch Source Data
    source_items = fetch_sheet_data(WORLD_SHEET_URL)
    logger.info(f"Fetched {len(source_items)} items from Sheet")
    
    # 2. Process Items
    final_items = []
    
    for item in source_items:
        logger.info(f"Processing: {item['name']}")
        
        # Scrape Image
        image_url = ""
        
        # Try scraping first
        scraped_image = scrape_vrchat_image(item['url'])
        if scraped_image:
            image_url = scraped_image
            logger.info("  -> Found og:image")
        
        # Fallback
        if not image_url and item['custom_image_url']:
            image_url = item['custom_image_url']
            logger.info("  -> Used fallback Custom Image")
            
        if not image_url:
            logger.warning("  -> No image found")
            # We add it anyway, frontend can handle missing image?
            # Or skip? User said "スプシから消えたURLは、worlds.json からも削除".
            # Implies we keep what's IN the sheet.
            
        # Construct Final Object
        world_obj = {
            "name": item["name"],
            "url": item["url"],
            "category": item["category"],
            "date": item["date_created"],
            "author": item["author"],
            "description": item["description"],
            "thumbnailUrl": image_url,
            "authorUrl": item["author_url"],
            "fetchedAt": datetime.now(timezone.utc).isoformat()
        }
        final_items.append(world_obj)
        
    # 3. Save JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_items, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Saved {len(final_items)} worlds to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
