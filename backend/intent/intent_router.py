"""
intent_router.py

Central dispatcher for intent → engine/feature routing.
Handles session memory, spaCy fallback, MongoDB logging, and canned responses.

Author: [Your Name], 2025-05-28
"""

import random
import re
import os
import logging
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse
import requests

import spacy
from pymongo import MongoClient

# --- Import Engines (for weather/news) ---
from chapo_engines.weather_engine import WeatherEngine
from chapo_engines.news_engine import NewsEngine

weather_engine = WeatherEngine()
news_engine = NewsEngine()

# --- Load spaCy NER model once ---
nlp = spacy.load("en_core_web_sm")

# --- MongoDB Client (optional for cloud logging) ---
mongo_uri = os.getenv("MONGODB_URI")
client = MongoClient(mongo_uri) if mongo_uri else None
try:
    db = client.get_default_database() if client else None
except Exception:
    db = None

# --- In-memory session dict (ephemeral) ---
session_memory = {}
SESSION_TTL_MINUTES = 15

# --- Intent Normalization Map ---
INTENT_NORMALIZATION_MAP = {
    # --- Main Supported Intents ---
    "wit$get_weather": "get_weather",
    "get_weather": "get_weather",
    "weather_forecast": "get_weather",
    # Shopping List
    "add_to_grocery_list": "add_to_shopping_list",
    "check_grocery_list": "check_shopping_list",
    "clear_list": "clear_shopping_list",
    "calendar_integration": "get_shopping_list",
    "remove_from_shopping_list": "remove_from_shopping_list",
    # Alarms
    "set_alarm": "set_alarm",
    "cancel_alarm": "stop_alarm",
    "delete_alarm": "stop_alarm",
    "stop_alarm": "stop_alarm",
    "list_alarms": "list_alarms",
    # Reminders
    "set_reminder": "set_reminder",
    "delete_reminder": "delete_reminder",
    "cancel_reminder": "delete_reminder",
    "list_reminders": "list_reminders",
    # Trivia
    "play_trivia": "play_trivia",
    "trivia_question": "play_trivia",
    "answer_trivia": "play_trivia",
    "start_trivia": "play_trivia",
    "trivia_question": "play_trivia",
    "answer_trivia": "play_trivia",
    # Greetings/Core
    "greeting": "greeting",
    "goodbye": "goodbye",
    "how_are_you": "how_are_you",
    "tell_me_about_you": "tell_me_about_you",
    "bot_feelings": "bot_feelings",
    # Help/Joke/Time/Fallback
    "help": "help",
    "what_can_you_do": "help",
    "tell_joke": "tell_joke",
    "time_now": "time_now",
    "unknown": "unknown",


   ## news
    "get_news": "get_news",
    "news_headlines": "get_news",
    "top_news": "get_news",
    "latest_news": "get_news",
    "today_headlines": "get_news",
    "todays_headlines": "get_news",
    "headline_news": "get_news",
    "tech_news": "get_news",
    "idle_convo": "small_talk" # or "greeting" or "casual_chat"

}


# --- Canned Response Templates ---
INTENT_RESPONSES = {
    "how_are_you": [
        "I'm functioning perfectly! How about you?",
        "Better now that we’re chatting!",
        "I’m great! What’s on your mind?",
        "Feeling sharp as ever!"
    ],
    "set_reminder": [
        "Reminder saved! I won’t let you forget.",
        "Got it — I’ll remind you.",
        "Noted. You’ll get a heads-up!",
        "I’ve locked it in your memory queue."
    ],
    "turn_on_lights": [
        "Lights turned on. Let there be light!",
        "Bringing brightness to the room!",
        "The lights are on now.",
        "Light mode: activated."
    ],
    "turn_off_lights": [
        "Turning the lights off now.",
        "Lights out. Enjoy the dark.",
        "Off they go. Night mode activated.",
        "Done. The room is now dark."
    ],
    "time_now": [
        lambda: f"The current time is {datetime.now().strftime('%I:%M %p')}",
        lambda: f"It’s now {datetime.now().strftime('%H:%M')}",
        lambda: f"Right now, it's {datetime.now().strftime('%I:%M %p')}",
        lambda: f"The time here is {datetime.now().strftime('%I:%M %p')}"
    ],
    "small_talk": [
        "I'm always here if you want to chat!",
        "Let's talk about anything you like.",
        "You can ask me to set reminders, check the weather, or just chat!",
        "What would you like to do today?"
    ]
}

def normalize_intent(intent):
    """Normalize/alias intents for robust routing."""
    if not intent:
        return "unknown"
    return INTENT_NORMALIZATION_MAP.get(intent, intent)

def handle_reminder_flow(session_id, entities):
    """
    Handles reminder intents, extracting task & time from Wit entities.
    Returns prompt if either field missing.
    """
    memory = session_memory.get(session_id, {}).get("data", {})
    logging.info(f"📦 Wit Entities: {entities}")

    # Extract task ("body" or "value") from entities
    task_key = next((k for k in entities if "task" in k), None)
    if task_key:
        task_values = [ent.get("value") or ent.get("body") for ent in entities[task_key] if ent.get("value") or ent.get("body")]
        if task_values:
            memory["task"] = max(task_values, key=len)  # Pick longest

    # Extract datetime value
    datetime_key = next((k for k in entities if "datetime" in k), None)
    if datetime_key:
        memory["datetime"] = entities[datetime_key][0].get("value")

    session_memory[session_id] = {"data": memory, "last_updated": datetime.now(timezone.utc)}

    task = memory.get("task")
    time = memory.get("datetime")

    if task and time:
        session_memory.pop(session_id, None)
        pretty_time = parse(time).strftime("%A at %I:%M %p") if time else time
        return f"✅ Reminder set: I’ll remind you to {task} on {pretty_time}."
    elif not task:
        return "📝 What should I remind you about?"
    elif not time:
        return "⏰ What time should I remind you?"

    return "Let's set your reminder. What should I remind you of and when?"

def prune_memory(session_id):
    """
    Deletes session memory if expired.
    """
    record = session_memory.get(session_id)
    if record and datetime.now(timezone.utc) - record.get("last_updated") > timedelta(minutes=SESSION_TTL_MINUTES):
        session_memory.pop(session_id, None)

def extract_spacy_entities(text: str):
    """
    Runs spaCy NER to extract fallback entities from user input.
    """
    doc = nlp(text)
    spacy_ents = {}
    for ent in doc.ents:
        label = ent.label_.lower()
        spacy_ents.setdefault(label, []).append(ent.text)
    return spacy_ents

def log_to_mongo(session_id, user_input, intent, response):
    """
    Saves each routed interaction to MongoDB, if available.
    """
    if db is not None:
        try:
            db.logs.insert_one({
                "session_id": session_id,
                "user_input": user_input,
                "intent": intent,
                "response": response,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            logging.error(f"❌ MongoDB logging error: {e}")

def route_intent(intent: str, entities: dict, user_input: str, session_id="default"):
    """
    Dispatches the intent to the right engine, handler, or canned response.
    - Adds spaCy fallback NER.
    - Logs to MongoDB.
    - Maintains session memory.
    """
    prune_memory(session_id)
    intent = normalize_intent(intent)

    # spaCy entity fallback
    spacy_entities = extract_spacy_entities(user_input)
    if spacy_entities:
        logging.info(f"🔍 spaCy NER fallback: {spacy_entities}")

    # --- Intent Routing ---
    if intent == "set_reminder":
        response = handle_reminder_flow(session_id, entities)

    elif intent == "time_now":
        response = random.choice(INTENT_RESPONSES["time_now"])()

    elif intent == "get_weather":
        # Use WeatherEngine (API key from .env)
        city = None
        # Wit.ai format
        if "wit$location" in entities:
            city = entities["wit$location"][0].get("value")
        # spaCy fallback
        if not city and "gpe" in spacy_entities:
            city = spacy_entities["gpe"][0]
        # Regex fallback
        if not city:
            match = re.search(r"(?:in|for)\s+([A-Za-z\s,]+)", user_input)
            if match:
                city = match.group(1).strip(" ?,")
        response = weather_engine.get_current_weather(city) if city else "Please provide a location to get the weather."

    elif intent == "get_news":
        # Accepts 'country' (wit$location or direct entity), but allows 'latest news' to default to general headlines
        country = None
        # Wit.ai "country" or "wit$location" or spaCy fallback
        if "country" in entities and isinstance(entities["country"], list):
            country = entities["country"][0].get("value")
        elif "wit$location" in entities and isinstance(entities["wit$location"], list):
            country = entities["wit$location"][0].get("value")
        elif "gpe" in spacy_entities:  # spaCy geo-political entity
            country = spacy_entities["gpe"][0]

        if country:
            response = news_engine.get_top_headlines(country)
        else:
            response = news_engine.get_latest_headlines()

    elif intent in INTENT_RESPONSES:
        responses = INTENT_RESPONSES[intent]
        response = random.choice(responses) if isinstance(responses, list) else responses

    elif intent == "small_talk":
        responses = INTENT_RESPONSES["small_talk"]
        response = random.choice(responses)

    else:
        response = "🤔 I'm not sure how to handle that yet."

    log_to_mongo(session_id, user_input, intent, response)
    return response
