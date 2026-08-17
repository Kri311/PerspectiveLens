import json
import time
import os
import csv
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import re

output_dir = "/app/output"
os.makedirs(output_dir, exist_ok=True)
csv_file = os.path.join(output_dir, "results.csv")

# Delete old CSV on fresh start
if os.path.exists(csv_file):
    os.remove(csv_file)

print("=== [API FEED FETCHER] Fetching LIVE Feed from Google News Tamil ===")
try:
    req = urllib.request.Request("https://news.google.com/rss?hl=ta&gl=IN&ceid=IN:ta", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        xml_data = response.read()
    
    root = ET.fromstring(xml_data)
    item = root.find('.//item') # Gets the very first (latest) news article
    title = item.find('title').text
    description = item.find('description').text
    pubDate = item.find('pubDate').text
    
    content = re.sub('<[^<]+>', '', description).strip()
    if len(content) < len(title):
        content = title
        
    api_feed = {
        "status": "success",
        "results": [
            {
                "article_id": "live_news_001",
                "title": title,
                "pubDate": pubDate,
                "content": content,
                "language": "tamil"
            }
        ]
    }
except Exception as e:
    print(f"Failed to fetch live feed: {e}")
    api_feed = {"status": "error", "error": str(e)}

with open(csv_file, mode='w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Timestamp", "Component", "Data"])
    writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "API_FEED", json.dumps(api_feed, ensure_ascii=False)])

print(json.dumps(api_feed, indent=2, ensure_ascii=False))
print("=== [API FEED FETCHER] Extraction Complete. Saved to CSV. ===\n")
