"""
news_engine.py

Fetches latest news headlines using NewsAPI.
Author: [Your Name], 2025-05-28

Example input/voice: "Give me the news in Nigeria" → intent: get_news, entities: {country: NG}
"""
import os
import requests
import logging

class NewsEngine:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY", "6513b1d989e44d3c853ff6e1e9eba7e3")
        self.base_url = "https://newsapi.org/v2/top-headlines"

    def get_top_headlines(self, country="us", count=3):
        """
        Returns a string summary of top news headlines for the given country.
        """
        country = self._normalize_country(country)
        params = {
            "apiKey": self.api_key,
            "country": country,
            "pageSize": count
        }
        return self._fetch_and_format_news(params, header=f"Top news in {country.upper()}:")

    def get_latest_headlines(self, count=3):
        """
        Returns latest news globally (default country='us').
        """
        params = {
            "apiKey": self.api_key,
            "country": "us",  # Always supply a country
            "pageSize": count
        }
        try:
            resp = requests.get(self.base_url, params=params, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("articles", [])
            if not articles:
                return "No news found right now."
            result = f"Top news headlines:\n"
            for idx, article in enumerate(articles, 1):
                result += f"{idx}. {article.get('title','No title')} ({article.get('source',{}).get('name','Unknown')})\n"
            return result.strip()
        except Exception as e:
            logging.error(f"NewsEngine error: {e}")
            return "Sorry, I couldn't fetch the news right now."


    def _fetch_and_format_news(self, params, header):
        try:
            resp = requests.get(self.base_url, params=params, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("articles", [])
            if not articles:
                return "No news found."
            result = header + "\n"
            for idx, article in enumerate(articles, 1):
                result += f"{idx}. {article.get('title','No title')} ({article.get('source',{}).get('name','Unknown')})\n"
            return result.strip()
        except Exception as e:
            logging.error(f"NewsEngine error: {e}")
            return "Sorry, I couldn't fetch the news right now."

    def _normalize_country(self, country):
        # Accepts country names or ISO-2 codes. (Improve as needed)
        country_map = {
            "nigeria": "ng", "united kingdom": "gb", "uk": "gb", "us": "us", "usa": "us",
            "canada": "ca", "germany": "de", "france": "fr", "india": "in", "australia": "au"
        }
        c = (country or "").strip().lower()
        return country_map.get(c, c if len(c) == 2 else "us")

# CLI test
if __name__ == "__main__":
    engine = NewsEngine()
    print("Type 'global' for global news, country code (us, gb, ng, etc) for local news, or 'exit':")
    while True:
        code = input("Country/global: ").strip()
        if code.lower() == "exit":
            break
        if code.lower() == "global":
            print(engine.get_latest_headlines())
        else:
            print(engine.get_top_headlines(code))




# News:

# User: "Tell me the latest news"

# Call: NewsEngine().get_top_headlines("gb")

# Response:

# Usage:

# NewsEngine().get_top_headlines("ng")

# User: "What's the news in France?" → intent: get_news, entities: {country: France} → Output: "Top news in FRANCE:\n1. ...\n2. ..."