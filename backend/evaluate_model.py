# === Imports === 
import os
import json
import requests
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    confusion_matrix,
    classification_report
)
from transformers import pipeline

# === Load environment variables ===
load_dotenv()  # Loads .env file for API tokens
WIT_TOKEN = os.getenv("WIT_TOKEN")  # Wit.ai API key
WIT_API_URL = "https://api.wit.ai/message?v=20230228"  # Wit.ai API endpoint

# === Hugging Face classifier setup ===
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", framework="pt")
# This pipeline is used for fallback intent prediction

# === Candidate intents ===
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

# === Intent normalization helper ===
def normalize_intent(intent):
    # Returns lowercase intent string with Wit.ai prefix removed, or "unknown" for empty/null
    if not intent:
        return "unknown"
    intent = intent.strip().lower()
    if intent.startswith("wit$"):
        return intent.split("$")[-1]
    return intent

# === Wit.ai intent detection ===
def get_intent_from_wit(text):
    # Sends utterance to Wit.ai, returns (intent, confidence, entities)
    if not text:
        return None, 0.0, {}

    headers = {"Authorization": WIT_TOKEN}
    params = {"q": text}

    try:
        response = requests.get(WIT_API_URL, headers=headers, params=params)
        if not response.ok:
            print("❌ Wit.ai error:", response.text)
            return None, 0.0, {}

        data = response.json()
        intents = data.get("intents", [])
        entities = data.get("entities", {})

        if intents:
            top_intent = intents[0]["name"]
            confidence = intents[0]["confidence"]
            return top_intent, confidence, entities

    except Exception as e:
        print(f"⚠️ Error calling Wit.ai: {e}")

    return None, 0.0, {}

# === Hugging Face fallback intent detection ===
def predict_intent_huggingface(user_input):
    # Uses HF zero-shot model for fallback intent detection, returns (intent, score)
    result = classifier(user_input, candidate_labels=CANDIDATE_INTENTS)
    best_intent = result['labels'][0]
    best_score = result['scores'][0]
    return best_intent, best_score

# === Load dataset ===
# Read CSV with utterances and true intents
df = pd.read_csv(
    r"/Users/user/chapo-bot-backend/new_batch/chapo_mega_training_dataset.csv"
)
df = df.dropna(subset=["uttrance", "intent"])  # Remove rows missing utterance/intent
df["intent"] = df["intent"].apply(normalize_intent)  # Normalize all intent labels

# === Evaluation tracking ===
true_labels = []       # True intents from CSV
predicted_labels = []  # Model-predicted intents

# === Intent evaluation ===
for _, row in tqdm(df.iterrows(), total=len(df), desc="Evaluating"):
    user_input = row["uttrance"]         # Utterance text
    true_intent = row["intent"]          # Ground-truth intent

    # Try Wit.ai first
    intent, confidence, _ = get_intent_from_wit(user_input)

    # Fallback to Hugging Face if Wit fails or is low confidence
    if not intent or confidence < 0.6:
        try:
            intent, confidence = predict_intent_huggingface(user_input)
        except Exception:
            intent = "unknown"

    predicted_intent = normalize_intent(intent)  # Standardize intent format

    # Store for metric calculation
    true_labels.append(true_intent)
    predicted_labels.append(predicted_intent)

# === Metric Reporting ===
print("\n📊 Evaluation Results")
print(f"✅ Accuracy: {accuracy_score(true_labels, predicted_labels):.4f}")
print(f"✅ Precision (macro): {precision_score(true_labels, predicted_labels, average='macro', zero_division=0):.4f}")
print(f"✅ Recall (macro): {recall_score(true_labels, predicted_labels, average='macro', zero_division=0):.4f}")

# === Confusion Matrix ===
print("\n✅ Confusion Matrix:\n", confusion_matrix(true_labels, predicted_labels))

# === Detailed Classification Report ===
print("\n✅ Classification Report:\n", classification_report(true_labels, predicted_labels, zero_division=0))

# === Save Misclassified Samples ===
# Find all misclassified utterances for manual analysis
misclassified = []
for i in range(len(true_labels)):
    if true_labels[i] != predicted_labels[i]:
        misclassified.append({
            "uttrance": df.iloc[i]["uttrance"],
            "true_intent": true_labels[i],
            "predicted_intent": predicted_labels[i]
        })

# Save misclassified examples to CSV for review
misclassified_df = pd.DataFrame(misclassified)
misclassified_df.to_csv("misclassified_intents.csv", index=False)

print(f"\n🔍 Saved {len(misclassified)} misclassified samples to 'misclassified_intents.csv'")
