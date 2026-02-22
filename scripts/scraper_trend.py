"""
Trend Scraper & AI Writer for VRC-LIFE Portal
Sources: Google News RSS (Keywords: VRChat, VRC, Metaverse)
AI: Google Gemini API
Function:
1. Fetches latest news via RSS.
2. Uses Gemini to filter for POSITIVE/CREATIVE topics (filters out drama/bugs).
3. Writes catchy magazine-style short articles.
4. Updates docs/data/trends.json.
"""

import os
import json
import logging
import feedparser
import google.generativeai as genai
from datetime import datetime, timezone, timedelta
import html

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
RSS_URLS = [
    "https://news.google.com/rss/search?q=VRChat+when:1d&hl=ja&gl=JP&ceid=JP:ja",
    "https://news.google.com/rss/search?q=VRChat+イベント+when:1d&hl=ja&gl=JP&ceid=JP:ja",
    "https://news.google.com/rss/search?q=VRChat+ワールド+when:1d&hl=ja&gl=JP&ceid=JP:ja",
]
OUTPUT_FILE = "docs/data/trends.json"
MAX_ITEMS_TO_PROCESS = 10  # Process top N items from RSS to save API tokens
HISTORY_LIMIT = 30         # Keep last N articles in JSON

def setup_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables.")
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

def fetch_rss_news():
    entries = []
    seen_links = set()
    
    for url in RSS_URLS:
        try:
            logger.info(f"Fetching RSS: {url}")
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: # Take top 5 from each feed
                if entry.link not in seen_links:
                    seen_links.add(entry.link)
                    # Clean title
                    title = entry.title.split(" - ")[0] # Remove source name
                    entries.append({
                        "title": title,
                        "link": entry.link,
                        "snippet": html.unescape(entry.summary if 'summary' in entry else entry.title),
                        "published": entry.published if 'published' in entry else str(datetime.now())
                    })
        except Exception as e:
            logger.error(f"Error fetching RSS {url}: {e}")
            
    return entries[:MAX_ITEMS_TO_PROCESS]

def generate_article_gemini(model, news_items):
    if not news_items:
        return []

    # Prompt Engineering
    prompt = """
    You are a stylish editor for "VRC-LIFE", a magazine about VRChat culture.
    
    Task:
    Review the following news items and select those that are:
    1. POSITIVE (Fun events, new worlds, beautiful items, creative tech logs).
    2. EXCITING (Something that makes users want to login).
    
    STRICTLY EXCLUDE:
    - Drama, flaming, harassment reports.
    - Bugs, technical troubleshooting, server outages.
    - Negative corporate news.
    - Duplicate topics.
    
    For the selected items, write a short, stylish article in Japanese.
    
    Format: JSON Array
    [
      {
        "title": "Catchy, Magazine-style Headline (No 'VRChat' prefix)",
        "content": "Stylish summary of what happened. 100-150 characters. Use polite but trendy tone.",
        "tags": ["#Tag1", "#Tag2"],
        "sourceUrl": "Original Link",
        "date": "YYYY-MM-DD"
      }
    ]
    
    Input Data:
    """
    
    for item in news_items:
        prompt += f"- [Title] {item['title']}\n  [Link] {item['link']}\n  [Snippet] {item['snippet']}\n  [Date] {item['published']}\n\n"

    try:
        response = model.generate_content(prompt)
        text = response.text
        # Clean markdown code blocks if present
        text = text.replace("```json", "").replace("```", "").strip()
        articles = json.loads(text)
        return articles
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        return []

def main():
    logger.info("Starting Trend Scraper...")
    
    # 1. Setup AI
    model = setup_gemini()
    if not model:
        return

    # 2. Fetch News
    raw_news = fetch_rss_news()
    logger.info(f"Fetched {len(raw_news)} raw items.")
    
    if not raw_news:
        logger.info("No news found.")
        return

    # 3. AI Processing
    logger.info("Requesting AI analysis...")
    new_articles = generate_article_gemini(model, raw_news)
    logger.info(f"Generated {len(new_articles)} articles.")
    
    if not new_articles:
        logger.info("No articles generated (maybe all were filtered out).")
        return

    # 4. Load Existing Data & Merge
    existing_data = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            pass
            
    # Prepend new articles (filtering duplicates by URL)
    existing_urls = {item.get('sourceUrl') for item in existing_data}
    
    added_count = 0
    for article in new_articles:
        if article.get('sourceUrl') not in existing_urls:
            # Ensure date format
            if 'date' not in article:
                article['date'] = datetime.now().strftime('%Y-%m-%d')
                
            existing_data.insert(0, article)
            added_count += 1
            
    # Trim to limit
    final_data = existing_data[:HISTORY_LIMIT]
    
    # 5. Save
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Saved. Added {added_count} new articles. Total: {len(final_data)}")

if __name__ == "__main__":
    main()
