import json
import time
import os
import csv
import urllib.request
from datetime import datetime

output_dir = "/app/output"
csv_file = os.path.join(output_dir, "results.csv")

input_content = ""

# Poll until NER_EXTRACTOR has finished (to ensure sequential execution)
ner_done = False
while not ner_done:
    try:
        if os.path.exists(csv_file):
            with open(csv_file, mode='r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 3 and row[1] == "API_FEED":
                        data = json.loads(row[2])
                        input_content = data["results"][0]["content"]
                    if len(row) >= 3 and row[1] == "NER_EXTRACTOR":
                        ner_done = True
    except Exception:
        pass
    if not ner_done:
        time.sleep(1)

print("=== [SUMMARIZER] Calling LIVE mT5 Summarization Engine ===")
nlp_url = "http://nlp-engine:8001/summarize"
summary_output = {}

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
    prompt = f"Summarize the following in Tamil: {input_content}"
    result = fetch_with_retry(nlp_url, {"text": prompt, "max_length": 150})
    summary_output = {
        "input_text": input_content,
        "model_used": "mT5_multilingual_XLSum (LIVE)",
        "abstractive_summary": result.get("summary", "")
    }
except Exception as e:
    summary_output = {"error": str(e), "input_text": input_content}

with open(csv_file, mode='a', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "SUMMARIZER", json.dumps(summary_output, ensure_ascii=False)])

print(json.dumps(summary_output, indent=2, ensure_ascii=False))
print("=== [SUMMARIZER] Neutral Summary Generated. Saved to CSV. ===\n")
