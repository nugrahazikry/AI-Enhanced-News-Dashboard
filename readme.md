# News Article Monitoring

A web application built with Flask that monitors and analyses news articles for any keyword. It scrapes articles from **Google News RSS** on-demand, then uses **Google Gemini AI** to automatically classify each article's sentiment (positive / neutral / negative), extract named entities (NER), and assign a news topic. The resulting dataset is surfaced through an interactive dashboard with 10+ chart types — including time-series trends, sentiment heatmaps, source bubble charts, Sankey diagrams, and radar charts — and an AI-generated narrative insight summarising coverage patterns.


# Table of Contents

- [For Developers](#for-developer)
  - [Project Structure](#project-structure)
  - [How to Run Locally](#how-to-run-the-apps-in-local)
- [For Users](#for-user)
  - [Apps Features](#apps-features)
  - [How to Use the Apps](#how-to-use-the-apps)


# For Developer

## Project Structure

```
.
├── app.py                          # Main Flask application and API routes
├── requirements.txt                # Python dependencies
├── readme.md                       # Project documentation
├── .env                            # Environment variables (GEN_AI_API_KEY) — not committed
├── images/
│   ├── visualization_1.png         # Screenshot: KPI cards and sentiment trend
│   ├── visualization_2.png         # Screenshot: bar charts and AI insight panel
│   └── visualization_3.png         # Screenshot: recent news content table
├── data/
│   └── *.xlsx / *.parquet          # Scraped and enriched news datasets
├── scripts/
│   ├── google_news_scraper.py      # Google News RSS scraper (day-looping for max results)
│   ├── data_processing.py          # AI pipeline: sentiment, NER, and topic classification
│   └── ai_generate_insight.py      # AI narrative insight generation
├── static/
│   ├── css/
│   │   └── style.css               # Application stylesheet
│   └── js/
│       └── main.js                 # Client-side JavaScript for UI interactions
└── templates/
    └── index.html                  # Main Jinja2 HTML template
```

**Key backend files:**

| File | Description |
|---|---|
| `app.py` | Main Flask application. Defines API routes (`/`, `/api/data/<keyword>`, `/api/run_analysis`, `/api/insight`), loads and caches the news dataset, computes all chart data server-side, and streams AI insights via Server-Sent Events |
| `scripts/google_news_scraper.py` | `GoogleNewsScraper` class. Queries Google News RSS day-by-day across a date range to maximise article yield, parses XML responses, and returns a structured DataFrame |
| `scripts/data_processing.py` | `run_processing_pipeline()`. Sends article headlines in batches to Gemini AI and parses JSON responses containing sentiment, NER entities, and topic labels for each article |
| `scripts/ai_generate_insight.py` | `generate_insight()`. Builds structured prompts from the filtered dataset and streams a narrative insight — broken into source analysis, entity analysis, and topic analysis — back to the frontend |

**Key frontend files:**

| File | Description |
|---|---|
| `templates/index.html` | Main Jinja2 HTML template. Contains the keyword selector, date-range picker, Run Analysis button, summary KPI cards, and all chart containers |
| `static/css/style.css` | Stylesheet for the entire web UI — layout, card components, chart containers, sidebar, and responsive styles |
| `static/js/main.js` | Client-side JavaScript. Fetches chart data from `/api/data/<keyword>`, renders all Plotly/Chart.js charts, triggers scraping and AI processing via `/api/run_analysis`, and streams AI insights via EventSource |


## How to run the apps in local

**Prerequisites:** Python 3.11 and a [Google AI Studio](https://aistudio.google.com/) API key.

**1. Clone the repository and navigate to the project directory:**

```bash
cd path/to/news-monitoring
```

**2. Create a virtual environment:**

```bash
python -m venv venv
```

**3. Activate the virtual environment:**

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**4. Install all required dependencies:**

```bash
pip install -r requirements.txt
```

**5. Create a `.env` file and add your Gemini API key:**

```
GEN_AI_API_KEY=your_google_ai_studio_api_key_here
```

**6. Run the application:**

```bash
python app.py
```

**7. Access the application in a browser:**

```
http://127.0.0.1:5000
```

# For User

## Apps Features

The application consists of five main areas accessible from a single-page dashboard.

![Main Visualization](images/main_visualization.png)

---

### 1. Keyword Selector & Run Analysis

A sidebar on the left provides controls for:

![Sidebar controls](images/visualization_1.png)

- **Keyword** — type or select the topic to monitor (e.g. "Pertamina")
- **Start Date / End Date** — date range for the news scrape
- **Language & Country** — locale settings passed to Google News RSS
- **Run Analysis** button — triggers a live scrape + AI enrichment pipeline and reloads all charts with fresh results

---

### 2. Summary KPI Cards

Four summary cards are displayed at the top of the main panel:

![Summary KPI Cards](images/visualization_2.png)

| Card | Description |
|---|---|
| **Total Mentions** | Total number of articles for the selected keyword, with week-over-week change |
| **Positive Mentions** | Count of positive articles with week-over-week % change |
| **Neutral Mentions** | Count of neutral articles with week-over-week % change |
| **Negative Mentions** | Count of negative articles with week-over-week % change |

---

### 3. Interactive Charts

The dashboard includes multiple chart types for deep analysis. The first section covers volume trends and share-of-voice:

![Line and pie chart](images/visualization_3.png)

| Chart | Description |
|---|---|
| **News Volume & Sentiment Trend** | Daily article count with positive / neutral / negative sentiment overlay as a multi-line chart |
| **Share of Voice by Top Media** | Donut chart showing each source's share of total article volume |
| **Top Entities Share** | Donut chart of the most-mentioned named entities across all articles |

The second section breaks down sentiment across sources, topics, and entities:

![Top Sources, Top Topics, Top Entities bar charts and AI Insight panel](images/visualization_4.png)

| Chart | Description |
|---|---|
| **Top Sources by Sentiment** | Horizontal stacked bar chart of the top 10 news sources, coloured by sentiment |
| **Top Topics by Sentiment** | Horizontal stacked bar showing sentiment distribution per news topic category |
| **Top Entities by Sentiment** | Horizontal stacked bar of the top 10 named entities, coloured by sentiment |

---

### 4. AI-Generated Insight

![AI Insight Summarization](images/visualization_5.png)

An **AI Insight Summarization** panel streams a narrative analysis generated by Gemini directly below the charts. The insight is structured into three sections:
- **Source analysis** — which sources drive positive vs. negative coverage and the key themes per source
- **Entity analysis** — which named entities appear most and in what sentiment context
- **Topic analysis** — which news topics dominate and their overall sentiment patterns

---

### 5. Recent News Content Table

![Recent News content table with filters and Download Excel button](images/visualization_6.png)

A filterable article list at the bottom of the page shows every scraped article for the selected keyword. Users can filter by:
- **Source** — filter to a specific news outlet
- **Topic** — filter by AI-assigned topic category
- **Entity** — filter to articles mentioning a specific named entity
- **Sentiment** — show only positive, neutral, or negative articles

Each row shows the article headline (linked to the original source), publication source, timestamp, topic tag, entity tags, and sentiment label. A **Download Excel** button exports the full filtered dataset.


## How to Use the Dasboard

### Step 1 — Open the application

Navigate to `http://127.0.0.1:5000` (local) in a web browser.

### Step 2 — Select a keyword

Use the **keyword dropdown** at the top of the page to choose the topic you want to monitor. The dashboard will immediately populate with pre-loaded data for that keyword.

### Step 3 — Run a fresh analysis

To scrape and analyse the latest news:

1. Set the **Start Date** and **End Date** for the period you want to monitor.
2. Click **Run Analysis**.
3. A progress indicator will appear while the scraper collects articles and the AI pipeline enriches them. This may take a few minutes depending on the date range and article volume.
4. The dashboard will automatically refresh when processing is complete.

### Step 4 — Explore the charts

Scroll through the dashboard to explore all chart sections. Most charts are interactive — hover over data points for exact values, click legend items to show/hide series, and zoom/pan where supported.

### Step 5 — Read the AI Insight

Scroll to the **AI Insight** section at the bottom. The narrative will stream in automatically, providing a written summary of source, entity, and topic patterns for the selected keyword.

> **Note:** If either parameter is outside the valid range, no prediction will be generated for that row.