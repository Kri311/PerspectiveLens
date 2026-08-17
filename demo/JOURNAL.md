# Faculty Demonstration: Separated NLP Containers

## Objective
This directory was created specifically to demonstrate the modular architecture of PerspectiveLens to the faculty. The goal is to explicitly showcase:
1. What the raw JSON API feeds (from NewsData.io / Currents API) look like.
2. How the monolithic NLP engine can be conceptualized (and practically separated) into distinct, specialized containers.
3. The exact structured JSON output produced by each step of the pipeline.

## Implementation Details

We have implemented a `docker-compose.yml` that orchestrates four isolated containers. Instead of loading the heavy 5GB PyTorch models into a single GPU instance (which is how the production app optimizes memory), this demo isolates the logic into sequential micro-processes. 

When you run this demo, the containers execute in a chain:

### 1. `api_feed_fetcher`
* **Role**: Simulates the ingestion worker.
* **Output Demonstrated**: The raw API JSON structure containing the `article_id`, publication date, source metadata, and the raw Tamil text string.

### 2. `ner_extractor`
* **Role**: Simulates the `ai4bharat/IndicNER` extraction model.
* **Output Demonstrated**: How the raw text is parsed into recognized entities (B-LOC for locations like Chennai, B-PER for people like M.K. Stalin, and B-DESIG for designations like Chief Minister) with confidence scores.

### 3. `summarizer`
* **Role**: Simulates the `mT5_multilingual_XLSum` abstractive summarization model.
* **Output Demonstrated**: Shows the generation of a concise, neutral Tamil summary from a verbose news article.

### 4. `stance_framing`
* **Role**: Simulates the `google/muril-base-cased` zero-shot classification pipelines.
* **Output Demonstrated**: Provides the probability distributions that power our Perspective Matrix. It outputs the Sentiment (Positive/Negative/Neutral), Stance towards a specific entity (Support/Oppose), and the Framing category (Policy/Achievement, Controversy, etc.).

## How to Run the Demo

To run this demonstration for your faculty, navigate to this directory and run:

```bash
cd demo
docker compose up
```

You will see the containers sequentially start up, process their simulated payload, and print the beautifully formatted JSON outputs directly to the console, making it extremely easy to explain the data transformation pipeline step-by-step.

### CSV Output Logging
Every time you run `docker compose up`, each container will automatically append its generated output payload to a central CSV file located at:
`demo/output/results.csv`

This file is formatted as: `Timestamp, Component, Data (JSON)`, giving you a persistent history of executions that you can easily open in Excel or a spreadsheet program.
