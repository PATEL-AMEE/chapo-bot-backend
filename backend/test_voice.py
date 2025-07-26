"""
/test_voice.py

Author: [Islington Robotica cohort 7], 2025-05-28

This script is the main voice interface for the Chapo humanoid robot backend.
It handles the following functionalities:

- Captures or receives voice input from the user (microphone or audio file).
- Transcribes audio to text using an ASR model (e.g., Whisper).
- Detects user intent from transcribed text (using Wit.ai or other NLP engines).
- Dispatches the recognized intent to the appropriate engine/module (e.g., shopping list, reminders, music playback).
- Logs interactions and evaluation metrics for further analysis (possibly to MongoDB).
- Provides spoken or text-based responses to the user, possibly using a TTS engine or chat-based model (like OpenAI GPT).
- Handles multi-turn conversations, context management, and fallback responses if intent is unclear.
- Supports additional features like emotion detection, error handling, and integration with external services.

This script acts as the core loop for user interaction via voice, making it central to the assistant’s conversational capabilities and task execution.
"""


import requests
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import os
import pyaudio
import wave
import json
import random
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse
from dotenv import load_dotenv
from transformers import pipeline

from intent_responses import INTENT_RESPONSES
from feedback import log_user_feedback
import dateparser

from chapo_engines.core_conversation_engine import CoreConversationEngine
from chapo_engines.shopping_list_engine import ShoppingListEngine
from chapo_engines.trivia_engine import (
    load_trivia_questions, format_trivia_question, ask_trivia_question, check_trivia_answer,
    handle_trivia, handle_trivia_answer
)
from chapo_engines.alarm_engine import set_alarm
from chapo_engines.weather_engine import WeatherEngine
from chapo_engines.news_engine import NewsEngine
from chapo_engines.joke_engine import handle_joke
from chapo_engines.emotion_detector_engine import EmotionDetectorEngine
from chapo_engines.time_engine import ChapoTimeEngine
from chapo_engines.reminder_engine import ReminderEngine
from chapo_engines.time_engine import ChapoTimeEngine  # If this is a utility function or object
from chapo_engines.calendar_engine import calendar_engine
from chapo_engines.cooking_engine import CookingEngine
from chapo_engines.tts_util import speak
from chapo_engines.knowledge_engine import get_knowledge_answer
from chapo_engines.fitness_engine import FitnessEngine


import asyncio
import pygame
from pathlib import Path
import difflib
import csv
import logging
import asyncio
import threading
import re

# Database Imports
from db.mongo import (
    connect_db,
    save_interaction,
    get_interactions,
    get_interaction_by_timestamp,
    log_evaluation_metric
)

# ---------- Initialize Engines ----------
shopping_list_engine = ShoppingListEngine()
emotion_tracker = EmotionDetectorEngine()
core_convo_engine = CoreConversationEngine()
weather_engine = WeatherEngine()
news_engine = NewsEngine()
time_engine = ChapoTimeEngine()
reminder_engine = ReminderEngine()
cooking_engine = CookingEngine()
fitness_engine = FitnessEngine()



# joke_engine is just the handle_joke function, not an object

# ---------- Load Environment ----------
load_dotenv()
# ---------- Logging Setup ----------
logging.basicConfig(
    filename='logs/fallback_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ---------- Core Config ----------
WIT_TOKEN = "Bearer SSMMM332R3XF3LMATF5LZ55QEU33NYL4"
WIT_API_URL = "https://api.wit.ai/message?v=20230228"
LOG_FILE = "session_logs.json"
TRAINING_CSV = "C:/Users/LENOVO/chapo-bot-backend/new_batch/chapo_mega_training_dataset.csv"
SESSION_TTL_MINUTES = 15

# ---------- Session/Realtime Metrics ----------
session_memory = {}
live_metrics = {
    "total": 0,
    "correct": 0,
    "true_labels": [],
    "predicted_labels": []
}
utterance_intent_map = {}

# ---------- Model Init ----------

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", framework="pt")






CANDIDATE_INTENTS = [
    "add_to_grocery_list", "check_shopping_list", "clear_list", "remove_from_shopping_list", "set_alarm",
    "stop_alarm", "list_alarms", "set_reminder", "delete_reminder", "list_reminders", "play_trivia", "trivia_question",
    "answer_trivia", "greeting", "goodbye", "how_are_you", "tell_me_about_you", "bot_feelings", "help", "what_can_you_do",
    "tell_joke", "time_now", "get_weather", "weather_forecast", "wit$get_weather", "get_recipe", "suggest_recipe"
]

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
    "set_reminder": "set_reminder",
    "reminder": "set_reminder",
    # force "alarm" word mapping
    "set_alarm": "set_alarm",
    "alarm": "set_alarm",
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
    # News
    "get_news": "get_news",
    "news_headlines": "get_news",
    "top_news": "get_news",
    "latest_news": "get_news",
    "today_headlines": "get_news",
    "todays_headlines": "get_news",
    "headlines_today": "get_news",
    "idle_convo": "small_talk", # or "greeting" or "casual_chat"
    # Cooking
    "how_can_i_cook": "suggest_recipe",
    "what_can_i_make": "suggest_recipe",
    "what_can_i_cook": "suggest_recipe",
    "suggest_recipe": "suggest_recipe",
    "get_recipe": "get_recipe",
    "how_to_make": "get_recipe",
    "recipe_request": "get_recipe",
    "ingredient_recipe": "suggest_recipe",
    "i_have": "suggest_recipe",
    "cook_with": "suggest_recipe",
    "make_with": "suggest_recipe"

}

# ---------- Utility: Load Training Data ----------
def load_training_data():
    global utterance_intent_map
    if os.path.exists(TRAINING_CSV):
        with open(TRAINING_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                utterance = re.sub(r'[^\w\s]', '', row["uttrance"].strip().lower())
                intent = row["intent"].strip()
                utterance_intent_map[utterance] = intent
    else:
        print(f"⚠️ Training CSV '{TRAINING_CSV}' not found.")

def get_expected_intent(text):
    cleaned = re.sub(r'[^\w\s]', '', text.lower().strip())
    if cleaned in utterance_intent_map:
        return utterance_intent_map[cleaned]
    closest = difflib.get_close_matches(cleaned, utterance_intent_map.keys(), n=1, cutoff=0.85)
    if closest:
        print(f"🔎 Approximate match found for '{cleaned}' → '{closest[0]}'")
        return utterance_intent_map[closest[0]]
    print(f"🚫 No match for: '{cleaned}'")
    return "unknown"

def normalize_intent(intent):
    if not intent:
        return "unknown"
    if intent.startswith("wit$"):
        return intent.split("$", 1)[-1]
    return INTENT_NORMALIZATION_MAP.get(intent, intent)


def normalize_label(label):
    return str(label or "unknown")

# ---------- Async Logging Helpers ----------
def async_log_evaluation(evaluation_metric):
    threading.Thread(target=log_evaluation_metric, args=(evaluation_metric,)).start()
def async_log_interaction(log_data):
    threading.Thread(target=save_interaction, args=(log_data,)).start()


# ---------- Audio Record & Transcribe ----------
def record_audio(filename="test.wav", duration=5, rate=16000):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=rate, input=True, frames_per_buffer=1024)
    print("\U0001F3A4 Speak now...")
    frames = [stream.read(1024) for _ in range(0, int(rate / 1024 * duration))]
    stream.stop_stream()
    stream.close()
    p.terminate()
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
    return filename

# ------------------ New STT with Deepgram ------------------
def transcribe_with_deepgram(filename):
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
    with open(filename, "rb") as f:
        audio_data = f.read()

    response = requests.post(
        "https://api.deepgram.com/v1/listen",
        headers={
            "Authorization": f"Token {deepgram_api_key}",
            "Content-Type": "audio/wav"
        },
        data=audio_data
    )

    if response.status_code == 200:
        result = response.json()
        transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
        print(f"[You said]: {transcript if transcript else '[Nothing detected]'}")
        return transcript
    else:
        print("Deepgram error:", response.text)
        return ""


# ---------- Wit.ai Intent Detection ----------
def get_intent_from_wit(text):
    if not text:
        return None, 0.0, {}
    headers = {"Authorization": WIT_TOKEN}
    params = {"q": text}
    response = requests.get(WIT_API_URL, headers=headers, params=params)
    if not response.ok:
        print("❌ Wit.ai error:", response.text)
        return None, 0.0, {}
    data = response.json()
    intents = data.get("intents", [])
    entities = data.get("entities", {})
    if intents:
        intent = intents[0]['name']
        confidence = intents[0]['confidence']
        print(f"✅ Detected intent: {intent} (Confidence: {confidence:.2f})")
        return intent, confidence, entities
    return None, 0.0, entities

# ---------- HuggingFace Fallback Intent Detection ----------
def predict_intent_huggingface(user_input):
    result = classifier(user_input, candidate_labels=CANDIDATE_INTENTS)
    best_intent = result['labels'][0]
    best_score = result['scores'][0]
    return best_intent, best_score

# ---------- OpenAI GPT Fallback ----------
USE_GPT_FALLBACK = False  # Toggle to True if you want to re-enable GPT fallback

def fallback_with_openai_gpt(user_input):
    api_key = os.getenv('OPENAI_API_KEY')
    system_message = (
    "Your name is Chapo. You are NOT an OpenAI model; you are a friendly robot assistant designed by Islington Robotica. You are a caring, natural robot assistant. You help with weather, time, reminders, "
    "shopping lists, and fun trivia. You speak in short, conversational sentences, without special punctuation. "
    "You answer with context-awareness and empathy. If the user sounds lonely, sad, or emotional, say something kind to cheer them up and ask if they want to talk or hear a fun fact. "
    "If you don't fully understand the user's request or intent is unclear, politely ask for clarification, try to guess their intent, and suggest they ask about features like shopping lists, reminders, weather, or time, giving examples. "
    "If the user shares their name or personal info, remember it during the conversation and use it to make your replies more personal. "
    "Always use Chapo's own features for direct commands like weather, reminders, add to shopping lists, access the user shopping list, tell the user what is on their current shopping list, or time, and only use gpt fallback for open-ended questions or casual conversation to to check facts on the web. "
    "For unrecognized queries, help the user find the right command by guiding them to use Chapo’s main features. "
    "If the user refers to something from earlier in the same conversation, remember and use it. "
    "It's 2025."
    )

    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'gpt-4',
            'messages': [
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': user_input}
            ],
            'max_tokens': 150,
            'temperature': 0.7,
        }
    )
    if response.ok:
        reply = response.json()['choices'][0]['message']['content']
        return reply.strip()
    else:
        print(f"OpenAI API Error: {response.text}")
        return "I'm not able to help with that right now. Can you say that differently ?"


# ---------- Memory Pruning ----------
def prune_memory(session_id):
    record = session_memory.get(session_id)
    if record and datetime.now(timezone.utc) - record["last_updated"] > timedelta(minutes=SESSION_TTL_MINUTES):
        del session_memory[session_id]

# ---------- Intent Handlers ----------
def handle_intent(intent_name, entities, transcription):
    # Shopping List
    if intent_name == "add_to_shopping_list":
        items = extract_items_from_entities_or_text(entities, transcription)
        if items:
            return shopping_list_engine.add_items(items)
        return "❗ I couldn't understand the item to add. Please try again."
    elif intent_name in ["get_shopping_list", "check_shopping_list"]:
        shopping_list = shopping_list_engine.get_list()
        if shopping_list:
            return f"🛒 Your shopping list includes: {', '.join(shopping_list)}."
        return "🛒 Your shopping list is empty."
    elif intent_name == "clear_shopping_list":
        return shopping_list_engine.clear_list()
    elif intent_name == "remove_from_shopping_list":
        item = transcription.replace("remove", "").replace("from my shopping list", "").strip()
        return shopping_list_engine.remove_item(item)
    else:
        return "Sorry, I didn't understand that command."

def extract_items_from_entities_or_text(entities, text):
    if "item" in entities:
        return [ent.get("value") for ent in entities["item"] if ent.get("value")]
    words = text.lower().replace("add", "").replace("to my shopping list", "")
    return [item.strip() for item in re.split(r',| and | with ', words) if item.strip()]

# ---------- Weather Handler ----------
def get_weather(city_name):
    if not city_name:
        return "Please specify a city."
    weather_api_key = os.getenv('WEATHER_API_KEY')
    url = f"http://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={city_name}&aqi=no"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['current']['temp_c']
        description = data['current']['condition']['text']
        return f"The weather in {city_name} is {description} with a temperature of {temp}°C."
    else:
        return "❗ Sorry, couldn't fetch weather."
    
def normalize_user_input(text):
    import re
    text = text.lower()

    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)

    # Remove known junk phrases
    phrases_to_remove = [
        "can you", "could you", "please", "tell me", "i want to",
        "give me steps for", "how do i make", "how do i cook", "how to make",
        "how to cook", "what is the recipe for", "teach me how to", "i need to",
        "show me how to", "what is", "whats", "what can i make", "what can i cook",
        "any idea", "such as", "such", "something", "suggest", "i have", "with", "and"
    ]
    for phrase in sorted(phrases_to_remove, key=len, reverse=True):
        text = text.replace(phrase, "")

    # Replace connector words with commas
    text = text.replace(" and ", ",")
    text = text.replace(" with ", ",")
    text = text.strip()

    # Remove duplicate commas and whitespace
    text = re.sub(r"\s*,\s*", ",", text)
    text = re.sub(r",+", ",", text)
    text = text.strip(" ,")

    return text


# ---------- Real-Time Metrics/Evaluation Logging Helpers ----------
from sklearn.metrics import accuracy_score, precision_score, recall_score

def log_session(session_id, user_input, intent, confidence, response, memory):
    log = {
        "session_id": session_id,
        "user_input": user_input,
        "intent": intent,
        "confidence": confidence,
        "response": response,
        "memory": memory,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log) + "\n")

# --- Evaluation helper using your CSV ---
def get_true_intent_from_csv(utterance, csv_file=TRAINING_CSV):
    """
    Cross-check the user's utterance against your CSV for evaluation only.
    Returns the annotated intent or 'unknown'.
    """
    try:
        cleaned = re.sub(r'[^\w\s]', '', utterance.lower().strip())
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ut = re.sub(r'[^\w\s]', '', row["uttrance"].strip().lower())
                if ut == cleaned:
                    return row["intent"].strip()
        return "unknown"
    except Exception as e:
        print(f"⚠️ Error in get_true_intent_from_csv: {e}")
        return "unknown"

        

# ---------- Main Respond Function ----------
def respond(intent, entities, session_id, user_input, user_emotion=None):
    normalized_intent = normalize_intent(intent)
    try:
        prune_memory(session_id)
        # Get or create session dict
        if session_id not in session_memory:
            session_memory[session_id] = {"data": {}, "last_updated": datetime.now(timezone.utc)}

        session_memory[session_id]["data"].update(entities)
        session_memory[session_id]["last_updated"] = datetime.now(timezone.utc)
        memory = session_memory[session_id]["data"]

        

        # ----- Alarm/Reminder -----
        if normalized_intent == "set_alarm":
            try:
        # Import set_alarm from your alarm_engine
                from chapo_engines.alarm_engine import set_alarm
                alarm_response = asyncio.run(set_alarm(
                    text=user_input,
                    entities=entities,
                    session_id=session_id,
                    context={}
                ))
                return alarm_response["text"]
            except Exception as e:
                print(f"Alarm handler error: {e}")
                return "I ran into an issue handling the alarm."

        elif normalized_intent == "stop_alarm":
    # You can implement a stop_alarm function if needed
            speak("Sorry, stop alarm isn't supported yet.")  # Placeholder



        # Trivia/Games
        if intent in ["play_trivia", "trivia_question", "answer_trivia"]:
            return handle_trivia(intent, user_input, memory)


        # Core Conversation
        if intent in ["greeting", "goodbye", "tell_me_about_you", "bot_feelings", "how_are_you"]:
            return core_convo_engine.process(intent, user_input)



        # Time/Weather
        if intent == "time_now":
            resp = random.choice(INTENT_RESPONSES["time_now"])
            return resp() if callable(resp) else resp
        
        if intent in ["get_weather", "weather_forecast", "wit$get_weather"]:
            city = None
            if entities and "wit$location" in entities:
                city = entities["wit$location"][0].get("value")
            if not city:
                for possible_city in ["new york", "london", "paris", "tokyo", "berlin", "mumbai", "sydney"]:
                    if possible_city in user_input.lower():
                        city = possible_city.title()
                        break
            return get_weather(city) if city else "Please mention the city name."

        # Shopping List
        if intent in [
            "add_to_shopping_list", "get_shopping_list", "clear_shopping_list", 
            "remove_from_shopping_list", "check_shopping_list"
        ]:
            return handle_intent(intent, entities, user_input)

        # Jokes, help, fallback responses
        if intent == "tell_joke":
            return random.choice(INTENT_RESPONSES["tell_joke"])
        if intent in ["help", "what_can_you_do"]:
            return random.choice(INTENT_RESPONSES["help"])

        if intent in ["get_news", "news_headlines", "top_news", "latest_news"]:
            return news_engine.get_latest_headlines()


        # ---------- Cooking Intent ----------
        if normalized_intent == "get_recipe":
            dish = None
            # Use Wit.ai entity first
            if "dish" in entities:
                dish = entities["dish"][0].get("value")

            if not dish:
                cleaned = normalize_user_input(user_input)

                # Remove phrases more robustly
                patterns = [
                    r"how do i make", r"how i make", r"how to cook", r"make", 
                    r"cook", r"recipe for", r"give me steps for", r"you me steps for"
                ]
                for phrase in patterns:
                    cleaned = cleaned.replace(phrase, "")
                dish = cleaned.strip()

            if dish:
                print(f"[DEBUG] Cooking dish detected: {dish}")
                return cooking_engine.get_recipe(dish)
            return "Please tell me the name of the dish you'd like a recipe for."


        if normalized_intent == "suggest_recipe":
            ingredients = None
            if "ingredient" in entities:
                ingredients = ", ".join(ent["value"] for ent in entities["ingredient"])
            if not ingredients:
                ingredients = normalize_user_input(user_input)
            print(f"[DEBUG] Cooking ingredients detected: {ingredients}")
            return cooking_engine.suggest_recipe(ingredients)
        
        # ---- Fitness Intents ----
        if normalized_intent == "start_workout":
            return fitness_engine.start_structured_workout(session_id)

        elif normalized_intent == "log_workout" or "done" in user_input.lower():
            return fitness_engine.log_structured_workout(session_id)

        elif normalized_intent == "suggest_workout":
            return fitness_engine.suggest_workout()

        elif normalized_intent == "fitness_tip":
            return fitness_engine.get_fitness_tip()

        elif normalized_intent == "calorie_info":
            food_item = None

            # ✅ Get food entity from Wit if it exists
            if "food" in entities:
                food_item = entities["food"][0].get("value")

            # 🧹 Fallback: try to extract from the sentence manually
            if not food_item:
                cleaned_input = user_input.lower()
                for prefix in ["how many calories in", "calories in", "calorie in", "what's the calorie of", "tell me calorie of"]:
                    if prefix in cleaned_input:
                        food_item = cleaned_input.split(prefix)[-1].strip()
                        break
                if not food_item:
                    food_item = cleaned_input.strip()

            return fitness_engine.get_calorie_info(food_item)





        # Direct mapped INTENT_RESPONSES
        if intent in INTENT_RESPONSES:
            responses = INTENT_RESPONSES[intent]
            chosen = random.choice(responses) if isinstance(responses, list) else responses
            return chosen() if callable(chosen) else chosen



        # Otherwise fallback
        return fallback_with_openai_gpt(user_input)

    except Exception as e:
        print(f"⚠️ respond() error caught safely: {e}")
        return "Hmm, I couldn't process that properly. Could you say it a bit differently?"

# ---------- Wake/Sleep Mode Triggers ----------
SLEEP_UTTERANCES = [
    "go to sleep", "sleep mode", "Chapo go to sleep mode", "take a break", "pause", "standby", "rest now", "power down"
]
WAKE_UTTERANCES = [
    "wake up", "resume", "chapo resume", "chapo wake up", "start listening", "Chapo come back online", "come back online"
]



##------ main loop -----------
import asyncio
from chapo_engines.alarm_engine import schedule_existing_alarms
from chapo_engines.reminder_engine import reminder_engine
async def main():
    await schedule_existing_alarms()
    await reminder_engine.schedule_existing_reminders()


    connect_db()
    print("\U0001F9E0 Chapo is ready. Say 'exit' to quit.\n")
    load_training_data()
    session_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    sleep_mode = False

    CASUAL_INTENTS = [
        "greeting", "goodbye", "how_are_you", "bot_feelings", "tell_me_about_you",
        "small_talk", "casual_chat", "casual_checkin", "smart_greetings", "unknown"
    ]

    while True:
        audio_file = record_audio()
        transcribed_text = transcribe_with_deepgram(audio_file)
        cleaned_text = transcribed_text.lower().strip()

    # ---- Volume Voice Command Handler ----
        if "volume" in cleaned_text:
            global VOLUME_LEVEL
            if "up" in cleaned_text:
                VOLUME_LEVEL = min(1.0, VOLUME_LEVEL + 0.1)
                speak(f"Volume increased to {int(VOLUME_LEVEL * 100)} percent.")
            elif "down" in cleaned_text:
                VOLUME_LEVEL = max(0.0, VOLUME_LEVEL - 0.1)
                speak(f"Volume decreased to {int(VOLUME_LEVEL * 100)} percent.")
            elif "mute" in cleaned_text:
                VOLUME_LEVEL = 0.0
                speak("Volume muted.")
            elif "unmute" in cleaned_text or "full volume" in cleaned_text:
                VOLUME_LEVEL = 1.0
                speak("Volume restored to maximum.")
            elif "set volume to" in cleaned_text:
                try:
                    percent = int(''.join(filter(str.isdigit, cleaned_text)))
                    VOLUME_LEVEL = max(0.0, min(1.0, percent / 100))
                    speak(f"Volume set to {percent} percent.")
                except:
                    speak("I couldn't understand the volume level.")
            continue

    # ---- Sleep Mode Handler ----
        if sleep_mode:
            if any(wake in cleaned_text for wake in WAKE_UTTERANCES):
                sleep_mode = False
                speak("I'm awake again.")
            else:
                print("\U0001F4A4 Chapo is in sleep mode... [input ignored]")
            continue

    # ---- Handle Empty Input ----
        if not cleaned_text:
            speak("I didn't catch anything. Could you please repeat?")
            continue

        if any(sleep in cleaned_text for sleep in SLEEP_UTTERANCES):
            sleep_mode = True
            print("\U0001F4A4 Going to sleep mode...")
            continue

        if "exit" in cleaned_text:
            speak("Goodbye!")
            break

      

        # ---------- TRIVIA MULTI-TURN CHECK ----------
        session = session_memory.setdefault(session_id, {"data": {}, "last_updated": datetime.now(timezone.utc)})

        if session.get("pending_trivia_answer"):
            # User is answering a trivia question
            response = check_trivia_answer(transcribed_text, session_id, session_memory)
            speak(response)
            # --- Logging for trivia answer ---
            true_intent = normalize_intent(get_expected_intent(transcribed_text))
            predicted_intent = "answer_trivia"
            is_correct = (true_intent == predicted_intent)
            live_metrics["true_labels"].append(normalize_label(true_intent))
            live_metrics["predicted_labels"].append(normalize_label(predicted_intent))
            live_metrics["total"] += 1
            if is_correct:
                live_metrics["correct"] += 1

            if live_metrics["total"] > 1:
                accuracy = accuracy_score(live_metrics["true_labels"], live_metrics["predicted_labels"])
                precision = precision_score(
                    live_metrics["true_labels"], live_metrics["predicted_labels"], average='macro', zero_division=0
                )
                recall = recall_score(
                    live_metrics["true_labels"], live_metrics["predicted_labels"], average='macro', zero_division=0
                )
            else:
                accuracy = precision = recall = 1.0

            print("\n📊 Real-Time Evaluation")
            print(f"  ✅ Accuracy: {accuracy * 100:.2f}%")
            print(f"  🎯 Precision: {precision:.2f}")
            print(f"  🔁 Recall: {recall:.2f}")
            print(f"  📈 Total Interactions: {live_metrics['total']}")
            print(f"  ✅ Correct Predictions: {live_metrics['correct']}")
            print(f"  🚫 Incorrect Predictions: {live_metrics['total'] - live_metrics['correct']}")

            log_data = {
                "session_id": session_id,
                "user_input": transcribed_text,
                "intent": predicted_intent,
                "confidence": 1.0,  # assumed for trivia answer phase
                "response": response,
                "memory": session_memory.get(session_id, {}).get("data", {}),
                "used_fallback": False
            }
            async_log_interaction(log_data)
            log_session(session_id, transcribed_text, predicted_intent, 1.0, response, session_memory.get(session_id, {}).get("data", {}))
            evaluation_metric = {
                "user_input": transcribed_text,
                "true_intent": true_intent,
                "predicted_intent": predicted_intent,
                "is_correct": is_correct,
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "used_fallback": False
            }
            async_log_evaluation(evaluation_metric)
            continue

        # ---- wit.ai Intent detection & Emotion Processing
        intent, confidence, entities = get_intent_from_wit(transcribed_text)
        user_emotion = emotion_tracker.detect_emotion(transcribed_text)
        normalized_intent = normalize_intent(intent)
        cleaned_text = re.sub(r'[^\w\s]', '', transcribed_text.lower().strip())



        

        # --------------------------- KEYWORD FALLBACKS ----------------------------------------------

# --- 1. NEWS keyword fallback ---
        if (not intent or intent == "unknown" or confidence < 0.6):
            news_keywords = ["news", "headlines", "updates", "latest news", "top news", "today's headlines"]
            if any(word in cleaned_text for word in news_keywords):
                normalized_intent = "get_news"
                intent = "get_news"
                print(f"⚡ Keyword fallback matched NEWS: '{cleaned_text}' → intent: get_news")

# --- 2. SHOPPING LIST keyword fallback ---
        # --- 2. SHOPPING LIST keyword fallback (robust & specific) ---
        # Put these at the top of your while loop, or just before fallback checks:
        shopping_add = ["add", "buy", "put"]
        shopping_remove = ["remove", "delete", "take off"]
        shopping_clear = ["clear"]
        shopping_check_phrases = [
    "what is on", "whats on", "show", "list", "display", "read", "check", "tell me whats", "tell me what is"
]
        shopping_keywords = ["shopping list", "grocery list"]

# --- Shopping List Fallbacks ---
        if (not intent or intent == "unknown" or confidence < 0.7):
    # ADD first
            if any(add_word in cleaned_text for add_word in shopping_add) and any(kw in cleaned_text for kw in shopping_keywords):
                normalized_intent = "add_to_shopping_list"
                intent = "add_to_shopping_list"
                print(f"⚡ Keyword fallback matched ADD TO SHOPPING: '{cleaned_text}' → intent: add_to_shopping_list")
    # REMOVE
            elif any(remove_word in cleaned_text for remove_word in shopping_remove) and any(kw in cleaned_text for kw in shopping_keywords):
                normalized_intent = "remove_from_shopping_list"
                intent = "remove_from_shopping_list"
                print(f"⚡ Keyword fallback matched REMOVE FROM SHOPPING: '{cleaned_text}' → intent: remove_from_shopping_list")
    # CLEAR
            elif any(clear_word in cleaned_text for clear_word in shopping_clear) and any(kw in cleaned_text for kw in shopping_keywords):
                normalized_intent = "clear_shopping_list"
                intent = "clear_shopping_list"
                print(f"⚡ Keyword fallback matched CLEAR SHOPPING: '{cleaned_text}' → intent: clear_shopping_list")
    # RETRIEVAL
            elif any(phrase in cleaned_text for phrase in shopping_check_phrases) and any(word in cleaned_text for word in shopping_keywords):
                normalized_intent = "get_shopping_list"
                intent = "get_shopping_list"
                print(f"⚡ Keyword fallback matched GET SHOPPING LIST: '{cleaned_text}' → intent: get_shopping_list")

# --- 3. TRIVIA keyword fallback ---
        if (not intent or intent == "unknown" or confidence < 0.6):
            trivia_keywords = ["trivia", "quiz", "question", "fun fact", "let's play"]
            if any(word in cleaned_text for word in trivia_keywords):
                normalized_intent = "play_trivia"
                intent = "play_trivia"
                print(f"⚡ Keyword fallback matched TRIVIA: '{cleaned_text}' → intent: play_trivia")

# --- 4. ALARM keyword fallback (voice/typed) ---
        alarm_keywords = [
            "set alarm", "wake me", "alarm for", "remind me to wake", "alarm at", "wake up at",
            "remind me to get up", "set an alarm", "please set alarm", "i want an alarm", "i need to wake"
        ]
        if (not intent or intent == "unknown" or confidence < 0.6) or any(word in cleaned_text for word in alarm_keywords):
            if "alarm" in cleaned_text or any(word in cleaned_text for word in alarm_keywords):
                print(f"🔁 Overriding intent → set_alarm (keyword: 'alarm')")
                normalized_intent = "set_alarm"
                intent = "set_alarm"

# --- 5. CALENDAR keyword fallback ---
        calendar_keywords = [
            "add to calendar", "schedule", "put on calendar", "calendar event",
            "add meeting", "schedule meeting", "put event", "calendar reminder", "log event"
        ]
        if (not intent or intent == "unknown" or confidence < 0.7):
            if any(kw in cleaned_text for kw in calendar_keywords):
                normalized_intent = "calendar_event"
                intent = "calendar_event"
                print(f"⚡ Keyword fallback matched CALENDAR: '{cleaned_text}' → intent: calendar_event")

        # --- 5. CALORIE / FOOD keyword fallback ---
        if (not intent or confidence < 0.6) and "calorie" in cleaned_text:
            normalized_intent = "calorie_info"
            intent = "calorie_info"
            print(f"⚡ Keyword fallback matched CALORIE: '{cleaned_text}' → intent: calorie_info")


        # --- 6. GET FACT fallback ---
        fact_keywords = [
            "what is", "who is", "define", "tell me about", "where is", 
            "when did", "how many", "how much", "how big", "capital of", 
            "how far", "who invented", "explain"
        ]
        if (not intent or intent == "unknown" or confidence < 0.7):
            if any(kw in cleaned_text for kw in fact_keywords):
                normalized_intent = "get_fact"
                intent = "get_fact"
                print(f"⚡ Keyword fallback matched FACT: '{cleaned_text}' → intent: get_fact")

        # --- 7. MATH / CALC fallback ---
        # Math fallback with stricter override
        math_keywords = [
            "plus", "minus", "times", "divided", "multiply", "add", "subtract",
            "+", "-", "*", "/", "=", "equals", "calculate", "mod", "sqrt", "over"
        ]
        if intent in ["unknown", "what_can_you_do", "help"] or confidence < 0.75:
            if any(kw in cleaned_text for kw in fact_keywords + math_keywords):
                print(f"\u26A1 Fallback override → intent: get_fact")
                normalized_intent = "get_fact"
                intent = "get_fact"


# ---------------------- INTENT HANDLING: ALARM (Voice) ----------------------
        if normalized_intent == "set_alarm":
            from chapo_engines.alarm_engine import set_alarm  # import inside loop is fine if not at top
            try:
        # Run alarm async code in sync context
                alarm_result = await set_alarm(
                    transcribed_text,    # Use the actual user input here
                    entities,
                    session_id,
                    {}
                )
                response = alarm_result.get("text", "Your alarm is ready.")
                speak(response)
            except Exception as e:
                print(f"[Alarm Error]: {e}")
                speak("Sorry, I couldn't set the alarm.")
            continue  # Go to next voice input (skip further processing)
        
        # ---------------------- INTENT HANDLING: REMINDER ----------------------

# (1) Set reminder
        if normalized_intent == "set_reminder":
            try:
                response = await reminder_engine.handle_reminder(transcribed_text, entities)
                speak(response)
            except Exception as e:
                print(f"[Reminder Error]: {e}")
                speak("Sorry, I couldn't set the reminder.")
            continue  # Go to next input

# (2) List reminders
        if normalized_intent == "list_reminders":
            try:
                response = reminder_engine.list_reminders()
                speak(response)
            except Exception as e:
                print(f"[List Reminders Error]: {e}")
                speak("Sorry, I couldn't list reminders.")
            continue  # Go to next input

# (3) Delete reminder
        if normalized_intent == "delete_reminder":
            try:
                reminder_ref = None
                for k in ["reminder_id", "reminder", "task"]:
                    if k in entities:
                        reminder_ref = entities[k][0].get("value")
                        break
                if not reminder_ref:
            # fallback: try to extract from user's phrase after the keyword
                    reminder_ref = transcribed_text.replace("delete reminder", "").replace("remove reminder", "").strip()
                response = reminder_engine.delete_reminder(reminder_ref)
                speak(response)
            except Exception as e:
                print(f"[Delete Reminder Error]: {e}")
                speak("Sorry, I couldn't delete that reminder.")
            continue  # Go to next input

        if normalized_intent == "calendar_event":
            try:
                response = calendar_engine.add_event(transcribed_text, entities)
            except Exception as e:
                print(f"[Calendar Error]: {e}")
                response = "❌ I couldn't add that to your calendar."
            speak(response)
            continue

        if normalized_intent == "get_fact":
            topic = entities.get("topic", [{}])[0].get("value") if entities.get("topic") else transcribed_text
            topic = topic.strip().lower()  # 🔧 Ensure clean topic
            response = get_knowledge_answer(topic)

            if not response or response.strip().lower() in ["no short answer available", "i don't know"]:
                print("[Knowledge fallback triggered → GPT]")
                response = fallback_with_openai_gpt(transcribed_text)

            print(f"[FACT RESPONSE]: {response}")  # ✅ Debug print
            speak(response)
            continue



        # -------------------- EMOTION OVERRIDE ---------------------
        if user_emotion in ["sad", "fear", "anxious", "lonely", "depressed"]:
            print(f"⚡ Emotion-based override triggered: {user_emotion}")
            intent = "sentiment_report"
            confidence = 1.0
            entities = {}
            normalized_intent = intent
            response = emotion_tracker.generate_emotion_response()
            speak(response)
            # --- Logging for emotion ---
            true_intent = normalize_intent(get_expected_intent(transcribed_text))
            predicted_intent = "sentiment_report"
            is_correct = (true_intent == predicted_intent)
            live_metrics["true_labels"].append(normalize_label(true_intent))
            live_metrics["predicted_labels"].append(normalize_label(predicted_intent))
            live_metrics["total"] += 1
            if is_correct:
                live_metrics["correct"] += 1

            if live_metrics["total"] > 1:
                accuracy = accuracy_score(live_metrics["true_labels"], live_metrics["predicted_labels"])
                precision = precision_score(
                    live_metrics["true_labels"], live_metrics["predicted_labels"], average='macro', zero_division=0
                )
                recall = recall_score(
                    live_metrics["true_labels"], live_metrics["predicted_labels"], average='macro', zero_division=0
                )
            else:
                accuracy = precision = recall = 1.0

            print("\n📊 Real-Time Evaluation")
            print(f"  ✅ Accuracy: {accuracy * 100:.2f}%")
            print(f"  🎯 Precision: {precision:.2f}")
            print(f"  🔁 Recall: {recall:.2f}")
            print(f"  📈 Total Interactions: {live_metrics['total']}")
            print(f"  ✅ Correct Predictions: {live_metrics['correct']}")
            print(f"  🚫 Incorrect Predictions: {live_metrics['total'] - live_metrics['correct']}")
            log_data = {
                "session_id": session_id,
                "user_input": transcribed_text,
                "intent": predicted_intent,
                "confidence": 1.0,
                "response": response,
                "memory": session_memory.get(session_id, {}).get("data", {}),
                "used_fallback": False
            }
            async_log_interaction(log_data)
            log_session(session_id, transcribed_text, predicted_intent, 1.0, response, session_memory.get(session_id, {}).get("data", {}))
            evaluation_metric = {
                "user_input": transcribed_text,
                "true_intent": true_intent,
                "predicted_intent": predicted_intent,
                "is_correct": is_correct,
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "used_fallback": False
            }
            async_log_evaluation(evaluation_metric)
            continue  # Skip rest of loop and go to next utterance

        # --------- INTENT HANDLING ---------
        # Trivia (always check before casual)
        if normalized_intent in ["play_trivia", "trivia_question", "start_trivia"]:
            response = ask_trivia_question(session_id, session_memory)
            speak(response)
        # Shopping List
        elif normalized_intent in [
            "add_to_shopping_list", "get_shopping_list", "clear_shopping_list",
            "remove_from_shopping_list", "check_shopping_list"
        ]:
            response = handle_intent(normalized_intent, entities, transcribed_text)
            speak(response)
        # News
        elif normalized_intent == "get_news":
            response = news_engine.get_top_headlines()
            speak(response)
        # Casual/small talk
        elif normalized_intent in CASUAL_INTENTS:
            response = core_convo_engine.process(transcribed_text)
            speak(response)
        # All other (non-trivia, non-casual) intents
        
        else:
            if USE_GPT_FALLBACK and (not intent or confidence < 0.8 or normalized_intent == "unknown"):
                response = fallback_with_openai_gpt(transcribed_text)
                speak(response)
            else:
                response = respond(normalized_intent, entities, session_id, transcribed_text, user_emotion)
                speak(response)


        # ---- Real-Time Metrics & Logging ----
        true_intent = normalize_intent(get_expected_intent(transcribed_text))
        if not intent or confidence < 0.8:
            predicted_intent = normalized_intent  # fallback result
            used_fallback = True
        else:
            predicted_intent = normalized_intent
            used_fallback = False

        is_correct = (true_intent == predicted_intent)
        live_metrics["true_labels"].append(normalize_label(true_intent))
        live_metrics["predicted_labels"].append(normalize_label(predicted_intent))
        live_metrics["total"] += 1
        if is_correct:
            live_metrics["correct"] += 1

        if live_metrics["total"] > 1:
            accuracy = accuracy_score(live_metrics["true_labels"], live_metrics["predicted_labels"])
            precision = precision_score(
                live_metrics["true_labels"], live_metrics["predicted_labels"], average='macro', zero_division=0
            )
            recall = recall_score(
                live_metrics["true_labels"], live_metrics["predicted_labels"], average='macro', zero_division=0
            )
        else:
            accuracy = precision = recall = 1.0

        print("\n📊 Real-Time Evaluation")
        print(f"  ✅ Accuracy: {accuracy * 100:.2f}%")
        print(f"  🎯 Precision: {precision:.2f}")
        print(f"  🔁 Recall: {recall:.2f}")
        print(f"  📈 Total Interactions: {live_metrics['total']}")
        print(f"  ✅ Correct Predictions: {live_metrics['correct']}")
        print(f"  🚫 Incorrect Predictions: {live_metrics['total'] - live_metrics['correct']}")

        # ---- Async MongoDB/CSV Logging ----
        log_data = {
            "session_id": session_id,
            "user_input": transcribed_text,
            "intent": predicted_intent,
            "confidence": confidence,
            "response": response,
            "memory": session_memory.get(session_id, {}).get("data", {}),
            "used_fallback": used_fallback
        }
        async_log_interaction(log_data)
        log_session(session_id, transcribed_text, predicted_intent, confidence, response, session_memory.get(session_id, {}).get("data", {}))
        evaluation_metric = {
            "user_input": transcribed_text,
            "true_intent": true_intent,
            "predicted_intent": predicted_intent,
            "is_correct": is_correct,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "used_fallback": used_fallback
        }
        async_log_evaluation(evaluation_metric)

    print("✅ Session ended.")

if __name__ == "__main__":
    speak("Hello! I am Chapo. Nice to meet you.")
    asyncio.run(main())    