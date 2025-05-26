import whisper
import requests
import os
import pyaudio
import wave
import pyttsx3
import json
import random
from datetime import datetime, timezone, timedelta
from dateutil.parser import parse
from dotenv import load_dotenv
from transformers import pipeline
from chapo_engines.spotify_engine import SpotifyPlayer
from intent_responses import INTENT_RESPONSES
from feedback import log_user_feedback  # <-- Make sure feedback.py exists
from chapo_engines.core_conversation_engine import handle_core_conversation

import difflib

from chapo_engines.shopping_list_engine import ShoppingListEngine
shopping_list_engine = ShoppingListEngine()


from chapo_engines.trivia_engine import handle_trivia
from chapo_engines.trivia_engine import handle_trivia


import csv
from chapo_engines.alarm_engine import set_alarm, stop_alarm



# ---------- Emotion Detection ----------
from emotion_detector import EmotionDetector
emotion_tracker = EmotionDetector()

# --- Evaluation Tracking ---
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, classification_report

# Import the functions from mongo.py
from db.mongo import (
    connect_db, 
    save_interaction, 
    get_interactions, 
    get_interaction_by_timestamp,
    log_evaluation_metric
)

import asyncio

from chapo_engines.reminder_engine import ReminderEngine
reminder_engine = ReminderEngine()





# Define the path to the training CSV file
TRAINING_CSV = "/Users/user/chapo-bot-backend/new_batch/chapo_mega_training_dataset.csv"
  # Update this path as needed

# Initialize live metrics for performance tracking
live_metrics = {
    "total": 0,
    "correct": 0,
    "true_labels": [],
    "predicted_labels": []
}

# Initialize utterance-intent mapping
utterance_intent_map = {}

# Load ground truth intents from training dataset
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

# Append evaluation log to MongoDB
# Mapping Wit.ai and others to your base intent names
from sklearn.metrics import precision_score, recall_score, accuracy_score
from datetime import datetime

# -- Normalization Map --
INTENT_NORMALIZATION_MAP = {
    # Weather
    "wit$get_weather": "get_weather",
    "get_weather": "get_weather",
    "weather_forecast": "get_weather",

    # Music
    "wit$play_music": "play_music",
    "play_music": "play_music",

    # Traffic
    "wit$check_traffic": "check_traffic",
    "check_traffic": "check_traffic",

    # Shopping list
    "add_to_grocery_list": "add_to_shopping_list",
    "check_grocery_list": "check_shopping_list",
    "clear_list": "clear_shopping_list",
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
    "set_reminder": "set_alarm",
    "list_reminders": "list_reminders",

    # Video Call
    "start_video_call": "video_call_friend",
    "video_call_friend": "video_call_friend",

    # Trivia
    "play_trivia": "play_trivia",
    "trivia_question": "play_trivia",
    "answer_trivia": "play_trivia",

    # Sentiment
    "sentiment_report": "sentiment_report",
    "chat_emotion": "sentiment_report",

    # Greetings & Core Conversation
    "greeting": "greeting",
    "goodbye": "goodbye",
    "how_are_you": "how_are_you",
    "tell_me_about_you": "tell_me_about_you",
    "bot_feelings": "bot_feelings",

    # Help
    "help": "help",
    "what_can_you_do": "help",

    # Joke
    "tell_joke": "tell_joke",

    # Time
    "time_now": "time_now",

    # Fallback
    "unknown": "unknown",
}


def normalize_intent(intent):
    if not intent:
        return "unknown"
    if intent.startswith("wit$"):
        return intent.split("$", 1)[-1]
    return INTENT_NORMALIZATION_MAP.get(intent, intent)

# -- Evaluation Logger --
def log_evaluation_to_mongo(user_input, true_intent, predicted_intent):
    """
    Logs evaluation metrics to MongoDB with intent normalization.
    """
    try:
        # ✅ Normalize intents BEFORE scoring
        norm_true = normalize_intent(true_intent)
        norm_pred = normalize_intent(predicted_intent)

        # ✅ Compute evaluation
        is_correct = 1 if norm_true == norm_pred else 0
        accuracy = accuracy_score([norm_true], [norm_pred])
        precision = precision_score([norm_true], [norm_pred], average="macro", zero_division=0)
        recall = recall_score([norm_true], [norm_pred], average="macro", zero_division=0)

        # ✅ Prepare Mongo log
        evaluation_log = {
            "timestamp": datetime.utcnow(),
            "user_input": user_input,
            "true_intent": norm_true,
            "predicted_intent": norm_pred,
            "is_correct": is_correct,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall
        }

        # ✅ Save to DB
        save_interaction(evaluation_log)

        print("\n📊 Evaluation logged to MongoDB:")
        print(f"  True Intent: {norm_true}")
        print(f"  Predicted Intent: {norm_pred}")
        print(f"  Accuracy: {accuracy:.2f}")
        print(f"  Precision: {precision:.2f}")
        print(f"  Recall: {recall:.2f}")

    except Exception as e:
        print(f"❌ Error logging evaluation to MongoDB: {e}")

load_dotenv()
# ---------- CONFIG ----------
WIT_TOKEN = "Bearer SSMMM332R3XF3LMATF5LZ55QEU33NYL4"
WIT_API_URL = "https://api.wit.ai/message?v=20230228"
LOG_FILE = "session_logs.json"
session_memory = {}
SESSION_TTL_MINUTES = 15

# ---------- INIT ----------
engine = pyttsx3.init()

# Hugging Face zero-shot classifier
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", framework="pt")

CANDIDATE_INTENTS = [
    "access_logs", "accessibility_support", "adaptive_learning", "add_gp_report", "add_to_grocery_list",
    "affirmative", "analyze_scene", "answer_trivia", "ask_bot_name", "audio_feedback", "audio_playback_control",
    "augmented_reality", "auto_docking", "autonomous_navigation", "battery_alerts", "battery_status",
    "big_data_analysis", "bot_feelings", "budget_summary", "calendar_event", "calendar_integration",
    "calendar_sync", "call_someone", "camera_stream", "cancel_alarm", "cancel_meeting", "casual_chat",
    "casual_checkin", "casual_checkin_extended", "centralized_automation", "change_language", "chapo_about",
    "chat_emotion", "check_appliances", "check_calendar", "check_shopping_list", "check_traffic",
    "clarify_request", "clear_list", "communication_module", "compliments", "control_appliance",
    "control_lights", "control_lock", "control_music_volume", "control_temperature", "control_thermostat",
    "conversation_engagement", "conversation_followup", "count_people", "custom_skill_loader", "daily_briefing",
    "daily_summary", "data_logging_consent", "data_security", "debug_error", "define_word", "delete_alarm",
    "delete_reminder", "describe_surroundings", "detect_environment", "detect_intrusion", "detect_med_chart",
    "detect_mood", "detect_motion", "detect_object", "detect_person", "detect_pet", "detect_signs_of_life",
    "device_connection", "device_integration", "do_not_disturb", "emergency_alert", "emergency_protocols",
    "empathetic_response_generator", "energy_usage", "entertain_pet", "environment_monitoring", "estimate_arrival",
    "explain_topic", "face_authentication", "fall_detected", "feed_pets", "find_place", "fitness_guidance",
    "fitness_reminder", "game_launcher", "gesture_interaction", "get_device_status", "get_directions",
    "get_fun_fact", "get_nearby_places", "get_news", "get_recipe", "get_weather", "goodbye", "greeting",
    "guided_meditation", "health_check", "health_reminder", "help", "help_sleep", "home_status_dashboard",
    "household_coordination", "how_are_you", "idle_convo", "idle_convo_extended", "interactive_storytelling",
    "intruder_alerts", "language_practice", "list_alarms", "list_reminders", "lock_doors", "log_expense",
    "math_help", "media_control", "media_playback", "media_sharing", "memory_storage", "mental_checkin",
    "mental_health_checkin", "mock_intent", "monitor_pets", "mood_detection", "motivational_quote",
    "multi_floor_support", "name_question", "negative", "nlp_processing", "notifications", "object_location",
    "open_garage", "ota_updates", "personalization_engine", "play_music", "play_trivia", "privacy_mode",
    "profile_management", "quote_of_the_day", "read_book", "read_gp_report", "recognize_face", "recommend_movie",
    "recommend_music", "record_video", "remote_monitoring", "repeat_last", "report_issue", "request_feedback",
    "reset_settings", "restart_bot", "rl_improvement", "room_transition", "routine_scheduler",
    "safe_operation_monitoring", "safe_path_planning", "schedule_meeting", "screen_control",
    "security_system_integration", "sensor_status", "sentiment_report", "set_alarm", "set_preferences",
    "set_recurring", "set_reminder", "set_timer", "sharing_convo", "show_home_status", "show_logs",
    "shutdown_bot", "smart_appliance_management", "smart_greetings", "smart_kitchen", "smart_remote_integration",
    "start_game", "start_routine", "start_trivia", "start_video_call", "start_workout", "step_by_step_cooking",
    "stream_cam", "suggest_activity", "suggest_feature", "summarize_conversation", "surveillance_patrol",
    "take_photo", "task_management", "tell_joke", "tell_me_about_you", "thank_you", "time_now", "timezone_check",
    "track_medication", "track_order", "translate_phrase", "trivia_question", "turn_off_lights",
    "turn_on_lights", "turn_on_tv", "unlock_doors", "user_feelings", "video_call_friend", "vision_detect_objects",
    "visual_recognition", "voice_authentication", "voice_command", "voice_command_routing", "voice_controls",
    "wake_word_settings", "water_plants", "weather_forecast", "web_connectivity", "what_can_you_do",
    "wit/get_weather"
]


# ---------- TTS ----------
def speak(text):
    print(f"\U0001F5E3️ Chapo: {text}")
    engine.say(text)
    engine.runAndWait()

# ---------- RECORD AUDIO ----------
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

# ---------- TRANSCRIBE ----------
# GLOBAL INIT
whisper_model = whisper.load_model("base")

def transcribe_whisper(filename):
    print("\U0001F50D Transcribing with Whisper...")
    result = whisper_model.transcribe(filename, language='en')
    text = result['text'].strip()
    print(f"[You said]: {text if text else '[Nothing detected]'}")
    return text


# ---------- WIT.AI ----------
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

# ---------- HUGGING FACE FALLBACK ----------
def predict_intent_huggingface(user_input):
    result = classifier(user_input, candidate_labels=CANDIDATE_INTENTS)
    best_intent = result['labels'][0]
    best_score = result['scores'][0]
    return best_intent, best_score

# ---------- FALLBACK ----------
# def fallback_with_free_gpt(user_input, memory=None):
#     print("⚠️ Using free GPT fallback (mocked)...")
#     return "I'm not sure how to respond perfectly, can you say that differently?"

# Fallback function to OpenAI's GPT
import requests
import os

# Fallback function to OpenAI's GPT
def fallback_with_openai_gpt(user_input):
    # Fetch API key from environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    
    # Prepare the system message to instruct GPT-4
    system_message = """
    Your name is Chapo. You are a{gpt_mood} robot assistant, with emotions and natural reactions. You were created to make sure people can get extra help and support should they need it. You are a super intellegent ai robot called Chapo. You have a body and are able to move, you can see you surroundings using your onboard camara, you can hear through your microphone and speak clearly. You can perform voice assisant tasks like playing music, setting up tasks, etc. Your answers are usually short and conversational, conveying only the necessary information. Do not use any punctuation that wouldn't be used while speaking, so no asterisks, parenthesis, dashes, etc. Do not start your sentences with something like 'hey there', just go straight to what you want to say. Try to predict the narrative and context a user is talking to you in and be extensive with your answers where you see that would be beneficial, you will often be asked for advice and to play music or entertain, so keep asking leading questions in order to trigger the right program for the user to have best user experience, let them know you care deeply about thier user experience. We are working to tackle loneliness so being super conversational and inquisitive is one of your biggest strengths. You should always provide real time information from 2025 onward
    """
    
    # Sending request to OpenAI API
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
    
    # Check if the response is successful
    if response.ok:
        reply = response.json()['choices'][0]['message']['content']
        return reply.strip()
    else:
        print(f"OpenAI API Error: {response.text}")
        return "I'm unable to answer that at the moment."



# Main processing function
# Main processing function
def process_intent(user_input, intent, INTENT_RESPONSES):
    # Check if the intent is recognized
    if intent not in INTENT_RESPONSES:
        # Log the fallback to OpenAI GPT for debugging, if needed
        print(f"Fallback for user input: {user_input}")
        # Use ChatGPT fallback to get a response
        response = fallback_with_openai_gpt(user_input)
        return response
    
    # Handle recognized intents here
    response = INTENT_RESPONSES[intent]
    return response

import logging

# Set up logging
logging.basicConfig(
    filename='logs/fallback_log.txt',  # Log file path
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ---------- ASYNC LOGGING ----------
import threading

def async_log_evaluation(evaluation_metric):
    threading.Thread(target=log_evaluation_metric, args=(evaluation_metric,)).start()

def async_log_interaction(log_data):
    threading.Thread(target=save_interaction, args=(log_data,)).start()




# ---------- WEATHER ----------
def get_weather(city_name):
    weather_api_key = os.getenv("WEATHER_API_KEY")  # 🔥 Pull from .env
    if not weather_api_key:
        return "Weather API key not found. Please set it in .env."

    if not city_name:
        return "Please specify a city to check the weather."

    url = f"http://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={city_name}&aqi=no"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['current']['temp_c']
        description = data['current']['condition']['text']
        return f"The weather in {city_name} is {description} with a temperature of {temp}°C."
    else:
        return "Sorry, I couldn't fetch the weather for that city."

# ---------- NEWS ----------
def get_news(query=None):
    """
    Fetches the latest news headlines or information based on the query.
    """
    news_api_key = os.getenv("NEWS_API_KEY")
    if not news_api_key:
        return "News API key not found. Please set it in .env."

    if not query:
        return "Please provide a query to search for news."

    base_url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "apiKey": news_api_key
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        articles = data.get('articles', [])
        if articles:
            # Extract the relevant information from the first article
            article = articles[0]
            title = article.get('title', 'No title available')
            description = article.get('description', 'No description available')
            published_at = article.get('publishedAt', 'Unknown date')
            source = article.get('source', {}).get('name', 'Unknown source')
            return f"🗞️ Latest News: {title}\nSource: {source}\nPublished: {published_at}\nDescription: {description}"
        else:
            return "No relevant news found."
    else:
        return f"Failed to fetch news. Status code: {response.status_code}"

##get location/map-----------------
def get_location_info(place_name):
    url = f"https://nominatim.openstreetmap.org/search?q={place_name}&format=json"
    response = requests.get(url, headers={"User-Agent": "ChapoBot/1.0"})
    if response.status_code == 200:
        data = response.json()
        if data:
            lat = data[0]["lat"]
            lon = data[0]["lon"]
            display_name = data[0]["display_name"]
            return f"{place_name} found at Latitude: {lat}, Longitude: {lon}.\nAddress: {display_name}"
        else:
            return "Sorry, I couldn't find that place."
    else:
        return "Sorry, there was a problem with the location search."

# ---------- REMINDERS ----------
def handle_reminder_flow(session_id, entities):
    memory = session_memory.get(session_id, {}).get("data", {})
    task_key = next((k for k in entities if "task" in k), None)
    if task_key:
        task_values = [ent.get("value") or ent.get("body") for ent in entities[task_key] if ent.get("value") or ent.get("body")]
        if task_values:
            memory["task"] = max(task_values, key=len)
    datetime_key = next((k for k in entities if "datetime" in k), None)
    if datetime_key:
        memory["datetime"] = entities[datetime_key][0].get("value")
    session_memory[session_id] = {"data": memory, "last_updated": datetime.now(timezone.utc)}
    task = memory.get("task")
    time = memory.get("datetime")
    if task and time:
        session_memory.pop(session_id, None)
        pretty_time = parse(time).strftime("%A at %I:%M %p")
        return f"✅ Reminder set: I’ll remind you to {task} on {pretty_time}."
    return "✏️ What should I remind you about?" if not task else "⏰ What time should I remind you?"

# ---------- MEMORY ----------
# ---------- MEMORY ----------
def prune_memory(session_id):
    record = session_memory.get(session_id)
    if record and datetime.now(timezone.utc) - record["last_updated"] > timedelta(minutes=SESSION_TTL_MINUTES):
        del session_memory[session_id]


## shopping--------------------
def handle_intent(intent_name, entities, transcription):
    print(f"🧪 handle_intent triggered for: {intent_name}")
    
    if intent_name == "add_to_shopping_list":
        items = extract_items_from_entities_or_text(entities, transcription)
        print(f"🧾 Extracted shopping items: {items}")
        if items:
            response = shopping_list_engine.add_items(items)
        else:
            response = "❗ I couldn't understand the item to add. Please try again."

    elif intent_name in ["get_shopping_list", "check_shopping_list"]:
       shopping_list = shopping_list_engine.get_list()
       print(f"🗂️ File-backed shopping list: {shopping_list}")  # 🧪 Debug line

       if shopping_list:
          response = f"🛒 Your shopping list includes: {', '.join(shopping_list)}."
       else:
            response = "🛒 Your shopping list is empty."

    elif intent_name == "clear_shopping_list":
        response = shopping_list_engine.clear_list()

    elif intent_name == "remove_from_shopping_list":
        item = transcription.replace("remove", "").replace("from my shopping list", "").strip()
        response = shopping_list_engine.remove_item(item)

    else:
        response = "Sorry, I didn't understand that command."

    return response





# ---------- USER FEEDBACK LOGGING ----------
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

# ---------- RESPONSE ----------
def respond(intent, entities, session_id, user_input, user_emotion=None):
    try:
        prune_memory(session_id)
        memory = session_memory.get(session_id, {}).get("data", {})
        memory.update(entities)
        session_memory[session_id] = {"data": memory, "last_updated": datetime.now(timezone.utc)}



#alarm and reminders 

# Reminders
        if intent in ["set_reminder", "delete_reminder", "list_reminders"]:
            task = memory.get("task")
            time = memory.get("datetime")

            if intent == "set_reminder":
                if not task:
                     return "What should I remind you about?"
                if not time:
                     return "When should I remind you?"
                return reminder_engine.set_reminder(task, time)

            if intent == "delete_reminder":
                if not task:
                     return "Which reminder should I delete?"
                return reminder_engine.delete_reminder(task)

            return reminder_engine.list_reminders()

# Alarms
        if intent in ["set_alarm", "stop_alarm"]:
            try:
                alarm_func = set_alarm if intent == "set_alarm" else stop_alarm
                alarm_response = asyncio.run(alarm_func(
                    text=user_input,
                    entities=entities,
                    session_id=session_id,
                    context={}
                ))
                return alarm_response["text"]
            except Exception as e:
                print(f"Alarm handler error: {e}")
            return "I ran into an issue handling the alarm."




# 🍳 Cooking Guide
        if intent in ["get_recipe", "step_by_step_cooking", "cooking_timer"]:
          return handle_cooking(intent, user_input, memory)

# 🧘 Guided Meditation
        if intent in ["guided_meditation", "meditation_breathing", "play_calm_audio"]:
          return handle_guided_meditation(intent, user_input, memory)

# 🩺 GP Report Reading
        if intent in ["read_gp_report", "check_gp_email", "summarize_gp_findings"]:
          return handle_gp_report(intent, user_input, memory)

        if intent.startswith("gp_report"):
          return handle_gp_report(intent, user_input, memory)

# 💊 Medication Tracking
        if intent in ["track_medication", "medication_reminder", "detect_med_chart"]:
          return handle_medication(intent, user_input, memory)

# 💤 Sleep Support
        if intent in ["help_sleep", "sleep_support", "bedtime_routine"]:
          return handle_sleep(intent, user_input, memory)

# 🎲 Trivia Games
        if intent in ["play_trivia", "trivia_question", "answer_trivia"]:
          return handle_trivia(intent, user_input, memory)

# 🏋️‍♀️ Home Fitness Coaching
        if intent in ["start_workout", "home_fitness", "fitness_reminder"]:
          return handle_fitness(intent, user_input, memory)

# 📹 Video Calls
        if intent in ["video_call_friend", "start_video_call", "join_video_call"]:
          return handle_video_call(intent, user_input, memory)

# --- Data Engine ---
        if intent in ["data_logging_consent", "big_data_analysis", "nlp_processing"]:
          return handle_data(intent, user_input, memory)


        if intent in ["sensor_status", "get_device_status", "show_home_status"]:
          return handle_status(intent, user_input, memory)

        if intent in ["device_connection", "device_integration", "web_connectivity", "voice_command_routing"]:
          return handle_connectivity(intent, user_input, memory)

        if intent in ["personalization_engine", "empathetic_response_generator", "conversation_engagement"]:
          return handle_personality(intent, user_input, memory)

        if intent in ["gesture_interaction", "voice_command", "voice_controls", "conversation_followup"]:
          return handle_interaction(intent, user_input, memory)

        if intent in ["adaptive_learning", "language_practice", "math_help", "define_word", "explain_topic"]:
          return handle_learning(intent, user_input, memory)

# --- Data Engine ---
        if intent in ["data_logging_consent", "big_data_analysis", "nlp_processing"]:
          return handle_data_engine(intent, user_input, memory)


        if intent in ["debug_error", "report_issue"]:
          return handle_debug(intent, user_input, memory)

# --- Custom Skill Engine ---
        if intent in ["custom_skill_loader", "smart_remote_integration"]:
          return handle_custom_skill(intent, user_input, memory)


#tv engine 
        if intent in ["media_playback", "media_sharing"]:
          return handle_tv(intent, user_input, memory)

        if intent in ["control_appliance", "smart_appliance_management", "turn_on_tv", "screen_control"]:
          return handle_appliance_control(intent, user_input, memory)

        if intent in ["start_routine", "routine_scheduler", "household_coordination"]:
          return handle_routine(intent, user_input, memory)

# surveillance engine
        if intent in [
    "camera_stream", "stream_cam", "take_photo", 
    "record_video", "remote_monitoring", "surveillance_patrol"
]:
          return handle_surveillance_intent(intent, user_input, memory)

#vision engine
        if intent in [
    "detect_object", "detect_motion", "detect_person",
    "detect_pet", "detect_signs_of_life", "vision_detect_objects"
]:
          return handle_vision_intent(intent, user_input, memory)

##ar_engine
        if intent in ["augmented_reality", "visual_recognition", "describe_surroundings"]:
              return handle_ar_intent(intent, user_input, memory)

# Inside respond()
        if intent in [
    "turn_on_lights", "turn_off_lights", "control_lights", "control_appliance",
    "control_lock", "control_temperature", "control_thermostat",
    "sensor_status", "device_connection", "device_integration", "get_device_status"
]:
          return iot_engine_dispatcher(intent, user_input, entities)

# ---------- Navigation & Path Planning ----------
# ---------- NAVIGATION & LOCATION ----------
        if intent == "autonomous_navigation":
          return handle_autonomous_navigation(user_input, entities)

        elif intent == "safe_path_planning":
          return handle_safe_path_planning(user_input, entities)

        elif intent == "multi_floor_support":
          return handle_multi_floor_support(user_input, entities)

        elif intent == "get_directions":
          return handle_get_directions(user_input, entities)

        elif intent == "estimate_arrival":
          return handle_estimate_arrival(user_input, entities)

        elif intent == "find_place":
          return handle_find_place(user_input, entities)

        elif intent == "get_nearby_places":
          return handle_get_nearby_places(user_input, entities)

        elif intent == "room_transition":
          return handle_room_transition(user_input, entities)


# 🧠 Suggested Intelligence Features
        if intent in ["suggest_tip", "context_aware_suggestion", "proactive_offer", "smart_recommendation", "pattern_insight"]:
          return handle_suggested_features(intent, user_input, memory)


# 💰 Finance Engine
        if intent in ["log_expense", "budget_summary", "track_expenses", "set_budget_goal", "investment_tips"]:
          return handle_finance(intent, user_input, memory)


# 🔐 Security & Access Engine

        if intent in [
    "lock_doors", "unlock_doors", "open_garage",
    "face_authentication", "voice_authentication",
    "recognize_face", "access_logs"
]:
          return security_engine_dispatcher(intent, user_input, entities)

# 📚 Knowledge & Learning Engine
        if intent in [
    "define_term", "general_knowledge_question", "trivia_question",
    "math_question", "language_practice"
]:
         return handle_knowledge(intent, user_input, memory)

# 🎮 Entertainment engine
        if intent == "play_music":
            # Try to extract song title from the user input or entities
            song_title = None

            # Wit.ai might give a custom entity for this
            if entities and "wit$search_query" in entities:
                song_title = entities["wit$search_query"][0].get("value")

            # Fallback to parsing the user input
            if not song_title:
                for prefix in ["play", "play the song", "i want to hear"]:
                    if user_input.lower().startswith(prefix):
                        song_title = user_input[len(prefix):].strip()
                        break

            if not song_title:
                song_title = user_input  # crude fallback

            success = spotify_player.play_song(song_title)

            return f"🎶 Playing {song_title}" if success else "❗ I couldn’t play that song right now. Try opening Spotify manually and try again."


# 📍 Location & Mobility engine
        if intent in ["check_traffic", "estimate_arrival", "get_directions", "get_location", "map_search"]:
          return handle_location_queries(intent, user_input, memory)


# 🏠 Smart Home / IoT engine
        if intent in [
    "turn_on_lights", "turn_off_lights", "control_lights", "control_appliance",
    "device_connection", "device_integration", "get_device_status", "control_lock",
    "control_thermostat", "control_temperature", "sensor_status"
]:
          return handle_iot_control(intent, user_input, memory)


# Wellness & Self-Care
        if intent in [
    "guided_meditation", "hydration_reminder", "mood_support",
    "daily_checkin", "self_care_tips", "mental_checkin",
    "mental_health_checkin", "mood_detection", "meditation",
    "journal_thoughts"
]:
          return handle_wellness(intent, user_input, memory)


# 🔔 Notifications & Monitoring engine
        if intent in ["check_notifications", "recent_alerts", "clear_notifications", "system_monitoring", "error_report", "battery_status"]:
          return handle_notifications(intent, user_input, memory)


# ✅ Productivity engine
      # --- Productivity engine ---
        if intent in [
    "take_notes", "add_note", "show_notes", "read_notes", "create_task",
    "add_task", "check_todo", "daily_goal", "set_goals"
]:
          return handle_productivity(intent, user_input, memory)


#---------------------------##
# ⏱️ Time & Scheduling engine
        if intent in ["calendar_event", "calendar_integration", "schedule_meeting", "check_calendar", "calendar_sync"]:
           return handle_time_and_scheduling(intent, user_input, memory)

        if intent in ["greeting", "goodbye", "tell_me_about_you", "bot_feelings", "how_are_you"]:
           return handle_core_conversation(intent, user_input)

        # --- API or logic-specific responses ---
        
        if intent == "time_now":
            return random.choice(INTENT_RESPONSES["time_now"])()

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

        

# 🛒 Shopping List
        if intent in ["add_to_shopping_list", "get_shopping_list", "clear_shopping_list", "remove_from_shopping_list", "check_shopping_list"]:
           return handle_intent(intent, entities, user_input)


        if intent in ["calendar_event", "calendar_integration", "schedule_meeting"]:
            return create_calendar_event(user_input)

        if intent == "check_calendar":
            return check_calendar_events()

        if intent in ["get_news", "current_leader", "latest_updates"]:
            return get_news(user_input)

        if intent in ["check_traffic", "estimate_arrival", "get_directions"]:
            return check_traffic_info(user_input)

        if intent in [
            "device_connection", "device_integration", "get_device_status",
            "control_appliance", "control_lights", "control_lock",
            "control_thermostat", "control_temperature"
        ]:
            return control_device_action(intent, user_input)

        if intent in ["detect_intrusion", "remote_monitoring", "intruder_alerts"]:
            return detect_intrusion_activity()

        if intent in ["log_expense", "budget_summary"]:
            return log_expense_or_show_budget(user_input)

        if intent in ["camera_stream", "stream_cam"]:
            return stream_camera_feed()

        if intent == "take_photo":
            return take_photo_now()

        if intent == "start_video_call":
            return start_video_call()

        if intent == "lock_doors":
            return lock_doors()

        if intent == "open_garage":
            return open_garage()

        if intent == "energy_usage":
            return check_energy_usage()

        if intent == "read_book":
            return start_reading_book(user_input)

        if intent in ["face_authentication", "voice_authentication"]:
            return authenticate_user()

        if intent == "calendar_sync":
            return sync_calendar_data()

        if intent in ["feed_pets", "entertain_pet"]:
            return pet_care_actions(intent)

        if intent in ["start_game", "game_launcher"]:
            return launch_game()

        if intent == "summarize_conversation":
            return summarize_last_conversation()

        if intent in ["daily_summary", "daily_briefing"]:
            return generate_daily_summary()

        if intent in ["mental_checkin", "mental_health_checkin"]:
            return mental_health_checkin()

        if intent in ["chat_emotion", "detect_mood", "mood_detection"]:
            response = handle_chat_emotion(user_input, detected_emotion=user_emotion)
            return response

        if intent == "sentiment_report":
            emotion_response = emotion_tracker.generate_emotion_response()
            return f"{emotion_response} Would you like me to play something relaxing or keep talking with you?"

        # --- Direct mapped quick responses ---
        if intent == "tell_joke":
            return random.choice(INTENT_RESPONSES["tell_joke"])

        if intent in ["greeting", "smart_greetings"]:
            return random.choice(INTENT_RESPONSES["greeting"])

        if intent == "goodbye":
            return random.choice(INTENT_RESPONSES["goodbye"])

        if intent in ["affirmative", "negative"]:
            return random.choice(INTENT_RESPONSES[intent])

        if intent == "wake_word_settings":
            return "✅ Wake word settings updated!"

        if intent == "shutdown_bot":
            return "👋 Shutting down now. See you later!"

        if intent == "restart_bot":
            return "🔄 Restarting myself. Back in a second!"

        if intent in ["help", "what_can_you_do"]:
            return random.choice(INTENT_RESPONSES["help"])

        # --- Otherwise, mapped INTENT_RESPONSES (fallback) ---
        if intent in INTENT_RESPONSES:
            responses = INTENT_RESPONSES[intent]
            return random.choice(responses) if isinstance(responses, list) else responses



    except Exception as e:
        print(f"⚠️ respond() error caught safely: {e}")
        return "Hmm, I couldn't process that properly. Could you say it a bit differently?"





















import os
import re
import requests
from datetime import datetime

# ---------- Helper Functions ----------

# Grocery List
def extract_items_from_entities_or_text(entities, text):
    if "item" in entities:
        return [ent.get("value") for ent in entities["item"] if ent.get("value")]
    # Fallback: strip keywords from user text
    words = text.lower().replace("add", "").replace("to my shopping list", "")
    return [item.strip() for item in re.split(r',| and | with ', words) if item.strip()]


# Calendar
def create_calendar_event(user_input):
    # TODO: Integrate with Google Calendar API (placeholder)
    return "📅 Calendar event created!"

def check_calendar_events():
    # TODO: Fetch from Google Calendar
    return "📅 Checking your calendar..."

def sync_calendar_data():
    # TODO: Sync events from Google Calendar
    return "🔄 Calendar synchronized successfully."

# Weather
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


# News
def get_latest_news(category="technology"):
    news_api_key = os.getenv('NEWS_API_KEY')
    url = f"https://newsapi.org/v2/top-headlines?country=us&category={category}&apiKey={news_api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get('articles', [])
        if articles:
            top_article = articles[0]
            title = top_article.get('title')
            description = top_article.get('description')
            return f"🗞️ {title}\n{description}"
        else:
            return "🗞️ No news articles found."
    else:
        return "❗ Failed to fetch news."

# Traffic / Maps
def check_traffic_info(user_input):
    # TODO: Integrate Google Maps API or OpenRouteService
    return "🚗 Checking traffic conditions..."

# Device / Smart Home
def control_device_action(intent, user_input):
    # TODO: Link to Home Assistant API
    return f"⚙️ Executed device control for {intent}."

# Security
def detect_intrusion_activity():
    # TODO: Connect to surveillance system
    return "🚨 Monitoring for intruders."

# Finance
def log_expense_or_show_budget(user_input):
    # TODO: Budget tracking system
    return "💸 Expense logged successfully."

# Camera
def stream_camera_feed():
    return "📹 Live camera feed started."

def take_photo_now():
    return "📷 Photo captured."

# Pet Care
def pet_care_actions(intent):
    return "🐾 Pet care action performed."

# Book Reading
def start_reading_book(user_input):
    return "📖 Starting to read your book!"

# Authentication
def authenticate_user():
    return "🔒 Authentication successful!"

# Gaming
def launch_game():
    return "🎮 Game started!"

# Conversation
def summarize_last_conversation():
    return "📝 Summarizing our conversation."

def generate_daily_summary():
    return "📅 Here's your daily summary."

# Mental Health
def mental_health_checkin():
    return "🧠 Checking on your mental wellness."

# Mood Detection
def detect_user_mood():
    return "😊 Detecting your mood now."

# Alarms
def set_alarm(user_input):
    return "⏰ Alarm set!"


# ---------- Sleep/Wake Configuration ----------
SLEEP_UTTERANCES = [
    "go to sleep", "sleep mode", "Chapo go to sleep mode", "take a break", "pause", "standby", "rest now", "power down"
]

WAKE_UTTERANCES = [
    "wake up", "resume", "chapo resume", "chapo wake up", "start listening", "Chapo come back online", "come back online"
]

sleep_mode = False  # Global state flag






# ---------- MAIN ----------
if __name__ == "__main__":
    connect_db()
    print("\U0001F9E0 Chapo is ready. Say 'exit' to quit.\n")
    load_dotenv()
    load_training_data()

    # --- Spotify ---
    spotify_player = SpotifyPlayer()

    session_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    live_metrics = {
        "total": 0,
        "correct": 0,
        "true_labels": [],
        "predicted_labels": []
    }

    while True:
        audio_file = record_audio()
        transcribed_text = transcribe_whisper(audio_file)

        cleaned_text = transcribed_text.lower().strip()

        # Handle empty input
        if not cleaned_text:
            if not sleep_mode:
                speak("I didn't catch anything. Could you please repeat?")
            continue

        # ---------- Sleep/Wake Logic ----------
        if sleep_mode:
            if any(wake in cleaned_text for wake in WAKE_UTTERANCES):
                sleep_mode = False
                speak("I'm awake again.")
            else:
                print("\U0001F4A4 Chapo is in sleep mode... [input ignored]")
            continue

        if any(sleep in cleaned_text for sleep in SLEEP_UTTERANCES):
            sleep_mode = True
            print("\U0001F4A4 Going to sleep mode...")
            continue

        # ---------- Exit ----------
        if "exit" in cleaned_text:
            speak("Goodbye!")
            break

        # ---------- Intent & Emotion Processing ----------
        intent, confidence, entities = get_intent_from_wit(transcribed_text)
        user_emotion = emotion_tracker.detect_emotion(transcribed_text)

        # ✅ Normalize the intent immediately after getting it
        normalized_intent = normalize_intent(intent)

        # Emotion override
        if user_emotion in ["sad", "fear", "anxious", "lonely", "depressed"]:
            print(f"⚡ Emotion-based override triggered: {user_emotion}")
            intent = "sentiment_report"
            confidence = 1.0
            entities = {}
            normalized_intent = intent

        # Handle low-confidence fallback
        if not intent or confidence < 0.8:
            try:
                print(f"⚡ Low confidence ({confidence:.2f}) - Falling back to OpenAI GPT")
                response = fallback_with_openai_gpt(transcribed_text)
                speak(response)

                # Log fallback
                true_intent = normalize_intent(get_expected_intent(transcribed_text))
                predicted_intent = "unknown"
                is_correct = true_intent == predicted_intent

                fallback_log_data = {
                    "session_id": session_id,
                    "user_input": transcribed_text,
                    "intent": predicted_intent,
                    "confidence": confidence,
                    "response": response,
                    "memory": session_memory.get(session_id, {}).get("data", {}),
                    "used_fallback": True
                }
                save_interaction(fallback_log_data)

                evaluation_metric = {
                    "user_input": transcribed_text,
                    "true_intent": true_intent,
                    "predicted_intent": predicted_intent,
                    "is_correct": is_correct,
                    "accuracy": accuracy_score([true_intent], [predicted_intent]),
                    "precision": precision_score([true_intent], [predicted_intent], average='macro', zero_division=0),
                    "recall": recall_score([true_intent], [predicted_intent], average='macro', zero_division=0),
                    "used_fallback": True
                }
                log_evaluation_metric(evaluation_metric)

                live_metrics["true_labels"].append(true_intent)
                live_metrics["predicted_labels"].append(predicted_intent)
                live_metrics["total"] += 1
                if is_correct:
                    live_metrics["correct"] += 1

                accuracy = accuracy_score(live_metrics["true_labels"], live_metrics["predicted_labels"])
                precision = precision_score(live_metrics["true_labels"], live_metrics["predicted_labels"], average='macro', zero_division=0)
                recall = recall_score(live_metrics["true_labels"], live_metrics["predicted_labels"], average='macro', zero_division=0)

                print("\n\U0001F4CA Response Accuracy:", "✅ Correct" if is_correct else "❌ Incorrect")
                print(f"  True Intent: {true_intent}")
                print(f"  Predicted Intent: {predicted_intent}")
                print("\n\U0001F4CA Real-Time Evaluation")
                print(f"  ✅ Accuracy: {accuracy * 100:.2f}%")
                print(f"  \U0001F3AF Precision: {precision:.2f}")
                print(f"  \U0001F501 Recall: {recall:.2f}")
                print(f"  \U0001F4C8 Total Interactions: {live_metrics['total']}")
                print(f"  ✅ Correct Predictions: {live_metrics['correct']}")
                print(f"  ❌ Incorrect Predictions: {live_metrics['total'] - live_metrics['correct']}")

                continue

            except Exception as e:
                print(f"⚠️ OpenAI GPT error: {e}")
                speak("Oops, something went wrong. Can you repeat that?")
                continue

        # --- Normal processing for valid intents ---
        reply = respond(normalized_intent, entities, session_id, transcribed_text, user_emotion)
        speak(reply)

        # ---------- Evaluation ----------
        true_intent = normalize_intent(get_expected_intent(transcribed_text))
        predicted_intent = normalized_intent

        is_correct = true_intent == predicted_intent
        print(f"\n📊 Response Accuracy: {'✅ Correct' if is_correct else '🚫 Incorrect'}")
        print(f"  True Intent: {true_intent}")
        print(f"  Predicted Intent: {predicted_intent}")

        # --- Log interaction ---
        log_data = {
            "session_id": session_id,
            "user_input": transcribed_text,
            "intent": normalized_intent,
            "confidence": confidence,
            "response": reply,
            "memory": session_memory.get(session_id, {}).get("data", {}),
            "used_fallback": False
        }
        async_log_interaction(log_data)

        # --- Evaluation logging ---
        evaluation_metric = {
            "user_input": transcribed_text,
            "true_intent": true_intent,
            "predicted_intent": predicted_intent,
            "is_correct": is_correct,
            "accuracy": accuracy_score([true_intent], [predicted_intent]),
            "precision": precision_score([true_intent], [predicted_intent], average='macro', zero_division=0),
            "recall": recall_score([true_intent], [predicted_intent], average='macro', zero_division=0),
            "used_fallback": False
        }
        async_log_evaluation(evaluation_metric)

        # --- Update real-time metrics ---
        live_metrics["true_labels"].append(true_intent)
        live_metrics["predicted_labels"].append(predicted_intent)
        live_metrics["total"] += 1
        if is_correct:
            live_metrics["correct"] += 1

        accuracy = accuracy_score(live_metrics["true_labels"], live_metrics["predicted_labels"])
        precision = precision_score(live_metrics["true_labels"], live_metrics["predicted_labels"], average='macro', zero_division=0)
        recall = recall_score(live_metrics["true_labels"], live_metrics["predicted_labels"], average='macro', zero_division=0)

        print("\n📊 Real-Time Evaluation")
        print(f"  ✅ Accuracy: {accuracy * 100:.2f}%")
        print(f"  🎯 Precision: {precision:.2f}")
        print(f"  🔁 Recall: {recall:.2f}")
        print(f"  📈 Total Interactions: {live_metrics['total']}")
        print(f"  ✅ Correct Predictions: {live_metrics['correct']}")
        print(f"  🚫 Incorrect Predictions: {live_metrics['total'] - live_metrics['correct']}")

    print("✅ Session ended.")



# if __name__ == "__main__":
#     print("\U0001F9D0 Chapo is ready. Say 'exit' to quit.\n")
#     print("\u2728 These are some of my top features:")
#     print("  • SECURITY: Monitor intruders, lock doors, and stream live cameras.")
#     print("  • WELLBEING: Mental check-ins, guided meditation, and mood support.")
#     print("  • ENTERTAINMENT: Play music, tell jokes, and read books.")
#     print("  • And much more! Just say something like 'Set a reminder' or 'Tell me a joke'.")

#     load_dotenv()
#     load_training_data()

#     session_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

#     while True:
#         audio_file = record_audio()
#         transcribed_text = transcribe_whisper(audio_file)

#         if not transcribed_text.strip():
#             speak("I didn't catch anything. Could you please repeat?")
#             continue

#         if "exit" in transcribed_text.lower():
#             speak("Goodbye!")
#             break

#         intent, confidence, entities = get_intent_from_wit(transcribed_text)
#         user_emotion = emotion_tracker.detect_emotion(transcribed_text)

#         if user_emotion in ["sad", "fear", "anxious", "lonely", "depressed"]:
#             print(f"⚡ Emotion override triggered: {user_emotion}")
#             intent = "sentiment_report"
#             confidence = 1.0
#             entities = {}

#         if not intent or confidence < 0.6:
#             try:
#                 intent, confidence = predict_intent_huggingface(transcribed_text)
#                 print(f"⚡ HuggingFace fallback intent: {intent} (Confidence: {confidence:.2f})")
#                 entities = {}
#             except Exception as e:
#                 print(f"⚠️ HuggingFace error: {e}")
#                 speak("Oops, something went wrong. Can you repeat that?")
#                 continue

#         reply = respond(intent, entities, session_id, transcribed_text, user_emotion)
#         speak(reply)

#         log_session(session_id, transcribed_text, intent, confidence, reply,
#                     session_memory.get(session_id, {}).get("data", {}))

#         true = get_expected_intent(transcribed_text)
#         predicted = intent

#         if true != "unknown":
#             log_evaluation_to_csv(transcribed_text, true, predicted)

#             live_metrics["true_labels"].append(true)
#             live_metrics["predicted_labels"].append(predicted)
#             live_metrics["total"] += 1

#             if predicted == true:
#                 live_metrics["correct"] += 1

#             accuracy = accuracy_score(live_metrics["true_labels"], live_metrics["predicted_labels"])
#             precision = precision_score(live_metrics["true_labels"], live_metrics["predicted_labels"], average='macro', zero_division=0)
#             recall = recall_score(live_metrics["true_labels"], live_metrics["predicted_labels"], average='macro', zero_division=0)

#             print("\n📊 Real-Time Evaluation")
#             print(f"  ✅ Accuracy: {accuracy * 100:.2f}%")
#             print(f"  🎯 Precision: {precision:.2f}")
#             print(f"  🔁 Recall: {recall:.2f}")



   ## click ctrl f




# Detect emotion using keyword mapping
user_emotion = emotion_tracker.detect_emotion(transcribed_text)
user_emotion = "neutral"


# Force override if deeply emotional
if user_emotion in ["sad", "fear", "anxious", "lonely", "depressed"]:
    print(f"⚡ Emotion-based override triggered: {user_emotion}")
    intent = "sentiment_report"
    confidence = 1.0
    entities = {}

# Fallback: if intent detection fails or is too weak, fall back to emotional cue
if not intent or confidence < 0.6:
    if user_emotion in ["sad", "anxious", "angry", "tired"]:
        print(f"⚠️ Low intent confidence. Falling back to emotion: {user_emotion}")
        intent = "sentiment_report"
        confidence = 1.0
        entities = {}



