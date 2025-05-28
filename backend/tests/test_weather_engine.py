import pytest
from chapo_engines.weather_engine import WeatherEngine

def test_get_current_weather(monkeypatch):
    # Mock API call for reproducible results
    def mock_api(*args, **kwargs):
        class Response:
            status_code = 200
            def json(self):
                return {
                    "current": {
                        "condition": {"text": "Sunny"},
                        "temp_c": 24
                    }
                }
        return Response()
    monkeypatch.setattr("requests.get", mock_api)
    engine = WeatherEngine()
    result = engine.get_current_weather("London")
    assert "Sunny" in result
    assert "24" in result

def test_get_current_weather_error(monkeypatch):
    def mock_api(*args, **kwargs):
        class Response:
            status_code = 500
            def json(self): return {}
        return Response()
    monkeypatch.setattr("requests.get", mock_api)
    engine = WeatherEngine()
    result = engine.get_current_weather("London")
    assert "couldn't fetch weather" in result.lower()
