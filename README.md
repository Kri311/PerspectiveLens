# PerspectiveLens

PerspectiveLens is a text analytics platform that helps readers compare how different news publishers report the same event.

Instead of showing a single news article, the platform collects reports from multiple publishers, identifies articles discussing the same event, extracts important information, and presents different reporting perspectives. The goal is to help readers understand how coverage differs across sources without modifying the original articles.

The platform does not rewrite news, change the tone of an article, or decide which publisher is correct. It only analyzes publicly available news articles and presents factual comparisons so readers can form their own opinions.

---

# Why PerspectiveLens?

People often consume news from only one publisher. While the facts may remain the same, different publishers may emphasize different details, use different language, or focus on different aspects of an event.

PerspectiveLens brings these reports together and allows readers to compare them side by side. Instead of relying on a single source, users can understand how multiple publishers describe the same event.

---

# Project Objectives

* Collect recent news articles from multiple publishers.
* Detect articles discussing the same event.
* Extract important information from every article.
* Compare reporting across publishers.
* Generate factual perspectives based on published content.
* Present the information in a clear and structured format.

---

# Features

## News Collection

The platform continuously collects recent news articles from multiple publishers and organizes them based on the events they describe.

---

## Text Preprocessing

The collected articles are cleaned before analysis.

This step includes:

* Removing unwanted characters.
* Removing duplicate content.
* Normalizing the text.
* Preparing the content for further processing.

---

## Named Entity Recognition

Important entities are extracted from every article.

Examples include:

* People
* Organizations
* Countries
* Cities
* Locations
* Dates
* Events

---

## Event Extraction

Each article is analyzed to identify the main event.

The extracted information includes:

* What happened
* Who was involved
* Where it happened
* When it happened
* Actions performed
* Outcomes

---

## Event Clustering

Articles describing the same real-world event are grouped together.

This helps prevent duplicate stories and creates a single event page containing reports from multiple publishers.

---

## Perspective Analysis

Once articles are grouped, the platform compares how each publisher reports the event.

The comparison includes:

* Headlines
* Important facts covered
* Information omitted
* Order of information
* Level of detail
* Reporting style

The original articles are never modified.

---

## Bias Analysis

The platform identifies measurable reporting characteristics such as:

* Emotional language
* Subjective statements
* Opinion-based wording
* Neutral reporting
* Consistency across publishers

The analysis is descriptive and does not determine whether a publisher is right or wrong.

---

## Perspective Generation

Using information collected from multiple publishers, the platform generates structured perspectives that summarize how different sources describe the same event.

These perspectives are based only on published information and do not introduce new facts or alter the meaning of the original articles.

---

## Comparison Dashboard

The final interface presents all information in one place.

Users can view:

* Event summary
* Related news articles
* Timeline of events
* Important entities
* Publisher comparison
* Reporting differences
* Generated perspectives

---

# System Workflow

1. Collect news articles from multiple publishers.
2. Clean and preprocess the article text.
3. Extract named entities.
4. Extract the main event from each article.
5. Group articles discussing the same event.
6. Compare reporting across publishers.
7. Analyze reporting characteristics.
8. Generate factual perspectives.
9. Display the results through the user interface.

---

# Technology Stack

## Backend

* Python
* FastAPI

## Frontend

* React
* Tailwind CSS

## Database

* PostgreSQL
* Redis

## Search Engine

* Elasticsearch

## Text Analytics

* Text preprocessing
* Named Entity Recognition
* Event Extraction
* Text Similarity
* Sentence Embeddings
* Clustering

## Machine Learning

* Transformer models
* Sentence embedding models
* Similarity models
* Classification models

---

# Expected Output

For every news event, PerspectiveLens provides:

* Event title
* Event summary
* Related articles
* Timeline
* Important people
* Organizations
* Locations
* Publisher comparison
* Reporting differences
* Multiple factual perspectives

---

# Applications

PerspectiveLens can be used for:

* News aggregation
* Journalism
* Media research
* Academic research
* Fact-checking support
* Public awareness
* Educational purposes

---

# Limitations

* The platform only analyzes publicly available news articles.
* The quality of the analysis depends on the available news sources.
* The platform does not verify whether an event actually occurred.
* It does not determine which publisher is correct.
* It does not rewrite or modify original news articles.

---

# Future Work

* Real-time news streaming
* Support for multiple languages
* Cross-country news comparison
* Interactive event timelines
* Historical event analysis
* Source reliability indicators
* Personalized news recommendations
* Mobile application support

---

# Project Goal

The goal of PerspectiveLens is to make news consumption more transparent by allowing readers to compare how multiple publishers report the same event. Instead of presenting a single version of a story, the platform provides structured comparisons and factual perspectives so users can understand different styles of reporting and make informed decisions.
