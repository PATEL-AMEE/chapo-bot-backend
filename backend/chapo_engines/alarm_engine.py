"""
alarm_engine.py

Handles user alarms: set, stop, and persist alarms to disk.
- Uses asyncio for alarm scheduling
- Plays an alarm sound and system notification on trigger

Author: [naim], 2025-05-28
"""

import asyncio
import datetime
import json
from pathlib import Path
from plyer import notification
import pygame
import pytz
from typing import Optional
import dateparser

# Timezone BST
BST = pytz.timezone("Europe/London")

# File paths
ALARM_FILE = Path.home() / "chapo-bot-backend" / "backend" / "chapo_engines" / "alarms.json"
ALARM_SOUND = Path.home() / "chapo-bot-backend" / "alarm.mp3"

# ---- PATCH: Store all scheduled alarm tasks here!
scheduled_alarms = []

def save_alarm_task(task):
    scheduled_alarms.append(task)

def load_alarms():
    print("[DEBUG] load_alarms called")
    try:
        if ALARM_FILE.exists():
            print(f"[DEBUG] Alarm file {ALARM_FILE} exists")
            with open(ALARM_FILE, 'r', encoding='utf-8') as f:
                alarms = json.load(f)
                print(f"[DEBUG] Loaded alarms: {alarms}")
                return alarms
        else:
            print(f"[DEBUG] Alarm file {ALARM_FILE} does not exist")
    except Exception as e:
        print(f"[ERROR] Error reading alarm file: {e}")
    return []

def save_alarm(alarm_time_bst):
    print(f"[DEBUG] save_alarm called with {alarm_time_bst}")
    try:
        alarms = load_alarms()
        alarms.append(alarm_time_bst.isoformat())
        with open(ALARM_FILE, 'w', encoding='utf-8') as f:
            json.dump(alarms, f, indent=2)
        print(f"[DEBUG] Alarm saved to {ALARM_FILE}")
    except Exception as e:
        print(f"[ERROR] Error saving alarm: {e}")

def parse_time_from_text(text: str) -> Optional[datetime.datetime]:
    print(f"[DEBUG] parse_time_from_text called with '{text}'")
    # Use dateparser for robust natural language parsing
    parsed_time = dateparser.parse(
        text,
        settings={
            'TIMEZONE': 'Europe/London',
            'RETURN_AS_TIMEZONE_AWARE': True,
            'PREFER_DATES_FROM': 'future'
        }
    )
    if parsed_time:
        parsed_time = parsed_time.astimezone(BST)
        print(f"[DEBUG] dateparser matched: {parsed_time}")
        return parsed_time

    print("[DEBUG] dateparser found no match")
    return None

async def trigger_alarm_after_delay(delay_seconds: float):
    print(f"[DEBUG] >>>>> ENTERED trigger_alarm_after_delay at {datetime.datetime.now(BST)}")
    print(f"[DEBUG] Alarm scheduled in {delay_seconds} seconds")
    await asyncio.sleep(delay_seconds)
    print("[DEBUG] Woke up from sleep, triggering alarm actions...")

    try:
        print("[DEBUG] Sending notification...")
        notification.notify(
            title="⏰ Chapo Alarm",
            message="Time to wake up!",
            timeout=10
        )
        print("[DEBUG] Notification sent.")
    except Exception as e:
        print(f"[ERROR] Notification error: {e}")

    try:
        print("[DEBUG] Initializing pygame mixer...")
        pygame.mixer.init()
        print("[DEBUG] Pygame mixer initialized.")
        if ALARM_SOUND.exists():
            print(f"[DEBUG] Alarm sound file exists: {ALARM_SOUND}")
            pygame.mixer.music.load(str(ALARM_SOUND))
            print("[DEBUG] Alarm sound loaded.")
            pygame.mixer.music.play()
            print("🔊 Playing alarm sound...")
            while pygame.mixer.music.get_busy():
                print("[DEBUG] Music is playing...")
                await asyncio.sleep(0.1)
            print("[DEBUG] Music finished.")
        else:
            print(f"[ERROR] Alarm sound file not found: {ALARM_SOUND}")
    except Exception as e:
        print(f"[ERROR] Error triggering alarm sound: {e}")

async def set_alarm(text: str, entities: dict, session_id: str, context: dict) -> dict:
    try:
        print(f"[DEBUG] set_alarm called with text='{text}', entities={entities}, session_id={session_id}")
        alarm_time = None

        # --- PATCH: entity handling ---
        if entities:
            # Try ALL datetime values, pick the soonest/most likely
            datetime_entities = []
            for k in entities:
                if "datetime" in k:
                    for entity in entities[k]:
                        val = entity.get("value")
                        if val:
                            datetime_entities.append(val)
            # Prefer the entity that parses into the soonest future time
            soonest_time = None
            for dt_val in datetime_entities:
                candidate_time = parse_time_from_text(dt_val)
                if candidate_time and (not soonest_time or candidate_time < soonest_time):
                    soonest_time = candidate_time
            if soonest_time:
                alarm_time = soonest_time
                print(f"[DEBUG] Chose soonest entity alarm_time: {alarm_time}")

        if not alarm_time:
            alarm_time = parse_time_from_text(text)
            if not alarm_time:
                print("[DEBUG] Could not parse alarm time from text")
                return {
                    "text": "I couldn't understand the time.",
                    "session_id": session_id
                }
            else:
                print(f"[DEBUG] Parsed alarm_time from text: {alarm_time}")

        now = datetime.datetime.now(BST)
        delay = (alarm_time - now).total_seconds()
        print(f"[DEBUG] Now: {now}, Alarm time: {alarm_time}, Delay: {delay}")

        if delay <= 0:
            print("[DEBUG] Alarm time is in the past")
            return {
                "text": "This time has already passed. Please provide a future time.",
                "session_id": session_id
            }

        save_alarm(alarm_time)
        print("[DEBUG] Creating asyncio task for alarm...")
        # --- PATCH: store all scheduled alarm tasks!
        t = asyncio.create_task(trigger_alarm_after_delay(delay))
        save_alarm_task(t)
        print("[DEBUG] Alarm task created.")

        if delay < 60:
            response = f"Alarm set in {int(delay)} seconds"
        elif delay < 3600:
            response = f"Alarm set in {int(delay//60)} minutes"
        else:
            response = f"Alarm set for {alarm_time.strftime('%H:%M')} (BST)"

        print(f"[DEBUG] Returning response: {response}")
        return {
            "text": response,
            "session_id": session_id
        }

    except Exception as e:
        print(f"[CRITICAL ERROR] in set_alarm: {e}")
        return {
            "text": "⚠️ An error occurred while setting the alarm.",
            "session_id": session_id
        }

async def schedule_existing_alarms():
    alarms = load_alarms()
    now = datetime.datetime.now(BST)
    print(f"[DEBUG] Scheduling all existing alarms: {alarms}")
    for alarm_str in alarms:
        try:
            alarm_time = datetime.datetime.fromisoformat(alarm_str)
            alarm_time = alarm_time.astimezone(BST)
            delay = (alarm_time - now).total_seconds()
            if delay > 0:
                print(f"[DEBUG] Scheduling alarm for {alarm_time} (in {delay} seconds)")
                t = asyncio.create_task(trigger_alarm_after_delay(delay))
                save_alarm_task(t)
            else:
                print(f"[DEBUG] Skipping past alarm: {alarm_time}")
        except Exception as e:
            print(f"[ERROR] Could not parse alarm time: {alarm_str}, error: {e}")

# Example for test only
async def main():
    await schedule_existing_alarms()
    await set_alarm("in 10 seconds", {}, "test", {})

if __name__ == "__main__":
    asyncio.run(main())
