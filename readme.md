# News Article Monitoring

A web application built with Flask that monitors and analyses news articles for any keyword. It scrapes articles from **Google News RSS** on-demand, then uses **Google Gemini AI** to automatically classify each article's sentiment (positive / neutral / negative), extract named entities (NER), and assign a news topic. The resulting dataset is surfaced through an interactive dashboard with 10+ chart types — including time-series trends, sentiment heatmaps, source bubble charts, Sankey diagrams, and radar charts — and an AI-generated narrative insight summarising coverage patterns.


# Table of Contents

- [For Developers](#for-developer)
  - [Project Structure](#project-structure)
  - [How to Run Locally](#how-to-run-the-apps-in-local)
  - [How to Deploy to Cloud Run](#how-to-deploy-the-apps-to-cloud-run)
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

## How to deploy the apps to Cloud Run

**Prerequisites:** Docker Desktop and the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated.

**1. Build the Docker image:**

```bash
docker build -t news-monitoring:latest .
```

**2. Tag the image for Artifact Registry:**

```bash
docker tag news-monitoring:latest \
  <region>-docker.pkg.dev/<your-gcp-project>/<your-repo>/news-monitoring:latest
```

**3. Push the image:**

```bash
docker push <region>-docker.pkg.dev/<your-gcp-project>/<your-repo>/news-monitoring:latest
```

**4. Deploy to Cloud Run:**

```bash
gcloud run deploy news-monitoring \
  --image <region>-docker.pkg.dev/<your-gcp-project>/<your-repo>/news-monitoring:latest \
  --region <region> \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GEN_AI_API_KEY=<your_api_key>
```

> **Note:** Replace `<region>`, `<your-gcp-project>`, `<your-repo>`, and `<your_api_key>` with your own values. Never commit secrets — use Cloud Run's Secret Manager integration for production deployments.


# For User

## Apps Features

The application consists of three main areas accessible from a single-page dashboard.

### 1. Keyword Selector & Run Analysis

A dropdown at the top of the page lists all monitored keywords. Selecting a keyword instantly refreshes all charts with pre-loaded data for that keyword. The **Run Analysis** button triggers a live scrape of Google News for the selected keyword across a specified date range, runs the AI enrichment pipeline (sentiment, NER, topics), and reloads the dashboard with fresh results.

### 2. Summary KPI Cards

Four summary cards are shown at the top of the dashboard:

| Card | Description |
|---|---|
| **Total News** | Total number of articles for the selected keyword, with week-over-week change |
| **Positive** | Count and percentage of positive articles, with week-over-week change |
| **Neutral** | Count and percentage of neutral articles, with week-over-week change |
| **Negative** | Count and percentage of negative articles, with week-over-week change |

### 3. Interactive Charts

The dashboard includes 10+ chart types for deep analysis:

| Chart | Description |
|---|---|
| **News Volume Over Time** | Daily article count as a line chart |
| **Sentiment Over Time** | Daily breakdown of positive / neutral / negative articles |
| **Top Sources by Sentiment** | Horizontal stacked bar chart of the top 10 news sources |
| **Top Topics by Sentiment** | Horizontal stacked bar showing sentiment per news topic category |
| **Top Entities (NER)** | Top 10 named entities mentioned, coloured by sentiment |
| **Source Bubble Chart** | Scatter plot of volume vs. negativity rate per source |
| **Activity Heatmap** | Publication frequency by day-of-week and hour-of-day |
| **Topic × Entity Heatmap** | Cross-tabulation of dominant sentiment per topic-entity pair |
| **Topic Radar** | Radar chart of sentiment distribution across top 8 topics |
| **Source Radar** | Radar chart of sentiment distribution across top 10 sources |
| **Topic Share Over Time** | Stacked area chart of the top 5 topics per day |
| **Entity Mention Trend** | Line chart of the top 5 entity mentions over time |
| **Source Trend** | Line chart of the top 5 news sources over time |
| **Sentiment → Topic Sankey** | Flow diagram from sentiment labels to topic categories |

### 4. AI-Generated Insight

Below the charts, an **AI Insight** panel streams a narrative analysis generated by Gemini, covering:
- Source analysis — which sources drive positive vs. negative coverage and why
- Entity analysis — which named entities appear most and in what context
- Topic analysis — which news topics dominate and their sentiment patterns


## How to Use the Apps

### Step 1 — Open the application

Navigate to `http://127.0.0.1:5000` (local) in a web browser.

### Step 2 — Select a keyword

Use the **keyword dropdown** at the top of the page to choose the topic you want to monitor. The dashboard will immediately populate with pre-loaded data for that keyword.

### Step 3 — (Optional) Run a fresh analysis

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