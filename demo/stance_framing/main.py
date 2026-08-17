import json
import time
import os
import csv
import urllib.request
from datetime import datetime

output_dir = "/app/output"
csv_file = os.path.join(output_dir, "results.csv")

input_content = ""
target_entity = "Unknown"

# Poll until SUMMARIZER has finished
summarizer_done = False
while not summarizer_done:
    try:
        if os.path.exists(csv_file):
            with open(csv_file, mode='r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 3:
                        if row[1] == "API_FEED":
                            data = json.loads(row[2])
                            input_content = data["results"][0]["content"]
                        elif row[1] == "NER_EXTRACTOR":
                            data = json.loads(row[2])
                            if "entities" in data and len(data["entities"]) > 0:
                                target_entity = data["entities"][0].get("word", "Unknown")
                        elif row[1] == "SUMMARIZER":
                            summarizer_done = True
    except Exception:
        pass
    if not summarizer_done:
        time.sleep(1)

print("=== [STANCE & FRAMING ENGINE] Calling LIVE MuRIL Classifiers ===")

sf_output = {"input_text": input_content, "model_used": "google/muril-base-cased & IndicBERTv2 (LIVE)"}

def fetch_with_retry(url, data_dict, max_retries=10):
    for i in range(max_retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(data_dict).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if i == max_retries - 1:
                raise e
            time.sleep(5)

try:
    # Sentiment
    sf_output["sentiment_analysis"] = fetch_with_retry("http://nlp-engine:8001/sentiment", {"text": input_content})
        
    # Framing
    sf_output["framing_analysis"] = fetch_with_retry("http://nlp-engine:8001/framing", {"text": input_content})
        
    # Stance
    if target_entity != "Unknown":
        sf_output["stance_analysis"] = fetch_with_retry("http://nlp-engine:8001/stance", {"text": input_content, "target_entity": target_entity})
            
except Exception as e:
    sf_output["error"] = str(e)

with open(csv_file, mode='a', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "STANCE_FRAMING", json.dumps(sf_output, ensure_ascii=False)])

print(json.dumps(sf_output, indent=2, ensure_ascii=False))
print("=== [STANCE & FRAMING ENGINE] Matrix Data Calculated. Saved to CSV. ===\n")
