# chapo_engines/calendar_engine.py

from chapo_engines.calendar_auth import get_google_calendar_service
from chapo_engines.tts_util import speak
from datetime import datetime, timedelta
from dateparser.search import search_dates
import dateparser
import pytz
import re
import json
from pathlib import Path
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

CALENDAR_FILE = Path(__file__).parent / "calendar_events.json"
LONDON = pytz.timezone("Europe/London")

class CalendarEngine:
    def __init__(self):
        self.service = get_google_calendar_service()

    def normalize_spoken_time(self, text):
        time_words = {
            "one": "1", "two": "2", "three": "3", "four": "4",
            "five": "5", "six": "6", "seven": "7", "eight": "8",
            "nine": "9", "ten": "10", "eleven": "11", "twelve": "12"
        }

        # Fix common misheard phrases
        text = re.sub(r"\bat\b\s+meeting", "add meeting", text, flags=re.IGNORECASE)
        text = re.sub(r"\bfile\b", "five", text, flags=re.IGNORECASE)

        # Convert "ten m" → "10 am"
        text = re.sub(
            r"\b(" + "|".join(time_words.keys()) + r")\s*m\b",
            lambda m: time_words[m.group(1).lower()] + " am",
            text,
            flags=re.IGNORECASE
        )

        # Convert spelled time + am/pm
        text = re.sub(
            r"\b(" + "|".join(time_words.keys()) + r")\s*(a|p)m?\b",
            lambda m: time_words[m.group(1).lower()] + (" am" if m.group(2).lower() == "a" else " pm"),
            text,
            flags=re.IGNORECASE
        )

        # Fuzzy time phrases
        fuzzy_map = {
            r"\bthis (evening|tonight)\b": "today at 7 pm",
            r"\btomorrow (morning)\b": "tomorrow at 9 am",
            r"\btomorrow (evening|night)\b": "tomorrow at 7 pm",
            r"\btonight\b": "today at 8 pm",
            r"\bat noon\b": "at 12 pm",
            r"\b(in the )?morning\b": "at 9 am",
            r"\b(in the )?afternoon\b": "at 2 pm",
            r"\b(in the )?evening\b": "at 7 pm",
            r"\bmidday\b": "at 12 pm",
        }

        for pattern, replacement in fuzzy_map.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    def to_london_aware(self, dt):
        if dt.tzinfo is None:
            return LONDON.localize(dt)
        return dt.astimezone(LONDON)

    def add_event(self, user_text, entities=None):
        if not self.service:
            speak("❌ Calendar service not available.")
            return

        normalized_text = self.normalize_spoken_time(user_text)
        found = search_dates(normalized_text, settings={'PREFER_DATES_FROM': 'future'})
        start_time = None
        now = datetime.now(LONDON)
        time_was_explicit = False

        if found:
            for phrase, dt in found:
                if not isinstance(dt, datetime):
                    continue
                dt = self.to_london_aware(dt)

                # 🎯 "tomorrow" with time?
                if "tomorrow" in phrase.lower():
                    time_match = re.search(
                        r"\b(?:tomorrow)\s+(?:at\s+)?(\d{1,2})(:(\d{2}))?\s*(am|pm)?\b",
                        normalized_text,
                        re.IGNORECASE
                    )
                    if time_match:
                        hour = int(time_match.group(1))
                        minute = int(time_match.group(3)) if time_match.group(3) else 0
                        ampm = time_match.group(4)
                        if ampm:
                            if ampm.lower() == "pm" and hour < 12:
                                hour += 12
                            elif ampm.lower() == "am" and hour == 12:
                                hour = 0
                        tomorrow = now + timedelta(days=1)
                        dt = self.to_london_aware(tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0))
                        time_was_explicit = True
                        start_time = dt
                        break
                    else:
                        # 🛑 User said "tomorrow" but not a clear time
                        speak("🕒 I heard 'tomorrow', but not the time. What time should I schedule it for?")
                        return

                elif dt > now:
                    # Acceptable datetime found
                    start_time = dt
                    time_was_explicit = True
                    break

        # 📅 Weekday fallback (e.g., "on Monday three")
        if not start_time:
            fallback_match = re.search(
                r"\b(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b.*?(?P<hour>\d{1,2})(:(?P<minute>\d{2}))?\s*(?P<ampm>am|pm)?",
                normalized_text,
                re.IGNORECASE
            )
            if fallback_match:
                weekday_str = fallback_match.group("weekday").lower()
                hour = int(fallback_match.group("hour"))
                minute = int(fallback_match.group("minute") or 0)
                ampm = fallback_match.group("ampm")

                if ampm:
                    if ampm.lower() == "pm" and hour < 12:
                        hour += 12
                    elif ampm.lower() == "am" and hour == 12:
                        hour = 0
                else:
                    # No AM/PM? Ask instead of guessing
                    speak(f"🕒 I heard '{weekday_str}', but not the time of day. What time should I schedule it for?")
                    return

                weekday_map = {
                    "monday": MO, "tuesday": TU, "wednesday": WE, "thursday": TH,
                    "friday": FR, "saturday": SA, "sunday": SU
                }

                target_day = now + relativedelta(weekday=weekday_map[weekday_str](+1))
                target_day = target_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
                start_time = self.to_london_aware(target_day)
                time_was_explicit = True

        # ❌ No valid time given
        if not time_was_explicit or not isinstance(start_time, datetime):
            speak("❌ I couldn’t understand the time. Try saying something like '10 AM' or 'tomorrow at 3 PM'.")
            return

        end_time = start_time + timedelta(hours=1)

        # 📝 Determine event title
        event_summary = "Untitled Event"
        if entities and 'event' in entities:
            event_summary = entities['event'][0].get("value", "").strip() or event_summary
        else:
            match = re.search(r"(?:add|create|schedule)\s+(a|an|the)?\s*(?P<title>.+?)\s+(to|on|for)?\s*(my)?\s*calendar", normalized_text, re.IGNORECASE)
            if match:
                title = match.group("title").strip()
                if title:
                    event_summary = title
            else:
                fallback_match = re.search(r"(?:dental|doctor|appointment|call|meeting|event)", normalized_text, re.IGNORECASE)
                if fallback_match:
                    event_summary = fallback_match.group(0).capitalize()
                else:
                    event_summary = "Meeting"

        event = {
            'summary': event_summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Europe/London'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Europe/London'
            },
        }

        try:
            self.service.events().insert(calendarId='primary', body=event).execute()

            local_event = {
                "name": event_summary,
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
            events = []
            if CALENDAR_FILE.exists():
                with open(CALENDAR_FILE, "r", encoding="utf-8") as f:
                    events = json.load(f)
            events.append(local_event)
            with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
                json.dump(events, f, indent=2)

            speak(f"📅 I've added {event_summary} for {start_time.strftime('%A at %I:%M %p')}.")
        except Exception as e:
            print("[Calendar Error]", e)
            speak("❌ Failed to save the event to your calendar.")

calendar_engine = CalendarEngine()
