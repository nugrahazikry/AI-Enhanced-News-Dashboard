from flask import Flask, render_template, jsonify, request, Response, stream_with_context, send_file
import json
import io
import threading
import queue as _queue
import tempfile
from datetime import timedelta
import pandas as pd
import numpy as np
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from ai_generate_insight import generate_insight
from data_processing import run_processing_pipeline

app = Flask(__name__)

genai.configure(api_key=os.getenv('GEN_AI_API_KEY'))
_model_generative = genai.GenerativeModel(model_name='gemini-2.5-flash-lite')

# Data source — defaults to the enriched file; switches to scraped file after Run Analysis
_DEFAULT_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'makan_bergizi_gratis_news.xlsx')
_active_data_path = _DEFAULT_DATA_FILE
_active_language = 'id'

def load_data():
    path = _active_data_path
    # Prefer parquet if a same-stem .parquet file exists alongside the xlsx
    parquet_path = os.path.splitext(path)[0] + '.parquet'
    if os.path.exists(parquet_path):
        df = pd.read_parquet(parquet_path)
    elif path.lower().endswith(('.xlsx', '.xls')):
        df = pd.read_excel(path)
    else:
        df = pd.read_parquet(path)

    # Normalise date column → always 'datetime'
    for candidate in ('datetime', 'last_update', 'date', 'published_date', 'publish_date', 'published_at', 'created_at'):
        if candidate in df.columns:
            df = df.rename(columns={candidate: 'datetime'})
            break

    # Fallback — try any column whose name contains 'date' or 'time'
    if 'datetime' not in df.columns:
        for col in df.columns:
            if any(kw in col.lower() for kw in ('date', 'time', 'update')):
                df = df.rename(columns={col: 'datetime'})
                break

    # Guarantee the column always exists to avoid downstream KeyErrors
    if 'datetime' not in df.columns:
        df['datetime'] = pd.NaT

    # Normalise topic column → always 'topik_berita'
    if 'topik' in df.columns and 'topik_berita' not in df.columns:
        df = df.rename(columns={'topik': 'topik_berita'})

    # Normalise sentiment → always English labels
    _sent_norm = {'positif': 'positive', 'negatif': 'negative', 'netral': 'neutral',
                  'positiv': 'positive', 'negativ': 'negative', 'nettral': 'neutral'}
    if 'sentimen' in df.columns:
        df['sentimen'] = df['sentimen'].map(
            lambda x: _sent_norm.get(str(x).lower().strip(), str(x).lower().strip()) if pd.notna(x) else x
        )

    # Add missing columns with safe defaults
    if 'sentimen' not in df.columns:
        df['sentimen'] = 'neutral'
    if 'topik_berita' not in df.columns:
        df['topik_berita'] = 'Tidak Dikategorikan'
    if 'normalized_source_news' not in df.columns:
        df['normalized_source_news'] = df['source_news'] if 'source_news' in df.columns else ''
    if 'source_news_url' not in df.columns:
        df['source_news_url'] = ''
    if 'NER' not in df.columns:
        df['NER'] = [[] for _ in range(len(df))]
    if 'NER_normalized' not in df.columns:
        df['NER_normalized'] = [[] for _ in range(len(df))]

    # Parse/flatten NER columns — handles lists (parquet), comma-separated strings (Excel), and NaN
    def _parse_ner(x):
        if isinstance(x, (list, np.ndarray)):
            return [e for e in x if pd.notna(e) and str(e).strip()]
        if isinstance(x, str) and x.strip():
            return [e.strip() for e in x.split(',') if e.strip()]
        return []

    for col in ('NER', 'NER_normalized'):
        if col in df.columns:
            df[col] = df[col].apply(_parse_ner)

    return df

# Cache the data
_cached_data = None

def get_data():
    global _cached_data
    if _cached_data is None:
        _cached_data = load_data()
    return _cached_data

@app.route('/')
def index():
    data = get_data()
    keywords = sorted(data['keyword'].dropna().unique().tolist())
    # Default to 'Pertamina' if available, else first keyword
    default_keyword = 'Pertamina' if 'Pertamina' in keywords else keywords[0] if keywords else ''
    return render_template('index.html', keywords=keywords, default_keyword=default_keyword)

@app.route('/api/data/<keyword>')
def get_keyword_data(keyword):
    data = get_data()
    
    # Filter by keyword
    subset_df = data[data['keyword'] == keyword]
    hashable_cols = [c for c in subset_df.columns if not subset_df[c].apply(lambda x: isinstance(x, (list, dict, np.ndarray))).any()]
    filtered_df = subset_df.drop_duplicates(subset=hashable_cols).reset_index(drop=True)

    if "datetime" not in filtered_df.columns and "last_update" in filtered_df.columns:
        filtered_df = filtered_df.rename(columns={"last_update": "datetime"})
    filtered_df["datetime"] = pd.to_datetime(filtered_df["datetime"], errors='coerce')
    filtered_df = filtered_df.sort_values("datetime")
    filtered_df["count"] = 1

    # Use ONLY normalized columns — never fall back to raw source/NER
    if 'normalized_source_news' in filtered_df.columns:
        filtered_df['source_news'] = filtered_df['normalized_source_news'].fillna('')

    # Build entitas from NER_normalized only (no raw NER fallback)
    def _pick_ner(row):
        val = row.get('NER_normalized') if 'NER_normalized' in row.index else None
        if isinstance(val, list):
            return ', '.join(str(e) for e in val if e)
        return ''

    if 'NER_normalized' in filtered_df.columns:
        filtered_df['entitas'] = filtered_df.apply(_pick_ner, axis=1)
    
    # 1. News count over time
    news_over_time = filtered_df.groupby(filtered_df["datetime"].dt.strftime('%Y-%m-%d')).size().reset_index(name='count')
    news_over_time.columns = ['date', 'count']
    
    # 2. News count by sentiment over time
    sentiment_over_time = filtered_df.groupby([filtered_df["datetime"].dt.strftime('%Y-%m-%d'), "sentimen"]).size().reset_index(name='count')
    sentiment_over_time.columns = ['date', 'sentiment', 'count']
    
    # Pivot for frontend
    sentiment_time_pivot = sentiment_over_time.pivot(index='date', columns='sentiment', values='count').fillna(0).reset_index()
    sentiment_time_data = sentiment_time_pivot.to_dict('records')
    
    # 3. Top 10 sources by sentiment
    sentiment_counts = filtered_df.groupby(["source_news", "sentimen"]).size().reset_index(name="count")
    top_sources = sentiment_counts.groupby("source_news")["count"].sum().nlargest(10).index.tolist()
    filtered_sources = sentiment_counts[sentiment_counts["source_news"].isin(top_sources)]
    sources_pivot = filtered_sources.pivot(index='source_news', columns='sentimen', values='count').fillna(0).reset_index()
    sources_data = sources_pivot.to_dict('records')
    
    # Sort by total count descending (highest at top of horizontal bar chart)
    for item in sources_data:
        item['total'] = sum([item.get('positive', 0), item.get('neutral', 0), item.get('negative', 0)])
    sources_data = sorted(sources_data, key=lambda x: x['total'], reverse=True)
    
    # 4. Top news topics by sentiment
    if 'topik_berita' in filtered_df.columns:
        topik_counts = filtered_df.groupby(["topik_berita", "sentimen"]).size().reset_index(name="count")
        top_topik = topik_counts.groupby("topik_berita")["count"].sum().nlargest(10).index.tolist()
        filtered_topik = topik_counts[topik_counts["topik_berita"].isin(top_topik)]
        topik_pivot = filtered_topik.pivot(index='topik_berita', columns='sentimen', values='count').fillna(0).reset_index()
        topik_data = topik_pivot.to_dict('records')
        for item in topik_data:
            item['total'] = sum([item.get('positive', 0), item.get('neutral', 0), item.get('negative', 0)])
        topik_data = sorted(topik_data, key=lambda x: x['total'], reverse=True)
    else:
        topik_data = []
    
    # 5. Top entities by sentiment
    if 'entitas' in filtered_df.columns:
        entitas_df = filtered_df[['entitas', 'sentimen']].copy()
        entitas_df["entitas"] = entitas_df["entitas"].str.lower().str.split(", ")
        entitas_df = entitas_df.explode("entitas").reset_index(drop=True)
        entitas_df = entitas_df[~entitas_df['entitas'].isin(['tidak ada', keyword.lower(), ''])]
        entitas_df = entitas_df.dropna(subset=['entitas'])
        entitas_counts = entitas_df.groupby(["entitas", "sentimen"]).size().reset_index(name="count")
        top_entitas = entitas_counts.groupby("entitas")["count"].sum().nlargest(10).index.tolist()
        filtered_entitas = entitas_counts[entitas_counts["entitas"].isin(top_entitas)]
        entitas_pivot = filtered_entitas.pivot(index='entitas', columns='sentimen', values='count').fillna(0).reset_index()
        entitas_data = entitas_pivot.to_dict('records')
        for item in entitas_data:
            item['total'] = sum([item.get('positive', 0), item.get('neutral', 0), item.get('negative', 0)])
        entitas_data = sorted(entitas_data, key=lambda x: x['total'], reverse=True)
    else:
        entitas_data = []
    
    # 6. Topic share over time (top 5 topics)
    if 'topik_berita' in filtered_df.columns:
        topic_time_df = filtered_df.groupby([filtered_df["datetime"].dt.strftime('%Y-%m-%d'), "topik_berita"]).size().reset_index(name='count')
        topic_time_df.columns = ['date', 'topic', 'count']
        top5_topics = filtered_df['topik_berita'].value_counts().nlargest(5).index.tolist()
        topic_time_df = topic_time_df[topic_time_df['topic'].isin(top5_topics)]
        topic_share_pivot = topic_time_df.pivot(index='date', columns='topic', values='count').fillna(0).reset_index()
        topic_share_data = topic_share_pivot.to_dict('records')
    else:
        topic_share_data = []
        top5_topics = []

    # 7. Entity mention trend over time (top 5 entities)
    if 'entitas' in filtered_df.columns:
        ent_trend_df = filtered_df[['datetime', 'entitas']].copy()
        ent_trend_df['date'] = ent_trend_df['datetime'].dt.strftime('%Y-%m-%d')
        ent_trend_df['entitas'] = ent_trend_df['entitas'].str.lower().str.split(', ')
        ent_trend_df = ent_trend_df.explode('entitas').reset_index(drop=True)
        ent_trend_df = ent_trend_df[~ent_trend_df['entitas'].isin(['tidak ada', keyword.lower(), ''])]
        ent_trend_df = ent_trend_df.dropna(subset=['entitas'])
        top5_entities = ent_trend_df['entitas'].value_counts().nlargest(5).index.tolist()
        ent_trend_df = ent_trend_df[ent_trend_df['entitas'].isin(top5_entities)]
        ent_trend_counts = ent_trend_df.groupby(['date', 'entitas']).size().reset_index(name='count')
        ent_trend_pivot = ent_trend_counts.pivot(index='date', columns='entitas', values='count').fillna(0).reset_index()
        entity_trend_data = ent_trend_pivot.to_dict('records')
    else:
        entity_trend_data = []
        top5_entities = []

    # 8. Source bubble: volume vs negativity rate
    filtered_df["source_news_clean"] = filtered_df["source_news"]
    source_agg = filtered_df.groupby("source_news_clean").agg(
        total=('sentimen', 'count'),
        negative=('sentimen', lambda x: (x == 'negative').sum())
    ).reset_index()
    source_agg['neg_pct'] = (source_agg['negative'] / source_agg['total'] * 100).round(1)
    source_bubble_data = source_agg.rename(columns={'source_news_clean': 'source'}).to_dict('records')

    # 9. Activity heatmap: weekday x hour
    hm_df = filtered_df.copy()
    hm_df['weekday'] = hm_df['datetime'].dt.weekday  # 0=Mon, 6=Sun
    hm_df['hour'] = hm_df['datetime'].dt.hour
    hm_counts = hm_df.groupby(['weekday', 'hour']).size().reset_index(name='count')
    heatmap_data = hm_counts.to_dict('records')

    # 10. Sentiment × Topic × Entity Heatmap
    if 'topik_berita' in filtered_df.columns and 'entitas' in filtered_df.columns:
        hm_te_df = filtered_df[['topik_berita', 'entitas', 'sentimen']].copy()
        hm_te_df = hm_te_df.dropna(subset=['topik_berita', 'entitas'])
        hm_te_df['entitas'] = hm_te_df['entitas'].str.lower().str.split(', ')
        hm_te_df = hm_te_df.explode('entitas').reset_index(drop=True)
        hm_te_df = hm_te_df[~hm_te_df['entitas'].isin(['tidak ada', keyword.lower(), ''])]
        top8_topics_hm = filtered_df['topik_berita'].value_counts().nlargest(8).index.tolist()
        top8_entities_hm = hm_te_df['entitas'].value_counts().nlargest(8).index.tolist()
        hm_te_df = hm_te_df[
            hm_te_df['topik_berita'].isin(top8_topics_hm) &
            hm_te_df['entitas'].isin(top8_entities_hm)
        ]
        hm_te_counts = hm_te_df.groupby(['topik_berita', 'entitas', 'sentimen']).size().reset_index(name='count')
        heatmap_cells = []
        for topic in top8_topics_hm:
            for entity in top8_entities_hm:
                sub = hm_te_counts[
                    (hm_te_counts['topik_berita'] == topic) &
                    (hm_te_counts['entitas'] == entity)
                ]
                pos = int(sub[sub['sentimen'] == 'positive']['count'].sum())
                neu = int(sub[sub['sentimen'] == 'neutral']['count'].sum())
                neg = int(sub[sub['sentimen'] == 'negative']['count'].sum())
                total = pos + neu + neg
                dominant = 'positive' if pos >= neu and pos >= neg else ('negative' if neg >= neu else 'neutral') if total > 0 else 'none'
                heatmap_cells.append({'topic': topic, 'entity': entity, 'positive': pos, 'neutral': neu, 'negative': neg, 'total': total, 'dominant': dominant})
        topic_entity_heatmap = {'data': heatmap_cells, 'topics': top8_topics_hm, 'entities': top8_entities_hm}
    else:
        topic_entity_heatmap = {'data': [], 'topics': [], 'entities': []}

    # 11. Radar: sentiment distribution across top 8 topics
    if 'topik_berita' in filtered_df.columns:
        top8_r = filtered_df['topik_berita'].value_counts().nlargest(8).index.tolist()
        r_df = filtered_df[filtered_df['topik_berita'].isin(top8_r)]
        r_counts = r_df.groupby(['topik_berita', 'sentimen']).size().unstack(fill_value=0)
        def _get(col):
            return [int(r_counts.loc[t, col]) if t in r_counts.index and col in r_counts.columns else 0 for t in top8_r]
        radar_payload = {'labels': top8_r, 'positive': _get('positive'), 'neutral': _get('neutral'), 'negative': _get('negative')}
    else:
        radar_payload = {'labels': [], 'positive': [], 'neutral': [], 'negative': []}

    # 13. Source trend over time (top 5 sources)
    top5_src = filtered_df['source_news'].value_counts().nlargest(5).index.tolist()
    src_trend_counts = filtered_df.groupby([filtered_df['datetime'].dt.strftime('%Y-%m-%d'), 'source_news']).size().reset_index(name='count')
    src_trend_counts.columns = ['date', 'source', 'count']
    src_trend_filtered = src_trend_counts[src_trend_counts['source'].isin(top5_src)]
    src_trend_pivot = src_trend_filtered.pivot(index='date', columns='source', values='count').fillna(0).reset_index()
    source_trend_data = src_trend_pivot.to_dict('records')

    # 14. Radar: sentiment distribution across top 10 sources
    top10_src_r = filtered_df['source_news'].value_counts().nlargest(10).index.tolist()
    r_src_df = filtered_df[filtered_df['source_news'].isin(top10_src_r)]
    r_src_counts = r_src_df.groupby(['source_news', 'sentimen']).size().unstack(fill_value=0)
    def _get_src(col):
        return [int(r_src_counts.loc[s, col]) if s in r_src_counts.index and col in r_src_counts.columns else 0 for s in top10_src_r]
    radar_sources_payload = {
        'labels': top10_src_r,
        'positive': _get_src('positive'),
        'neutral':  _get_src('neutral'),
        'negative': _get_src('negative')
    }

    # 12. Sankey: Sentiment → Topic
    if 'topik_berita' in filtered_df.columns:
        top10_sk = filtered_df['topik_berita'].value_counts().nlargest(10).index.tolist()
        sk_df = filtered_df[filtered_df['topik_berita'].isin(top10_sk)]\
            .groupby(['sentimen', 'topik_berita']).size().reset_index(name='flow')
        sankey_data = [{'from': r['sentimen'], 'to': r['topik_berita'], 'flow': int(r['flow'])} for _, r in sk_df.iterrows()]
    else:
        sankey_data = []

    # Calculate summary stats
    total_news = len(filtered_df)
    positive_count = len(filtered_df[filtered_df['sentimen'] == 'positive'])
    neutral_count = len(filtered_df[filtered_df['sentimen'] == 'neutral'])
    negative_count = len(filtered_df[filtered_df['sentimen'] == 'negative'])

    # Week-over-week comparison
    max_date = filtered_df['datetime'].max()
    min_date = filtered_df['datetime'].min()
    total_days = max(1, (max_date - min_date).days)

    if total_days >= 7:
        # Normal week-over-week split
        current_week_start = max_date - timedelta(days=6)
        prev_week_start    = max_date - timedelta(days=13)
        current_week_df = filtered_df[filtered_df['datetime'] >= current_week_start]
        prev_week_df = filtered_df[
            (filtered_df['datetime'] >= prev_week_start) &
            (filtered_df['datetime'] < current_week_start)
        ]
        comparison_label = 'last week'
    else:
        # Sub-week: split data at midpoint and compare halves
        half_days = total_days / 2
        split_date = min_date + timedelta(days=half_days)
        current_week_df = filtered_df[filtered_df['datetime'] >= split_date]
        prev_week_df    = filtered_df[filtered_df['datetime'] <  split_date]
        comparison_label = f'last {total_days} day{"s" if total_days != 1 else ""}'

    def _pct_change(curr, prev):
        if prev == 0:
            return None if curr == 0 else 100.0
        return round((curr - prev) / prev * 100, 1)

    week_over_week = {
        'total':    _pct_change(len(current_week_df), len(prev_week_df)),
        'positive': _pct_change(int((current_week_df['sentimen'] == 'positive').sum()),
                                int((prev_week_df['sentimen'] == 'positive').sum())),
        'neutral':  _pct_change(int((current_week_df['sentimen'] == 'neutral').sum()),
                                int((prev_week_df['sentimen'] == 'neutral').sum())),
        'negative': _pct_change(int((current_week_df['sentimen'] == 'negative').sum()),
                                int((prev_week_df['sentimen'] == 'negative').sum()))
    }

    # Source share of voice (top 8)
    source_sov_series = filtered_df['source_news'].value_counts()
    source_sov = [{'source': src, 'count': int(cnt)} for src, cnt in source_sov_series.items()]

    # Entity share of voice (top 10 entities by mention count)
    if 'entitas' in filtered_df.columns:
        ent_sov_df = filtered_df[['entitas']].copy()
        ent_sov_df['entitas'] = ent_sov_df['entitas'].str.lower().str.split(', ')
        ent_sov_df = ent_sov_df.explode('entitas').reset_index(drop=True)
        ent_sov_df = ent_sov_df[~ent_sov_df['entitas'].isin(['tidak ada', keyword.lower(), ''])]
        entity_sov_series = ent_sov_df['entitas'].value_counts()
        entity_sov = [{'entity': ent, 'count': int(cnt)} for ent, cnt in entity_sov_series.items()]
    else:
        entity_sov = []

    # Date range from actual data
    dates_sorted = sorted(filtered_df['datetime'].dt.strftime('%Y-%m-%d').unique().tolist())
    date_range = {'min': dates_sorted[0], 'max': dates_sorted[-1]} if dates_sorted else {'min': None, 'max': None}
    
    return jsonify({
        'news_over_time': news_over_time.to_dict('records'),
        'sentiment_over_time': sentiment_time_data,
        'top_sources': sources_data,
        'top_topics': topik_data,
        'top_entities': entitas_data,
        'topic_share': {'data': topic_share_data, 'topics': top5_topics},
        'entity_trend': {'data': entity_trend_data, 'entities': top5_entities},
        'source_bubble': source_bubble_data,
        'heatmap': heatmap_data,
        'topic_entity_heatmap': topic_entity_heatmap,
        'radar': radar_payload,
        'sankey': sankey_data,
        'source_trend': {'data': source_trend_data, 'sources': top5_src},
        'radar_sources': radar_sources_payload,
        'summary': {
            'total': total_news,
            'positive': positive_count,
            'neutral': neutral_count,
            'negative': negative_count
        },
        'week_over_week': week_over_week,
        'comparison_label': comparison_label,
        'source_sov': source_sov,
        'entity_sov': entity_sov,
        'date_range': date_range
    })

@app.route('/api/news/<keyword>')
def get_news_list(keyword):
    data = get_data()
    subset_df = data[data['keyword'] == keyword]
    hashable_cols = [c for c in subset_df.columns if not subset_df[c].apply(lambda x: isinstance(x, (list, dict, np.ndarray))).any()]
    filtered_df = subset_df.drop_duplicates(subset=hashable_cols).reset_index(drop=True)
    date_col = "datetime" if "datetime" in filtered_df.columns else ("last_update" if "last_update" in filtered_df.columns else None)
    if date_col:
        filtered_df[date_col] = pd.to_datetime(filtered_df[date_col], errors='coerce')
        filtered_df = filtered_df.sort_values(date_col, ascending=False)
    
    # Get all news (removed .head(20) limitation)
    news_list = []
    for _, row in filtered_df.iterrows():
        ner_val = row.get('NER_normalized') if 'NER_normalized' in filtered_df.columns else []
        if not isinstance(ner_val, list):
            ner_val = []
        entities = [e for e in ner_val if e and str(e).lower() not in ('tidak ada', keyword.lower())]
        src = row.get('normalized_source_news', '')
        news_list.append({
            'title': row.get('headline_title', row.get('judul_berita', '')),
            'source': src if src and str(src) != 'nan' else '',
            'date': str(row.get('last_update', '') or row.get('last_update', '')),
            'sentiment': row.get('sentimen', ''),
            'topic': row.get('topik_berita', ''),
            'url': row.get('source_news_url', row.get('url', '#')),
            'entities': entities
        })
    
    return jsonify(news_list)

@app.route('/api/scrape')
def scrape_news_stream():
    keyword    = request.args.get('keyword', '').strip()
    start_date = request.args.get('start_date', '')
    end_date   = request.args.get('end_date', '')
    language   = request.args.get('language', 'id')
    country    = request.args.get('country', 'ID')

    if not keyword or not start_date or not end_date:
        def _err():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Missing required parameters'})}\n\n"
        return Response(stream_with_context(_err()), mimetype='text/event-stream')

    msg_queue = _queue.Queue()

    def progress_cb(message):
        msg_queue.put({'type': 'progress', 'message': message})

    def do_scrape():
        global _cached_data, _active_data_path, _active_language
        _active_language = language
        try:
            from google_news_scraper import GoogleNewsScraper
            scraper = GoogleNewsScraper(language=language, country=country)
            df = scraper.scrape_keywords(
                [keyword], start_date, end_date, progress_cb=progress_cb
            )
            if df is not None and not df.empty:
                df['sentimen']               = 'neutral'
                df['topik_berita']           = 'Tidak Dikategorikan'
                df['normalized_source_news'] = df['source_news']
                with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
                    raw_path = tmp.name
                df.to_parquet(raw_path, index=False)
                msg_queue.put({'type': 'progress', 'message': f'Scraping done ({len(df)} articles). Starting AI labeling...'})

                # Run the full processing pipeline with progress updates
                def _proc_cb(msg):
                    msg_queue.put({'type': 'progress', 'message': msg})

                processed_df = run_processing_pipeline(df, _model_generative, language=language, progress_cb=_proc_cb)

                # Keep processed result in memory only — no file written to disk
                _cached_data = processed_df
                msg_queue.put({'type': 'done', 'count': len(processed_df)})
            else:
                msg_queue.put({'type': 'error', 'message': 'No articles found. Try a different keyword or date range.'})
        except Exception as exc:
            msg_queue.put({'type': 'error', 'message': str(exc)})

    threading.Thread(target=do_scrape, daemon=True).start()

    def generate():
        while True:
            try:
                msg = msg_queue.get(timeout=600)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg['type'] in ('done', 'error'):
                    break
            except _queue.Empty:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Request timed out'})}\n\n"
                break

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@app.route('/api/download/<keyword>')
def download_excel(keyword):
    data = get_data()
    subset_df = data[data['keyword'] == keyword]
    hashable_cols = [c for c in subset_df.columns if not subset_df[c].apply(lambda x: isinstance(x, (list, dict, np.ndarray))).any()]
    export_df = subset_df.drop_duplicates(subset=hashable_cols).reset_index(drop=True)
    # Flatten list columns to comma-separated strings for Excel
    for col in ('NER', 'NER_normalized'):
        if col in export_df.columns:
            export_df[col] = export_df[col].apply(
                lambda x: ', '.join(str(e) for e in x) if isinstance(x, list) else (x or '')
            )
    buf = io.BytesIO()

    # Clean up export_df
    export_df = export_df[['datetime', 'keyword', 'headline_title',
                           'source_news_url', 'normalized_source_news', 
                           'topik_berita', 'NER_normalized',  
                           'sentimen']].copy()
    
    export_df = export_df.rename(columns={
        'normalized_source_news': 'source_news',
        'topik_berita': 'news_topic',
        'NER_normalized': 'entities',
        'sentimen': 'sentiment'
    })

    export_df.to_excel(buf, index=False, engine='openpyxl')
    buf.seek(0)
    safe_kw = keyword.replace(' ', '_').replace('/', '_').replace('\\', '_')
    return send_file(
        buf,
        as_attachment=True,
        download_name=f'{safe_kw}_news.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/api/ai_insight/<keyword>')
def get_ai_insight(keyword):
    data = get_data()
    filtered_df = data[data['keyword'] == keyword].copy()
    if filtered_df.empty:
        return jsonify({'error': 'No data found for keyword'}), 404
    result = generate_insight(filtered_df, _model_generative, language=_active_language)
    return jsonify({'insight': result})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
