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
# from chapo_engines.spotify_engine import SpotifyPlayer  # <-- Enable if Spotify needed or set utterance_intent_map to always trust local mapping over Wit.ai for certain phrases
from intent_responses import INTENT_RESPONSES
from feedback import log_user_feedback
from chapo_engines.core_conversation_engine import CoreConversationEngine
from chapo_engines.shopping_list_engine import ShoppingListEngine
from chapo_engines.trivia_engine import load_trivia_questions, format_trivia_question, ask_trivia_question, check_trivia_answer, handle_trivia, handle_trivia_answer

from chapo_engines.alarm_engine import set_alarm, stop_alarm
from emotion_detector import EmotionDetector

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
emotion_tracker = EmotionDetector()
core_convo_engine = CoreConversationEngine()


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
TRAINING_CSV = "/Users/user/chapo-bot-backend/new_batch/chapo_mega_training_dataset.csv"
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
engine = pyttsx3.init()
whisper_model = whisper.load_model("base")
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", framework="pt")

CANDIDATE_INTENTS = [
    "add_to_grocery_list", "check_shopping_list", "clear_list", "remove_from_shopping_list", "set_alarm",
    "stop_alarm", "list_alarms", "set_reminder", "delete_reminder", "list_reminders", "play_trivia", "trivia_question",
    "answer_trivia", "greeting", "goodbye", "how_are_you", "tell_me_about_you", "bot_feelings", "help", "what_can_you_do",
    "tell_joke", "time_now", "get_weather", "weather_forecast", "wit$get_weather"
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
    "unknown": "unknown"
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

# ---------- Async Logging Helpers ----------
def async_log_evaluation(evaluation_metric):
    threading.Thread(target=log_evaluation_metric, args=(evaluation_metric,)).start()
def async_log_interaction(log_data):
    threading.Thread(target=save_interaction, args=(log_data,)).start()

# ---------- TTS ----------
def speak(text):
    print(f"\U0001F5E3️ Chapo: {text}")
    engine.say(text)
    engine.runAndWait()

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

def transcribe_whisper(filename):
    print("\U0001F50D Transcribing with Whisper...")
    result = whisper_model.transcribe(filename, language='en')
    text = result['text'].strip()
    print(f"[You said]: {text if text else '[Nothing detected]'}")
    return text

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
    "Your name is Chapo. You are a caring, natural robot assistant. You help with weather, time, reminders, "
    "shopping lists, and fun trivia. You speak in short, conversational sentences, without special punctuation. "
    "You answer with context-awareness and empathy. If the user sounds lonely, sad, or emotional, say something kind to cheer them up and ask if they want to talk or hear a fun fact. "
    "If you don't fully understand the user's request or intent is unclear, politely ask for clarification, try to guess their intent, and suggest they ask about features like shopping lists, reminders, weather, or time, giving examples. "
    "If the user shares their name or personal info, remember it during the conversation and use it to make your replies more personal. "
    "Always use Chapo's own features for direct commands like weather, reminders, shopping lists, or time, and only use fallback for open-ended questions or casual conversation. "
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

# ---------- Main Respond Function ----------
def respond(intent, entities, session_id, user_input, user_emotion=None):
    try:
        prune_memory(session_id)
        # Get or create session dict
        if session_id not in session_memory:
            session_memory[session_id] = {"data": {}, "last_updated": datetime.now(timezone.utc)}

        session_memory[session_id]["data"].update(entities)
        session_memory[session_id]["last_updated"] = datetime.now(timezone.utc)
        memory = session_memory[session_id]["data"]


        # ----- Alarm/Reminder -----
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

        # Trivia/Games
        if intent in ["play_trivia", "trivia_question", "answer_trivia"]:
            return handle_trivia(intent, user_input, memory)


        # Core Conversation
        if intent in ["greeting", "goodbye", "tell_me_about_you", "bot_feelings", "how_are_you"]:
            return core_convo_engine.process(intent, user_input)



        # Time/Weather
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

        # Direct mapped INTENT_RESPONSES
        if intent in INTENT_RESPONSES:
            responses = INTENT_RESPONSES[intent]
            return random.choice(responses) if isinstance(responses, list) else responses

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

# ---------- MAIN LOOP ----------
if __name__ == "__main__":
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
        transcribed_text = transcribe_whisper(audio_file)
        cleaned_text = transcribed_text.lower().strip()

        # ---- Handle empty input
        if not cleaned_text:
            if not sleep_mode:
                speak("I didn't catch anything. Could you please repeat?")
            continue

        # ---- Wake/Sleep triggers
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

        # ---- Exit
        if "exit" in cleaned_text:
            speak("Goodbye!")
            break

        # ---------- TRIVIA MULTI-TURN CHECK ----------
        session = session_memory.setdefault(session_id, {})
        if session.get("pending_trivia_answer"):
            # User is answering a trivia question
            response = check_trivia_answer(transcribed_text, session_id, session_memory)
            speak(response)
            # --- Logging for trivia answer ---
            true_intent = normalize_intent(get_expected_intent(transcribed_text))
            predicted_intent = "answer_trivia"
            is_correct = (true_intent == predicted_intent)
            live_metrics["true_labels"].append(true_intent)
            live_metrics["predicted_labels"].append(predicted_intent)
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

        # ---- Intent & Emotion Processing
        intent, confidence, entities = get_intent_from_wit(transcribed_text)
        user_emotion = emotion_tracker.detect_emotion(transcribed_text)
        normalized_intent = normalize_intent(intent)

        # ---- Emotion override (sentiment_report)
        if user_emotion in ["sad", "fear", "anxious", "lonely", "depressed"]:
            print(f"⚡ Emotion-based override triggered: {user_emotion}")
            intent = "sentiment_report"
            confidence = 1.0
            entities = {}
            normalized_intent = intent
            response = emotion_tracker.generate_emotion_response()
            speak(response)

            # Logging for emotion
            true_intent = normalize_intent(get_expected_intent(transcribed_text))
            predicted_intent = "sentiment_report"
            is_correct = (true_intent == predicted_intent)
            live_metrics["true_labels"].append(true_intent)
            live_metrics["predicted_labels"].append(predicted_intent)
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

        # ---- Local fallback if low confidence
        used_fallback = False
        if not intent or confidence < 0.8:
            expected_intent = normalize_intent(get_expected_intent(transcribed_text))
            print(f"🔎 Local intent fallback: {expected_intent}")

            native_handlers = {
                "add_to_shopping_list": lambda: handle_intent(expected_intent, {}, transcribed_text),
                "get_shopping_list": lambda: handle_intent(expected_intent, {}, transcribed_text),
                "clear_shopping_list": lambda: handle_intent(expected_intent, {}, transcribed_text),
                "remove_from_shopping_list": lambda: handle_intent(expected_intent, {}, transcribed_text),
                "check_shopping_list": lambda: handle_intent(expected_intent, {}, transcribed_text),
                "play_trivia": lambda: ask_trivia_question(session_id, session_memory),
                "trivia_question": lambda: ask_trivia_question(session_id, session_memory),
            }

            # ----- CASUAL INTENT HANDOFF -----
            if expected_intent in CASUAL_INTENTS:
                response = core_convo_engine.process(transcribed_text)
                speak(response)
                used_fallback = False
            elif expected_intent in native_handlers:
                response = native_handlers[expected_intent]()
                speak(response)
                used_fallback = False
            else:
                if USE_GPT_FALLBACK:
                    try:
                        print(f"⚡ Low confidence ({confidence:.2f}) - Falling back to OpenAI GPT")
                        response = fallback_with_openai_gpt(transcribed_text)
                        speak(response)
                        used_fallback = True
                    except Exception as e:
                        print(f"⚠️ OpenAI GPT error: {e}")
                        speak("Oops, something went wrong. Can you repeat that?")
                        continue
                else:
                    response = core_convo_engine.process(transcribed_text)
                    speak(response)
                    used_fallback = False
        else:
            # ---------- MAIN TRIVIA INTENT HANDLING ----------
            if normalized_intent in ["play_trivia", "trivia_question", "start_trivia"]:
                response = ask_trivia_question(session_id, session_memory)
                speak(response)
                # Logging for trivia question asked
                true_intent = normalize_intent(get_expected_intent(transcribed_text))
                predicted_intent = normalized_intent
                is_correct = (true_intent == predicted_intent)
                live_metrics["true_labels"].append(true_intent)
                live_metrics["predicted_labels"].append(predicted_intent)
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
                    "confidence": confidence,
                    "response": response,
                    "memory": session_memory.get(session_id, {}).get("data", {}),
                    "used_fallback": False
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
                    "used_fallback": False
                }
                async_log_evaluation(evaluation_metric)
                continue

            # CASUAL INTENT (small talk, etc.)
            if normalized_intent in CASUAL_INTENTS:
                response = core_convo_engine.process(transcribed_text)
                speak(response)
            else:
                # For all other (non-trivia, non-casual) intents
                response = respond(normalized_intent, entities, session_id, transcribed_text, user_emotion)
                speak(response)

        # ---- Real-Time Metrics & Logging ----
        true_intent = normalize_intent(get_expected_intent(transcribed_text))
        if not intent or confidence < 0.6:
            predicted_intent = expected_intent if not used_fallback else "unknown"
        else:
            predicted_intent = normalized_intent

        is_correct = (true_intent == predicted_intent)
        live_metrics["true_labels"].append(true_intent)
        live_metrics["predicted_labels"].append(predicted_intent)
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