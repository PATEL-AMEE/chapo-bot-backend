"""
main.py - Chapo Bot Backend FastAPI App
Handles API routing, CORS, and database connection.
IntentRouter class is the entry point for voice/text intent dispatch.
Author: Your Name, 2025-05-28
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import voice, text, interactions
from backend.db.mongo import connect_db
from backend.api.shopping_list_routes import router as shopping_list_router
import logging
import os

from dotenv import load_dotenv
load_dotenv()

# --- FastAPI App Setup ---
app = FastAPI(title="Chapo Bot Backend")

# --- CORS Setup ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to ["https://yourfrontend.com"] in prod!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers Registration ---
app.include_router(shopping_list_router, prefix="/api")
app.include_router(voice.router)
app.include_router(text.router)
app.include_router(interactions.router)

# --- Logging Setup ---
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=os.path.join("logs", "chapo_backend.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# --- Engine Imports ---
# --- Engine Imports (exact from  chapo_engines folder) ---
from chapo_engines.alarm_engine import AlarmEngine
from chapo_engines.chapo_time_engine import ChapoTimeEngine
from chapo_engines.core_conversation_engine import CoreConversationEngine
from chapo_engines.emotion_detector_engine import EmotionDetectorEngine
from chapo_engines.joke_engine import handle_joke
from chapo_engines.memory_engine import MemoryEngine    # If you use this in routing (not shown in current logic)
from chapo_engines.news_engine import NewsEngine
from chapo_engines.reminder_engine import ReminderEngine
from chapo_engines.shopping_list_engine import ShoppingListEngine
# from chapo_engines.spotify_engine import SpotifyEngine  # (Optional, for future)
from chapo_engines.time_engine import ChapoTimeEngine
from chapo_engines.trivia_engine import handle_trivia
from chapo_engines.weather_engine import WeatherEngine


class IntentRouter:
    def __init__(self):
        self.alarm_engine = AlarmEngine()
        self.shopping_engine = ShoppingListEngine()
        self.core_convo = CoreConversationEngine()
        self.weather_engine = WeatherEngine()
        self.news_engine = NewsEngine()
        self.joke_engine = handle_joke  # function, not a class
        self.time_engine = TimeEngine()
        self.reminder_engine = ReminderEngine()
        self.emotion_engine = EmotionDetectorEngine()
        self.trivia_handler = handle_trivia  # function, not a class
        # Add more as needed (e.g., MemoryEngine, SpotifyEngine)


async def handle_intent(self, intent: str, entities: dict, session_id: str, user_input: str, session_memory: dict = None):
    session_memory = session_memory or {}

    # --- Alarm ---
    if intent == "set_alarm":
        return await self.alarm_engine.set_alarm(entities.get('time'), session_id)
    elif intent == "stop_alarm":
        return self.alarm_engine.stop_alarm(session_id)
    
    # --- Reminder ---
    elif intent in ["set_reminder", "delete_reminder", "list_reminders"]:
        return self.reminder_engine.handle_intent(intent, entities, session_id, user_input)
    
    # --- Shopping List ---
    elif intent in ["add_to_shopping_list", "remove_from_shopping_list", "get_shopping_list", "clear_shopping_list", "check_shopping_list"]:
        return self.shopping_engine.handle_intent(intent, entities, user_input)

    # --- Trivia/Games ---
    elif intent in ["play_trivia", "trivia_question", "answer_trivia"]:
        return self.trivia_handler(intent, user_input, session_id, session_memory)

    # --- Jokes ---
    elif intent == "tell_joke":
        return self.joke_engine(intent, user_input, entities)
    
    # --- Core Conversation ---
    elif intent in ["greeting", "how_are_you", "tell_me_about_you", "small_talk", "bot_feelings"]:
        return self.core_convo.process(intent, user_input)
    
    # --- Weather ---
    elif intent in ["get_weather", "weather_forecast", "wit$get_weather"]:
        city = None
        if entities and "wit$location" in entities:
            city = entities["wit$location"][0].get("value")
        if not city:
            city = self.weather_engine.extract_city_from_text(user_input)
        return self.weather_engine.get_current_weather(city) if city else "Please specify a city for weather."

    # --- News ---
    elif intent in ["get_news", "news_headlines", "top_news", "latest_news"]:
        country = None
    # Extract country from entities (adjust structure as needed)
        if entities and ("country" in entities):
            country = entities["country"][0].get("value")
        if not country:
        # Try fuzzy matching from user_input (optional, fallback)
            for name in ["nigeria", "united kingdom", "uk", "us", "canada", "germany", "france", "india", "australia"]:
                if name in user_input.lower():
                    country = name
                    break
        if country:
            return self.news_engine.get_top_headlines(country)
        else:
            return self.news_engine.get_latest_headlines()


    # --- Time ---
    elif intent in ["time_now"]:
        return self.time_engine.get_current_time()

    # --- Emotion/Emotion Report ---
    elif intent == "sentiment_report":
        return self.emotion_engine.handle_emotion(user_input)

    # --- Memory (if you want to support memory commands) ---
    elif intent in ["remember_that", "recall_memory"]:
        return self.memory_engine.handle_intent(intent, entities, user_input)
    
    # --- Fallback ---
    else:
        logging.warning(f"Unknown intent: {intent}, user_input: {user_input}")
        return "Sorry, I didn’t understand that. Try again!"

# --- FastAPI Startup Hook ---
@app.on_event("startup")
async def startup_event():
    try:
        connect_db()
        logging.info("✅ MongoDB connected.")
    except Exception as e:
        logging.error(f"❌ MongoDB startup error: {e}")

# --- Health Check Route ---
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Chapo Bot Backend is running"}
