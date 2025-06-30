# chapo_engines/calendar_auth.py

import os
import json
import time
import requests
from dotenv import load_dotenv
from pathlib import Path
from chapo_engines.tts_util import speak
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

load_dotenv()

# File to store tokens
GOOGLE_TOKEN_FILE = Path.home() / "chapo_token.json"

# Scopes required for Google Calendar
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Load from environment
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Google endpoints
DEVICE_AUTH_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"

def get_google_calendar_service():
    # ✅ Step 1: Load token if it exists
    if GOOGLE_TOKEN_FILE.exists():
        with open(GOOGLE_TOKEN_FILE, "r") as token_file:
            token_data = json.load(token_file)
            if not is_token_expired(token_data):
                return build_calendar_service(token_data)
            else:
                refresh_token = token_data.get("refresh_token")
                if refresh_token:
                    token_data = refresh_access_token(refresh_token)
                    if token_data:
                        return build_calendar_service(token_data)

    # 🟡 Step 2: Start Device OAuth Flow
    speak("Initiating calendar connection...")

    device_payload = {
        "client_id": GOOGLE_CLIENT_ID,
        "scope": " ".join(SCOPES)
    }

    response = requests.post(DEVICE_AUTH_URL, data=device_payload)
    if response.status_code != 200:
        speak("Failed to contact Google for authentication.")
        print("Error:", response.text)
        return None

    data = response.json()
    user_code = data["user_code"]
    verification_url = data["verification_url"]
    interval = data.get("interval", 5)
    device_code = data["device_code"]

    speak(f"To link your calendar, go to google dot com slash device and enter the code: {user_code}")
    print(f"[Google OAuth] Visit {verification_url} and enter code: {user_code}")

    # 🔁 Step 3: Poll for user approval
    while True:
        time.sleep(interval)
        token_response = requests.post(
            TOKEN_URL,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            }
        )

        if token_response.status_code == 200:
            token_data = token_response.json()
            token_data["created_at"] = time.time()

            with open(GOOGLE_TOKEN_FILE, "w") as token_file:
                json.dump(token_data, token_file)

            speak("✅ Calendar connected successfully.")
            return build_calendar_service(token_data)

        elif token_response.status_code in [428, 403]:
            continue  # Still waiting for user to authorize

        else:
            speak("❌ Authentication failed. Please try again.")
            print("Auth Error:", token_response.text)
            return None

def is_token_expired(token_data):
    expires_in = token_data.get("expires_in")
    issued_at = token_data.get("created_at", 0)
    return time.time() > issued_at + expires_in if expires_in else True

def refresh_access_token(refresh_token):
    response = requests.post(
        TOKEN_URL,
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
    )
    if response.status_code == 200:
        token_data = response.json()
        token_data["created_at"] = time.time()
        with open(GOOGLE_TOKEN_FILE, "w") as token_file:
            json.dump(token_data, token_file)
        speak("🔄 Calendar token refreshed.")
        return token_data
    else:
        speak("❌ Failed to refresh calendar token.")
        print("Refresh Error:", response.text)
        return None

def build_calendar_service(token_data):
    creds = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=TOKEN_URL,
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET
    )
    return build("calendar", "v3", credentials=creds)
