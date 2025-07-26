import random
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import unicodedata
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Clean up unicode text
def sanitize_unicode(text):
    replacements = {
        '–': '-', '—': '-',  # dashes
        '‘': "'", '’': "'",  # quotes
        '“': '"', '”': '"',
        '\u00a0': ' ',       # non-breaking space
    }
    for orig, replacement in replacements.items():
        text = text.replace(orig, replacement)
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

class FitnessEngine:
    def __init__(self):
        self.nutritionix_app_id = sanitize_unicode(os.getenv("NUTRITIONIX_APP_ID", "").strip())
        self.nutritionix_api_key = sanitize_unicode(os.getenv("NUTRITIONIX_API_KEY", "").strip())
        self.active_sessions = {}

        self.workouts = {
            "stretch": [
                "Neck rolls for 30 seconds.",
                "Shoulder rolls for 30 seconds.",
                "Side stretches for 1 minute.",
                "Hamstring stretch for 30 seconds each leg."
            ],
            "cardio": [
                "Jumping jacks - 1 minute.",
                "High knees - 30 seconds.",
                "Burpees - 10 reps.",
                "Mountain climbers - 45 seconds."
            ],
            "strength": [
                "Push-ups - 10 reps.",
                "Bodyweight squats - 15 reps.",
                "Plank - Hold for 1 minute.",
                "Lunges - 10 each leg."
            ]
        }

        self.fitness_tips = [
            "Hydrate regularly throughout your workout.",
            "Focus on form, not speed.",
            "A little progress each day adds up to big results.",
            "Don't skip your warm-up or cool-down."
        ]

    def start_structured_workout(self, session_id):
        now = datetime.now().strftime("%I:%M %p")
        self.active_sessions[session_id] = {"started_at": now}

        plan = [
            random.choice(self.workouts["stretch"]),
            random.choice(self.workouts["cardio"]),
            random.choice(self.workouts["strength"])
        ]

        return (
            f"🏋️ Starting your workout ({now}):\n"
            f"1. {plan[0]}\n2. {plan[1]}\n3. {plan[2]}\n"
            "Let me know when you're done to log this session."
        )

    def log_structured_workout(self, session_id):
        session = self.active_sessions.pop(session_id, None)
        if session:
            return f"✅ Great job! Workout started at {session['started_at']} is now logged. 💪"
        else:
            return "I didn’t find an active workout to log. Say 'Start a workout' first."

    def logout_user(self, user_id):
        self.active_sessions.pop(user_id, None)  # Remove workout session
        return f"👋 You've been logged out, {user_id}. See you next time!"

    def suggest_workout(self):
        all_exercises = self.workouts["stretch"] + self.workouts["cardio"] + self.workouts["strength"]
        return "Try this one today: " + random.choice(all_exercises)

    def get_fitness_tip(self):
        return random.choice(self.fitness_tips)

    def get_calorie_info(self, food_item):
        if not food_item:
            return "Please tell me what food item you're asking about."

        food_item = sanitize_unicode(str(food_item))
        print(f"[SANITIZED FOOD ITEM]: {food_item}")

        url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
        headers = {
            "x-app-id": self.nutritionix_app_id,
            "x-app-key": self.nutritionix_api_key,
            "Content-Type": "application/json"
        }
        payload = {"query": food_item}

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if not data.get("foods"):
                return "I couldn’t find that in the database."

            food = data["foods"][0]
            name = sanitize_unicode(food.get("food_name", "food"))
            calories = food.get("nf_calories", 0)
            return f"🍽️ {name.title()} has approximately {round(calories)} calories."

        except Exception as e:
            logger.error(f"[Nutritionix error]: {e}", exc_info=True)
            return "❌ Sorry, I couldn’t fetch the calorie info right now."
