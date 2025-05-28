import pytest
from chapo_engines.news_engine import NewsEngine

def test_get_latest_headlines(monkeypatch):
    def mock_api(*args, **kwargs):
        class Response:
            status_code = 200
            def json(self):
                return {
                    "articles": [
                        {"title": "AI beats humans at chess"},
                        {"title": "Mars rover finds water"}
                    ]
                }
        return Response()
    monkeypatch.setattr("requests.get", mock_api)
    engine = NewsEngine()
    result = engine.get_latest_headlines()
    assert "AI beats humans" in result or "Mars rover finds water" in result

def test_get_latest_headlines_error(monkeypatch):
    def mock_api(*args, **kwargs):
        class Response:
            status_code = 500
            def json(self): return {}
        return Response()
    monkeypatch.setattr("requests.get", mock_api)
    engine = NewsEngine()
    result = engine.get_latest_headlines()
    assert "couldn't fetch news" in result.lower()
