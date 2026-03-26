# News Article Monitoring

A web app that monitors news articles for any keyword. It scrapes **Google News RSS**, uses **Google Gemini AI** to classify sentiment, extract named entities, and assign topics — then displays everything in an interactive dashboard with charts and an AI-generated narrative summary.

![Python Version](https://img.shields.io/badge/python-3.11-blue)
![Docker](https://img.shields.io/badge/docker-supported-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)

# Table of content

- [For Users](#for-users)
  - [Application Demo](#application-demo)
  - [Apps Features](#apps-features)
  - [How to Use the Dashboard](#how-to-use-the-dashboard)
- [For Developers](#for-developers)
  - [Project Structure](#project-structure)
  - [Getting Started](#getting-started)
  - [Code Explanation](#code-explanation)
  - [Run the project with Docker (Local)](#run-the-project-with-docker-local)
  - [Deploy to Google Cloud Run](#deploy-to-google-cloud-run)
  - [Contributors](#contributors)
  - [License](#license)


# For Users 

## Application Demo

The deployed application is in this link:
[https://news-monitoring-prod-v1-118493320623.asia-southeast2.run.app/ *(update with the live Cloud Run URL)*](https://news-monitoring-prod-v1-118493320623.asia-southeast2.run.app/)


## Apps Features

The application consists of six main areas accessible from a single-page dashboard.

<p align="center"><img src="images/main_visualization.png" alt="Main Visualization"></p>

---

### 1. Login / Logout

A login button is displayed in the top-right corner of the dashboard. The dashboard is publicly viewable by anyone, but certain actions — specifically **Run Analysis** — require authentication.

- Click **Login** to open a sign-in popup. Enter your username and password and click **Login**.
- On success, the navbar updates to show your username and a **Log out** button.
- Clicking **Log out** returns the navbar to the anonymous state.
- Refreshing the page always resets to the anonymous (logged-out) state — login state is not persisted across page loads.

> **Default credentials** (for local / demo use):
> - Username: `player_zero`
> - Password: (ask the developer)

---

### 2. Keyword Selector & Run Analysis

A sidebar on the left provides controls for:

<p align="center"><img src="images/visualization_1.png" alt="Sidebar controls"></p>

- **Keyword** — type the topic you want to scrape (e.g. "Pertamina")
- **Start Date / End Date** — date range for the news scrape
- **Language & Country** — locale settings passed to Google News RSS
- **Run Analysis** button — triggers a live scrape + AI enrichment pipeline and reloads all charts with fresh results

> **Note:** The **Run Analysis** button is login-gated. If you are not logged in, clicking the button will show a prompt asking you to sign in first. Once logged in, the button works normally.

Refreshing the page always resets the dashboard to the default pre-loaded dataset, discarding any in-memory data from a previous Run Analysis session.

---

### 3. Choose Keyword (Pre-loaded Data)

At the bottom of the sidebar is a **Choose Keyword** dropdown. 

<p align="center"><img src="images/visualization_keyword.png" alt="Keyword Visualization"></p>

This lets you switch between keywords that are already present in the pre-loaded dataset files stored on the server — without needing to run a new scrape.

- Selecting a keyword from the dropdown immediately reloads all charts and the news table with data for that keyword.
- This is useful for quickly comparing multiple keywords that have already been scraped and processed.
- The dropdown is always available regardless of login status.

---

### 4. Summary KPI Cards

Four summary cards are displayed at the top of the main panel:

<p align="center"><img src="images/visualization_2.png" alt="Summary KPI Cards"></p>

| Card | Description |
|---|---|
| **Total Mentions** | Total number of articles for the selected keyword, with week-over-week change |
| **Positive Mentions** | Count of positive articles with week-over-week % change |
| **Neutral Mentions** | Count of neutral articles with week-over-week % change |
| **Negative Mentions** | Count of negative articles with week-over-week % change |

---

### 5. Interactive Charts

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

### 6. AI-Generated Insight


An **AI Insight Summarization** panel streams a narrative analysis generated by Gemini directly below the charts. The insight is structured into three sections:

<p align="center"><img src="images/visualization_5.png" alt="AI Insight Summarization"></p>

- **Source analysis** — which sources drive positive vs. negative coverage and the key themes per source
- **Entity analysis** — which named entities appear most and in what sentiment context
- **Topic analysis** — which news topics dominate and their overall sentiment patterns

---

### 7. Recent News Content Table

A filterable article list at the bottom of the page shows every scraped article for the selected keyword. Users can filter by:

<p align="center"><img src="images/visualization_6.png" alt="Recent News content table with filters and Download Excel button"></p>

- **Source** — filter to a specific news outlet
- **Topic** — filter by AI-assigned topic category
- **Entity** — filter to articles mentioning a specific named entity
- **Sentiment** — show only positive, neutral, or negative articles

Each row shows the article headline (linked to the original source), publication source, timestamp, topic tag, entity tags, and sentiment label. A **Download Excel** button exports the full filtered dataset.

The exported `.xlsx` file contains two sheets:

| Sheet | Contents |
|---|---|
| **News Data** | All article rows with headline, source, date, topic, entities, sentiment, and URL |
| **AI Insight** | The full AI-generated narrative summary for the selected keyword |


## How to Use the Dashboard

### Step 1 — Open the application

Navigate to `http://localhost` (Docker) or `http://localhost:5000` (local) in a web browser.

### Step 2 — Log in

Click the **Login** button in the top-right corner of the dashboard. Enter your credentials in the popup and click **Login**.

> Logging in is required to use the **Run Analysis** feature. Browsing pre-loaded data and charts is available to all users without login.

### Step 3 — Select a keyword from pre-loaded data

Use the **Choose Keyword** dropdown at the bottom of the sidebar to switch between keywords that are already stored on the server. The dashboard will immediately populate with data for the selected keyword.

### Step 4 — Run a fresh analysis

To scrape and analyse the latest news for a new keyword:

1. Make sure you are **logged in** (see Step 2).
2. Enter a keyword in the **Keyword** field in the sidebar.
3. Set the **Start Date** and **End Date** for the period you want to monitor.
4. Select the **Language** and **Country** if needed.
5. Click **Run Analysis**.
6. A progress indicator will appear while the scraper collects articles and the AI pipeline enriches them. This may take a few minutes depending on the date range and article volume.
7. The dashboard will automatically refresh when processing is complete.

> Refreshing the browser page after a Run Analysis will discard the in-session data and return the dashboard to the default pre-loaded keyword.

### Step 5 — Explore the charts

Scroll through the dashboard to explore all chart sections. Most charts are interactive — hover over data points for exact values, click legend items to show/hide series, and zoom/pan where supported.

### Step 6 — Read the AI Insight

Scroll to the **AI Insight** section. The narrative will stream in automatically, providing a written summary of source, entity, and topic patterns for the selected keyword.

### Step 7 — Read the news in detail and download

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


# For Developers

## Project Structure
```
.
├── docker-compose.yml          # Runs frontend + backend containers locally
├── cloud-run-deploy.yaml       # Cloud Run multi-container deployment manifest
├── Makefile                    # Shortcuts for Docker operations
├── readme.md
├── .env                        # Your API keys — not committed to git
├── .gitignore
├── .dockerignore
│
├── backend/
│   ├── app.py                  # Flask app and API routes
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── data/                   # Cached datasets (Excel / Parquet)
│   └── scripts/
│       ├── google_news_scraper.py   # Scrapes Google News RSS by date range
│       ├── data_processing.py       # AI pipeline: sentiment, NER, topic
│       └── ai_generate_insight.py   # AI narrative summary generation
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf              # Serves /static/, proxies everything else to Flask
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/main.js
│   └── templates/
│       └── index.html
│
└── images/                     # Dashboard screenshots for readme
```

## Getting started

### Dependencies and Prerequisites

| Dependency | Version | Purpose |
|---|---|---|
| Python | 3.11 | Runtime language |
| Flask | 3.0.0 | Web framework and REST API server |
| Pandas | 2.2.3 | Data loading, filtering, and aggregation |
| NumPy | 1.26.4 | Numerical operations |
| PyArrow | 23.0.1 | Parquet file read/write support |
| OpenPyXL | 3.1.2 | Excel (.xlsx) file read/write |
| google-generativeai | 0.8.3 | Google Gemini AI SDK for sentiment, NER, topic, and insight generation |
| Requests | 2.31.0 | HTTP requests for Google News RSS scraping |
| BeautifulSoup4 | 4.12.3 | XML/HTML parsing of RSS feed responses |
| python-dotenv | 0.21.0 | Loading environment variables from `.env` |
| Docker Desktop | Latest | Building and running containers locally |
| Google Cloud CLI | Latest | Pushing images and deploying to Cloud Run |

### Tech stack

| Layer | Tech stack |
|---|---|
| AI / LLM | Google Gemini (`gemini-2.5-flash-lite`) via `google-generativeai` |
| News Scraping | Google News RSS + Requests + BeautifulSoup4 |
| Data Processing | Pandas, NumPy, PyArrow |
| Frontend | HTML5, CSS3, Vanilla JavaScript, Plotly.js |
| Reverse Proxy | Nginx |
| Containerization | Docker, Docker Compose |
| Cloud Platform | Google Cloud Run (multi-container) |
| Container Registry | Google Artifact Registry |

### Credentials setup

This project requires API keys and environment variables. Follow these steps:

1. Copy the example environment file:
```bash
   cp .env.example .env
```

2. Open `.env` and fill in your actual values:
```bash
   nano .env  # or use any text editor
```

3. Below is the full list of required variables:

| Variable | Description | Required |
|---|---|---|
| `GEN_AI_API_KEY` | Your API key from [Google AI Studio](https://aistudio.google.com/) for Gemini AI | ✅ Yes |

> ⚠️ **Never commit your `.env` file.** Make sure `.env` is listed in your `.gitignore`.

**Example `.env.example` file:**
```env
# .env.example — copy this to .env and fill in your values
GEN_AI_API_KEY=your_google_ai_studio_api_key_here
```


## Code explanation

### Key Backend files

| Category | File | Description |
|---|---|---|
| API Server | `app.py` | Flask application with all REST API endpoints; handles session-based authentication, data loading (Excel/Parquet), chart data aggregation, SSE-streamed AI insight, and Excel export |
| News Scraper | `scripts/google_news_scraper.py` | Scrapes Google News RSS feed with a day-by-day loop to maximise article yield; returns a DataFrame of headlines, sources, URLs, and timestamps |
| AI Pipeline | `scripts/data_processing.py` | Sends article headlines to Gemini in concurrent batches; enriches each article with sentiment (positive / neutral / negative), named entities (NER), and a topic category |
| AI Insight | `scripts/ai_generate_insight.py` | Builds structured prompts from aggregated source, entity, and topic data using real article samples, then streams a narrative Gemini-generated analysis panel |

### Key Frontend files

| Category | File | Description |
|---|---|---|
| HTML Template | `templates/index.html` | Main single-page dashboard; defines the sidebar controls, KPI cards, Plotly chart containers, streaming AI insight panel, and filterable news table |
| HTML Template | `templates/login.html` | Login page with username and password form used for session-based authentication |
| JavaScript | `static/js/main.js` | All client-side logic: fetches API endpoints, renders Plotly charts, manages table filters, handles login/logout flow, streams the AI insight via SSE, and triggers Excel download |
| CSS | `static/css/style.css` | Dashboard layout, component styling, responsive design, and colour themes for sentiment labels and chart elements |
| Reverse Proxy | `nginx.conf` | Serves `/static/` files directly from disk; proxies all other requests (API calls, template rendering) to the Flask backend |


## Run the project with Docker (Local)

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) and a [Google AI Studio](https://aistudio.google.com/) API key.

**1. Navigate to the project directory:**

```bash
cd path/to/AI-Enhanced-News-Dashboard-repo
```

**2. Create a `.env` file and add your Gemini API key:**

```
GEN_AI_API_KEY=your_google_ai_studio_api_key_here
```

**3. Make sure `nginx.conf` is set for local Docker use.**

In `frontend/nginx.conf`, the active `proxy_pass` line should be:

```nginx
proxy_pass http://backend:5000;   # for Docker Compose (local)
# proxy_pass http://localhost:5000;  # for Cloud Run
```

**4. Build and start:**

```bash
make up
```

**5. Open in browser:** `http://localhost`

### Makefile reference

| Command | Description |
|---|---|
| `make build` | Build (or rebuild) images |
| `make up` | Build and start all containers |
| `make start` | Start already-built containers |
| `make stop` | Stop containers |
| `make down` | Stop and remove containers |
| `make clean` | Full teardown (containers, images, volumes) |
| `make logs` | Tail live logs |


## Deploy to Google Cloud Run

**Prerequisites:**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) authenticated
- Access to GCP project `zikrys-project`

---

### One-Time Setup

**1. Authenticate Docker with Artifact Registry:**

```bash
gcloud auth configure-docker asia-southeast2-docker.pkg.dev
```

**2. Allow public access (run once after first deploy):**

```powershell
gcloud run services add-iam-policy-binding news-monitoring-prod-v1 `
  --region asia-southeast2 `
  --member="allUsers" `
  --role="roles/run.invoker"
```

---

### Deploy / Redeploy Steps

**Step 1 — Set the API key as a Cloud Run environment variable**

In the Cloud Run console, go to your service → **Edit & Deploy New Revision** → **Variables & Secrets** tab, and add:

```
GEN_AI_API_KEY = your_google_ai_studio_api_key_here
```

Or via CLI:

```powershell
gcloud run services update news-monitoring-prod-v1 `
  --region asia-southeast2 `
  --update-env-vars GEN_AI_API_KEY="YOUR_ACTUAL_API_KEY"
```

> This only needs to be done once, or whenever you rotate the key.

**Step 2 — Switch `nginx.conf` to Cloud Run mode**

In `frontend/nginx.conf`, make sure it looks like this:

```nginx
proxy_pass http://localhost:5000;    # for Cloud Run
# proxy_pass http://backend:5000;   # for Docker Compose (local)
```

**Step 3 — Build images**

```powershell
docker build -f backend/Dockerfile  -t asia-southeast2-docker.pkg.dev/zikrys-project/news-monitoring-repo/news-monitoring-prod_v1-backend:latest  .
docker build -f frontend/Dockerfile -t asia-southeast2-docker.pkg.dev/zikrys-project/news-monitoring-repo/news-monitoring-prod_v1-frontend:latest .
```

**Step 4 — Push to Artifact Registry**

```powershell
docker push asia-southeast2-docker.pkg.dev/zikrys-project/news-monitoring-repo/news-monitoring-prod_v1-backend:latest
docker push asia-southeast2-docker.pkg.dev/zikrys-project/news-monitoring-repo/news-monitoring-prod_v1-frontend:latest
```

**Step 5 — Deploy**

```powershell
gcloud run services replace cloud-run-deploy.yaml --region asia-southeast2
```

**Step 6 — Get the live URL**

```powershell
gcloud run services describe news-monitoring-prod-v1 --region asia-southeast2 --format="value(status.url)"
```

---

## Contributors
Contributors names and contact info:
1. **[Zikry Adjie Nugraha](https://github.com/nugrahazikry)**: Sole developer — designed and built the full application including the Google News RSS scraper, Gemini AI enrichment pipeline, Flask REST API, interactive Plotly dashboard, Docker multi-container setup, and Google Cloud Run deployment.


## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
