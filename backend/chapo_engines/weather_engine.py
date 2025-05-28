"""
weather_engine.py

Fetches current weather conditions using WeatherAPI.
Author: [Your Name], 2025-05-28

Example input/voice: "What's the weather in Paris?" → intent: get_weather, entities: {city: Paris}
"""

import os
import requests
import logging

class WeatherEngine:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("WEATHER_API_KEY", "9da4a523b41c453ab6f91434251604")
        self.base_url = "http://api.weatherapi.com/v1/current.json"

    def get_current_weather(self, city):
        """
        Returns a string with the current weather for the given city.
        """
        if not city:
            return "Please specify a city to check the weather."
        params = {
            "key": self.api_key,
            "q": city,
            "aqi": "no"
        }
        try:
            resp = requests.get(self.base_url, params=params, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            description = data['current']['condition']['text']
            temp = data['current']['temp_c']
            return f"The weather in {city} is {description} with {temp}°C."
        except Exception as e:
            logging.error(f"WeatherEngine error for {city}: {e}")
            return f"Sorry, I couldn't fetch weather info for {city} right now."

# CLI test
if __name__ == "__main__":
    engine = WeatherEngine()
    print("Type a city for weather ('exit' to quit):")
    while True:
        city = input("City: ").strip()
        if city.lower() == "exit":
            break
        print(engine.get_current_weather(city))



# How these work (with examples)
# Weather:

# User: "What's the weather in Lagos?"

# Call: WeatherEngine().get_current_weather("Lagos")

# Response: "The weather in Lagos is Cloudy with 28°C."

# Usage:

# WeatherEngine().get_current_weather("London")

# User: "What's the weather in Lagos?" → intent: get_weather, city: Lagos → Output: "The weather in Lagos is Sunny with 30°C."