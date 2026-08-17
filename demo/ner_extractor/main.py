import json
import time
import os
import csv
import urllib.request
from datetime import datetime

output_dir = "/app/output"
csv_file = os.path.join(output_dir, "results.csv")

input_content = ""

# Poll until API_FEED is present in CSV
while not input_content:
    try:
        if os.path.exists(csv_file):
            with open(csv_file, mode='r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 3 and row[1] == "API_FEED":
                        data = json.loads(row[2])
                        if "results" in data:
                            input_content = data["results"][0]["content"]
    except Exception:
        pass
    if not input_content:
        time.sleep(1)

print("=== [NER EXTRACTOR] Calling LIVE IndicNER Engine ===")
nlp_url = "http://nlp-engine:8001/ner"
ner_output = {}

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
    result = fetch_with_retry(nlp_url, {"text": input_content})
    ner_output = result
    ner_output["input_text"] = input_content
    ner_output["model_used"] = "ai4bharat/IndicNER (LIVE)"
except Exception as e:
    ner_output = {"error": str(e), "input_text": input_content}

with open(csv_file, mode='a', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "NER_EXTRACTOR", json.dumps(ner_output, ensure_ascii=False)])

print(json.dumps(ner_output, indent=2, ensure_ascii=False))
print("=== [NER EXTRACTOR] Entities Mapped. Saved to CSV. ===\n")
