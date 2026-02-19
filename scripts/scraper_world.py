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
WORLD_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ98u4MEiJ3o8jesqRUMv7hrg8atUwxQoIggjMlRWlHFCeCNDCObcde1cjOVXKVW5BFscQe7Z5zsG2_/pub?gid=162444085&single=true&output=csv" 
# ADDED gid=0 temporarily, user needs to verify the gid for "WORLD" sheet.
# If they used "Publish to Web" for the specific sheet, the URL is unique.
# I will use the one from booth_scraper as base but flag it.

OUTPUT_FILE = "docs/data/worlds.json"
USER_AGENT = "VRC-LIFE Portal Bot"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def fetch_csv_data(csv_url: str) -> list[dict]:
    """
    Fetch and parse CSV from Google Sheets.
    Columns:
    A: Name
    B: URL
    C: Category
    D: Date (YYYY-MM-DD)
    E: Author
    F: Description
    G: Custom Image URL (Fallback)
    """
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # Parse CSV
        f = io.StringIO(response.text)
        reader = csv.reader(f)
        items = []
        
        for i, row in enumerate(reader):
            # Skip header if it exists? Assuming user might have header.
            # Simple heuristic: check if col B looks like a URL.
            if len(row) < 6:
                continue
            
            world_name = row[0].strip()
            world_url = row[1].strip()
            category = row[2].strip()
            date_created = row[3].strip()
            author = row[4].strip()
            description = row[5].strip()
            custom_image_url = row[6].strip() if len(row) > 6 else ""

            if not world_url.startswith("http"):
                continue

            items.append({
                "name": world_name,
                "url": world_url,
                "category": category,
                "date_created": date_created,
                "author": author,
                "description": description,
                "custom_image_url": custom_image_url
            })
            
        return items
    except Exception as e:
        logger.error(f"Failed to fetch CSV: {e}")
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
    source_items = fetch_csv_data(WORLD_CSV_URL)
    logger.info(f"Fetched {len(source_items)} items from CSV")
    
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
            "fetchedAt": datetime.now(timezone.utc).isoformat()
        }
        final_items.append(world_obj)
        
    # 3. Save JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_items, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Saved {len(final_items)} worlds to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
