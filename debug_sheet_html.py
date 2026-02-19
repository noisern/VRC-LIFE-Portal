import requests
from bs4 import BeautifulSoup

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ98u4MEiJ3o8jesqRUMv7hrg8atUwxQoIggjMlRWlHFCeCNDCObcde1cjOVXKVW5BFscQe7Z5zsG2_/pub?gid=162444085&single=true&output=html"

def debug():
    print(f"Fetching {URL}...")
    try:
        resp = requests.get(URL)
        resp.encoding = 'utf-8'
        print(f"Status: {resp.status_code}")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        
        if not table:
            print("ERROR: No <table> found.")
            # Print first 500 chars to see what we got
            print(resp.text[:500])
            return

        rows = table.find_all('tr')
        print(f"Found {len(rows)} rows.")
        
        for i, row in enumerate(rows[:5]):
            cells = row.find_all('td')
            print(f"Row {i}: {len(cells)} cells")
            row_text = [c.get_text(strip=True) for c in cells]
            print(f"  Text: {row_text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug()
