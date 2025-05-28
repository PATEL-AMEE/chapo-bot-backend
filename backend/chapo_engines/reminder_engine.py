"""
reminder_engine.py

Handles reminders: add, delete, list, and persist reminders for each user session.
- Uses a JSON file for simple persistence.
- Easy to expand for notification or async reminders.

Author: [Your Name], 2025-05-28
"""

import asyncio
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.parser import parse, ParserError
from plyer import notification
import pygame
import pytz

BST = pytz.timezone("Europe/London")

REMINDER_FILE = Path.home() / "chapo-bot-backend" / "backend" / "chapo_engines" / "reminders.json"
REMINDER_SOUND = Path.home() / "chapo-bot-backend" / "alarm.mp3"  # Change as needed

def to_london_aware(dt):
    """Ensure datetime is timezone-aware in Europe/London (BST)."""
    if dt.tzinfo is None:
        return BST.localize(dt)
    else:
        return dt.astimezone(BST)

class ReminderEngine:
    def __init__(self):
        self.reminders = self.load_file()
        self.tasks = []

    def load_file(self):
        if REMINDER_FILE.exists():
            try:
                with open(REMINDER_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[REMINDER] Error loading file: {e}")
        return []

    def save_file(self):
        try:
            with open(REMINDER_FILE, "w", encoding="utf-8") as f:
                json.dump(self.reminders, f, indent=2)
        except Exception as e:
            print(f"[REMINDER] Error saving file: {e}")

    def generate_id(self):
        if not self.reminders:
            return 1
        return max(r.get("id", 0) for r in self.reminders) + 1

    def extract_task_and_time(self, text, entities):
        # 1. Try entity
        datetime_entity = next(
            (ent[0]['value'] for key, ent in entities.items() if "datetime" in key and ent and 'value' in ent[0]), None
        )
        time = None

        # Try entity parse
        if datetime_entity:
            try:
                parsed_time = parse(datetime_entity)
                parsed_time = to_london_aware(parsed_time)
                now = datetime.now(BST)
                if parsed_time > now:
                    time = parsed_time.isoformat()
            except (ParserError, ValueError) as e:
                print(f"[REMINDER] Entity datetime parse error: {e}")
                time = None

        # 2. Try NLP parse from text
        if not time:
            try:
                parsed_time = parse(text, fuzzy=True)
                parsed_time = to_london_aware(parsed_time)
                now = datetime.now(BST)
                if parsed_time > now:
                    time = parsed_time.isoformat()
            except (ParserError, ValueError) as e:
                print(f"[REMINDER] Text datetime parse error: {e}")
                time = None

        # 3. Try relative phrasing: "in 10 minutes"
        if not time:
            match = re.search(r'in (\d+)\s*(minutes?|hours?)', text.lower())
            if match:
                n = int(match.group(1))
                unit = match.group(2)
                delta = timedelta(minutes=n) if "minute" in unit else timedelta(hours=n)
                dt = datetime.now(BST) + delta
                time = dt.isoformat()

        # Clean up task phrase
        task = re.sub(r'remind me( to)?', '', text, flags=re.IGNORECASE).strip()
        task = re.sub(r'\bin \d+ (minutes?|hours?)\b', '', task, flags=re.IGNORECASE).strip()
        task = re.sub(r'\btomorrow\b', '', task, flags=re.IGNORECASE)
        task = re.sub(r'\bat\b', '', task, flags=re.IGNORECASE)
        task = re.sub(r'\b\d{1,2}(:\d{2})?\s*(am|pm)?\b', '', task, flags=re.IGNORECASE)
        task = re.sub(r'\s+', ' ', task).strip()

        return task or text, time

    async def trigger_reminder_after_delay(self, reminder):
        try:
            reminder_time = parse(reminder["time"])
            reminder_time = to_london_aware(reminder_time)
            now = datetime.now(BST)
            delay = (reminder_time - now).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)

            print(f"[REMINDER] Triggering: {reminder['task']} at {reminder['time']}")
            try:
                notification.notify(
                    title="⏰ Chapo Reminder",
                    message=f"Task: {reminder['task']}",
                    timeout=10
                )
            except Exception as e:
                print(f"[REMINDER] Notification failed: {e}")
            try:
                pygame.mixer.init()
                if REMINDER_SOUND.exists():
                    pygame.mixer.music.load(str(REMINDER_SOUND))
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
            except Exception as e:
                print(f"[REMINDER] Sound failed: {e}")
        except Exception as e:
            print(f"[REMINDER] Error in trigger_reminder_after_delay: {e}")

    async def schedule_existing_reminders(self):
        # For all future reminders, schedule
        now = datetime.now(BST)
        for reminder in self.reminders:
            try:
                reminder_time = parse(reminder["time"])
                reminder_time = to_london_aware(reminder_time)
                if reminder_time > now:
                    print(f"[REMINDER] Scheduling: {reminder['task']} at {reminder['time']}")
                    task = asyncio.create_task(self.trigger_reminder_after_delay(reminder))
                    self.tasks.append(task)
                else:
                    print(f"[REMINDER] Skipping past reminder: {reminder['task']} at {reminder['time']}")
            except Exception as e:
                print(f"[REMINDER] Could not parse reminder time: {reminder.get('time')}, {e}")

    async def handle_reminder(self, text, entities):
        task, time = self.extract_task_and_time(text, entities)
        if not task:
            return "❓ What should I remind you about?"
        if not time:
            return "⏰ When should I remind you?"

        reminder_id = self.generate_id()
        reminder = {"id": reminder_id, "task": task, "time": time}
        self.reminders.append(reminder)
        self.save_file()
        print(f"[REMINDER] Set: {reminder}")

        try:
            notification.notify(
                title="Reminder Set ✅", message=f"Task: {task}\nAt: {time}", timeout=5
            )
        except Exception as e:
            print(f"[REMINDER] Notification failed: {e}")

        # Schedule async trigger
        asyncio.create_task(self.trigger_reminder_after_delay(reminder))

        return f"🔔 Reminder #{reminder_id} set to '{task}' at {time}."

    def list_reminders(self):
        if not self.reminders:
            return "🔕 No reminders set."
        return "🔔 Reminders:\n" + "\n".join([f"{r['id']}. {r['task']} at {r['time']}" for r in self.reminders])

    def delete_reminder(self, task_or_id):
        initial_len = len(self.reminders)
        if isinstance(task_or_id, int) or (isinstance(task_or_id, str) and str(task_or_id).isdigit()):
            task_or_id = int(task_or_id)
            self.reminders = [r for r in self.reminders if r["id"] != task_or_id]
        else:
            self.reminders = [r for r in self.reminders if r["task"].lower() != str(task_or_id).lower()]
        self.save_file()
        if len(self.reminders) < initial_len:
            return "🗑️ Reminder deleted."
        return "⚠️ Reminder not found."

# --- Singleton instance ---
reminder_engine = ReminderEngine()
