# News Article Monitoring

A web application built with Flask that monitors and analyses news articles for any keyword. It scrapes articles from **Google News RSS** on-demand, then uses **Google Gemini AI** to automatically classify each article's sentiment (positive / neutral / negative), extract named entities (NER), and assign a news topic. The resulting dataset is surfaced through an interactive dashboard with multiple chart types and an AI-generated narrative insight summarising coverage patterns.


# Table of Contents

- [For Developers](#for-developer)
  - [Project Structure](#project-structure)
  - [How to Run with Docker (Recommended)](#how-to-run-with-docker-recommended)
  - [How to Run Locally](#how-to-run-the-apps-in-local)
- [For Users](#for-user)
  - [Apps Features](#apps-features)
  - [How to Use the Apps](#how-to-use-the-apps)


# For Developer

## Project Structure

```
.
├── docker-compose.yml              # Orchestrates frontend + backend containers
├── Makefile                        # Shortcuts for common Docker operations
├── readme.md                       # Project documentation
├── .env                            # Environment variables (GEN_AI_API_KEY) — not committed
├── .env.example                    # Template for .env — safe to commit
├── .gitignore                      # Git ignore rules
├── .dockerignore                   # Docker ignore rules
│
├── backend/                        # Flask API + AI processing
│   ├── app.py                      # Main Flask application and API routes
│   ├── requirements.txt            # Python dependencies
│   ├── Dockerfile                  # Multi-stage Docker image for the backend
│   ├── data/
│   │   ├── makan_bergizi_gratis_news.xlsx        # Sample enriched news dataset (Excel)
│   │   └── finished_makan_bergizi_gratis.parquet # Cached enriched dataset (Parquet)
│   ├── images/
│   │   ├── main_visualization.png  # Screenshot: full dashboard overview
│   │   ├── visualization_1.png     # Screenshot: sidebar controls and KPI cards
│   │   ├── visualization_2.png     # Screenshot: KPI cards detail
│   │   ├── visualization_3.png     # Screenshot: sentiment trend and share-of-voice charts
│   │   ├── visualization_4.png     # Screenshot: top sources, topics, and entities bar charts
│   │   ├── visualization_5.png     # Screenshot: AI insight summarization panel
│   │   └── visualization_6.png     # Screenshot: recent news content table
│   └── scripts/
│       ├── google_news_scraper.py  # Google News RSS scraper (day-looping for max results)
│       ├── data_processing.py      # AI pipeline: sentiment, NER, and topic classification
│       └── ai_generate_insight.py  # AI narrative insight generation
│
└── frontend/                       # Nginx static server + reverse proxy
    ├── Dockerfile                  # Nginx Docker image for serving static assets
    ├── nginx.conf                  # Nginx config: serves /static/, proxies all else to backend
    ├── static/
    │   ├── css/
    │   │   └── style.css           # Application stylesheet
    │   └── js/
    │       └── main.js             # Client-side JavaScript for UI interactions
    └── templates/
        └── index.html              # Main Jinja2 HTML template
```

**Key backend files:**

| File | Description |
|---|---|
| `backend/app.py` | Main Flask application. Defines API routes (`/`, `/api/data/<keyword>`, `/api/scrape`, `/api/download/<keyword>`, `/api/ai_insight/<keyword>`), loads and caches the news dataset, computes all chart data server-side, and streams scrape progress via Server-Sent Events |
| `backend/scripts/google_news_scraper.py` | `GoogleNewsScraper` class. Queries Google News RSS day-by-day across a date range to maximise article yield, parses XML responses, and returns a structured DataFrame |
| `backend/scripts/data_processing.py` | `run_processing_pipeline()`. Sends article headlines in batches to Gemini AI and parses JSON responses containing sentiment, NER entities, and topic labels for each article |
| `backend/scripts/ai_generate_insight.py` | `generate_insight()`. Builds structured prompts from the filtered dataset and returns a narrative insight covering source, entity, and topic analysis |

**Key frontend files:**

| File | Description |
|---|---|
| `frontend/templates/index.html` | Main Jinja2 HTML template. Contains the keyword selector, date-range picker, Run Analysis button, summary KPI cards, and all chart containers |
| `frontend/static/css/style.css` | Stylesheet for the entire web UI — layout, card components, chart containers, sidebar, and responsive styles |
| `frontend/static/js/main.js` | Client-side JavaScript. Fetches chart data from `/api/data/<keyword>`, renders all charts, triggers scraping and AI processing, and streams progress via EventSource |
| `frontend/nginx.conf` | Nginx configuration. Serves `/static/` assets directly from disk; proxies all other requests (pages, API calls, SSE streams) to the Flask backend |

**Docker / deployment files:**

| File | Description |
|---|---|
| `backend/Dockerfile` | Multi-stage Python 3.11-slim image. Stage 1 installs dependencies; Stage 2 copies only the final packages and source — no build tools or pip cache in the final image |
| `frontend/Dockerfile` | Nginx stable-alpine image. Copies static assets and the custom Nginx config |
| `docker-compose.yml` | Wires the two services. Backend port 5000 is internal-only; frontend exposes port 80 to the host |
| `Makefile` | Convenience targets for common Docker Compose operations (see below) |


## How to Run with Docker (Recommended)

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) and a [Google AI Studio](https://aistudio.google.com/) API key.

**1. Clone the repository and navigate to the project directory:**

```bash
cd path/to/prod_v1
```

**2. Create your `.env` file from the template:**

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholder with your real Gemini API key:

```
GEN_AI_API_KEY=your_google_ai_studio_api_key_here
```

**3. Build and start both containers using Make:**

```bash
make up
```

**4. Access the application in a browser:**

```
http://localhost
```

### Makefile reference

All Docker operations are wrapped in the `Makefile` at the project root:

| Command | Description |
|---|---|
| `make build` | Build (or rebuild) all Docker images without starting them |
| `make up` | Build images and start all containers in detached mode |
| `make start` | Start already-built containers without rebuilding |
| `make stop` | Stop running containers (keeps containers and images intact) |
| `make down` | Stop and remove containers and the default network |
| `make clean` | Full teardown — removes containers, images, volumes, and orphaned resources |
| `make logs` | Tail live logs from all containers (Ctrl-C to exit) |
| `make help` | Show the full command reference |


## How to Run the Apps in Local

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
pip install -r backend/requirements.txt
```

**5. Create a `.env` file in the project root and add your Gemini API key:**

```
GEN_AI_API_KEY=your_google_ai_studio_api_key_here
```

**6. Run the application:**

```bash
python backend/app.py
```

**7. Access the application in a browser:**

```
http://localhost:5000
```

# For User

## Apps Features

The application consists of five main areas accessible from a single-page dashboard.

<p align="center"><img src="images/main_visualization.png" alt="Main Visualization"></p>

---

### 1. Keyword Selector & Run Analysis

A sidebar on the left provides controls for:

<p align="center"><img src="images/visualization_1.png" alt="Sidebar controls"></p>

- **Keyword** — type or select the topic to monitor (e.g. "Pertamina")
- **Start Date / End Date** — date range for the news scrape
- **Language & Country** — locale settings passed to Google News RSS
- **Run Analysis** button — triggers a live scrape + AI enrichment pipeline and reloads all charts with fresh results

---

### 2. Summary KPI Cards

Four summary cards are displayed at the top of the main panel:

<p align="center"><img src="images/visualization_2.png" alt="Summary KPI Cards"></p>

| Card | Description |
|---|---|
| **Total Mentions** | Total number of articles for the selected keyword, with week-over-week change |
| **Positive Mentions** | Count of positive articles with week-over-week % change |
| **Neutral Mentions** | Count of neutral articles with week-over-week % change |
| **Negative Mentions** | Count of negative articles with week-over-week % change |

---

### 3. Interactive Charts

The dashboard includes multiple chart types for deep analysis. The first section covers volume trends and share-of-voice:

<p align="center"><img src="images/visualization_3.png" alt="Line and pie chart"></p>

| Chart | Description |
|---|---|
| **News Volume & Sentiment Trend** | Daily article count with positive / neutral / negative sentiment overlay as a multi-line chart |
| **Share of Voice by Top Media** | Donut chart showing each source's share of total article volume |
| **Top Entities Share** | Donut chart of the most-mentioned named entities across all articles |

The second section breaks down sentiment across sources, topics, and entities:

<p align="center"><img src="images/visualization_4.png" alt="Top Sources, Top Topics, Top Entities bar charts and AI Insight panel"></p>

| Chart | Description |
|---|---|
| **Top Sources by Sentiment** | Horizontal stacked bar chart of the top 10 news sources, coloured by sentiment |
| **Top Topics by Sentiment** | Horizontal stacked bar showing sentiment distribution per news topic category |
| **Top Entities by Sentiment** | Horizontal stacked bar of the top 10 named entities, coloured by sentiment |

---

### 4. AI-Generated Insight


An **AI Insight Summarization** panel streams a narrative analysis generated by Gemini directly below the charts. The insight is structured into three sections:

<p align="center"><img src="images/visualization_5.png" alt="AI Insight Summarization"></p>

- **Source analysis** — which sources drive positive vs. negative coverage and the key themes per source
- **Entity analysis** — which named entities appear most and in what sentiment context
- **Topic analysis** — which news topics dominate and their overall sentiment patterns

---

### 5. Recent News Content Table

A filterable article list at the bottom of the page shows every scraped article for the selected keyword. Users can filter by:

<p align="center"><img src="images/visualization_6.png" alt="Recent News content table with filters and Download Excel button"></p>

- **Source** — filter to a specific news outlet
- **Topic** — filter by AI-assigned topic category
- **Entity** — filter to articles mentioning a specific named entity
- **Sentiment** — show only positive, neutral, or negative articles

Each row shows the article headline (linked to the original source), publication source, timestamp, topic tag, entity tags, and sentiment label. A **Download Excel** button exports the full filtered dataset.


## How to Use the Dasboard

### Step 1 — Open the application

Navigate to `http://localhost` (Docker) or `http://localhost:5000` (local) in a web browser.

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

### Step 6 — Read the news in detail and download

Scroll to the **Recent News** section at the bottom of the dashboard to browse the full list of scraped articles for the selected keyword.

**Filtering articles:**

Use the filter bar above the table to narrow down results:

| Filter | Description |
|---|---|
| **Filter by Source** | Show only articles from a specific news outlet |
| **Filter by Topic** | Show only articles under a specific AI-assigned topic |
| **Filter by Entity** | Show only articles that mention a specific named entity |
| **Filter by Sentiment** | Show only positive, neutral, or negative articles |

Filters can be combined — for example, show only *negative* articles from *HarianBasis* about *ekonomi dan keuangan*.

**Reading an article:**

Click any article headline in the table to open the original article in a new browser tab.

**Downloading the dataset:**

Click the **Download Excel** button (top-right of the table) to export all currently-displayed articles — respecting any active filters — as a `.xlsx` file. The file includes the headline, source, publication date, topic, entities, sentiment, and article URL for each row.