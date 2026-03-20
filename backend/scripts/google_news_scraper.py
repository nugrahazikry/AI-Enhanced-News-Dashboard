"""Google News Scraper v2 - day-looping for maximum results.
Can be imported as a module or run as a CLI script.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import random
import os
import argparse
import urllib.parse
from xml.etree import ElementTree


class GoogleNewsScraper:
    """Google News Scraper using RSS Feed with date looping for maximum results."""

    def __init__(self, language='id', country='ID'):
        self.rss_url = "https://news.google.com/rss/search"
        self.language = language
        self.country = country
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        }
        self.session = requests.Session()

    def _build_rss_url(self, keyword, start_date=None, end_date=None):
        query = keyword
        if start_date and end_date:
            query = f"{keyword} after:{start_date} before:{end_date}"
        elif start_date:
            query = f"{keyword} after:{start_date}"
        elif end_date:
            query = f"{keyword} before:{end_date}"
        params = {
            'q': query,
            'hl': f'{self.language}-{self.country}',
            'gl': self.country,
            'ceid': f'{self.country}:{self.language}',
        }
        return f"{self.rss_url}?{urllib.parse.urlencode(params)}"

    def _parse_datetime(self, pub_date_str):
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(pub_date_str).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return pub_date_str

    def _extract_source_from_title(self, title):
        if ' - ' in title:
            parts = title.rsplit(' - ', 1)
            return parts[0].strip(), parts[1].strip()
        return title.strip(), ''

    def _generate_date_ranges(self, start_date, end_date):
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        ranges = []
        current = start
        while current <= end:
            next_day = current + timedelta(days=1)
            ranges.append({
                'start': current.strftime('%Y-%m-%d'),
                'end': next_day.strftime('%Y-%m-%d'),
            })
            current = next_day
        return ranges

    def _fetch_single_day(self, keyword, day_start, day_end):
        news_items = []
        url = self._build_rss_url(keyword, day_start, day_end)
        try:
            response = self.session.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            root = ElementTree.fromstring(response.content)
            scrape_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for item in root.findall('.//item'):
                try:
                    pub_date_elem = item.find('pubDate')
                    last_update = self._parse_datetime(
                        pub_date_elem.text if pub_date_elem is not None else ''
                    )
                    title_elem = item.find('title')
                    full_title = title_elem.text if title_elem is not None else ''
                    headline, source = self._extract_source_from_title(full_title)

                    link_elem = item.find('link')
                    article_url = link_elem.text if link_elem is not None else ''

                    desc_elem = item.find('description')
                    source_url = article_url
                    if desc_elem is not None and desc_elem.text:
                        soup = BeautifulSoup(desc_elem.text, 'html.parser')
                        link_tag = soup.find('a')
                        if link_tag and link_tag.get('href'):
                            source_url = link_tag['href']

                    news_items.append({
                        'scrape_date': scrape_date,
                        'keyword': keyword,
                        'last_update': last_update,
                        'headline_title': headline,
                        'source_news': source,
                        'normalized_source_news': source,
                        'source_news_url': source_url,
                    })
                except Exception:
                    continue
        except Exception:
            pass
        return news_items

    def scrape_keyword(self, keyword, start_date, end_date, progress_cb=None):
        date_ranges = self._generate_date_ranges(start_date, end_date)
        total_days = len(date_ranges)
        all_news = []
        seen_urls = set()

        if progress_cb:
            progress_cb(f"Starting scrape for '{keyword}' — {total_days} days to process")

        for i, dr in enumerate(date_ranges, 1):
            if progress_cb:
                progress_cb(f"Scraping news for \"{keyword}\" ({i}/{total_days})")
            day_news = self._fetch_single_day(keyword, dr['start'], dr['end'])
            new_count = 0
            for news in day_news:
                url = news['source_news_url']
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_news.append(news)
                    new_count += 1
            time.sleep(random.uniform(0.3, 0.6))

        # Keep only articles where the keyword appears in the headline
        all_news = [n for n in all_news if keyword.lower() in n['headline_title'].lower()]

        for i, news in enumerate(all_news, 1):
            news['page'] = (i - 1) // 10 + 1
            news['position'] = i

        if progress_cb:
            progress_cb(f"Found {len(all_news)} unique articles for '{keyword}'")

        return all_news

    def scrape_keywords(self, keywords, start_date, end_date, progress_cb=None):
        all_results = []
        for i, keyword in enumerate(keywords):
            results = self.scrape_keyword(
                keyword, start_date, end_date, progress_cb=progress_cb
            )
            all_results.extend(results)
            if i < len(keywords) - 1:
                delay = random.uniform(2, 4)
                if progress_cb:
                    progress_cb(f"Waiting {delay:.1f}s before next keyword...")
                time.sleep(delay)
        return pd.DataFrame(all_results) if all_results else pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description='Scrape Google News by keyword')
    parser.add_argument('--keywords', '-k', nargs='+', required=True)
    parser.add_argument('--start-date', '-s', required=True)
    parser.add_argument('--end-date', '-e', required=True)
    parser.add_argument('--language', '-l', default='id')
    parser.add_argument('--country', '-c', default='ID')
    parser.add_argument('--output-dir', '-o', default='../data')
    args = parser.parse_args()

    scraper = GoogleNewsScraper(language=args.language, country=args.country)
    df = scraper.scrape_keywords(
        args.keywords, args.start_date, args.end_date,
        progress_cb=lambda m: print(m)
    )
    if not df.empty:
        os.makedirs(args.output_dir, exist_ok=True)
        date_str = datetime.now().strftime('%Y%m%d')
        clean_kw = '_'.join(args.keywords).replace(' ', '_')
        path = os.path.join(args.output_dir, f'{date_str}_{clean_kw}_news.parquet')
        df.to_parquet(path, index=False)
        print(f"Saved {len(df)} articles -> {path}")
    else:
        print("No articles found.")


if __name__ == '__main__':
    main()