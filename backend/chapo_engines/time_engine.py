# time_engine.py

"""
ChapoTimeEngine
---------------
Handles time and date responses for the Chapo voice assistant.

Usage:
    from chapo_engines.chapo_time_engine import chapo_time_engine

    time_str = chapo_time_engine.get_time_str()
    date_str = chapo_time_engine.get_date_response()
    full = chapo_time_engine.get_full_time_response()
    datetime_str = chapo_time_engine.get_time_and_date()
    
Author: [Your Name]
Date: 2025-05-28
"""

from datetime import datetime
import random

class ChapoTimeEngine:
    """
    Provides utilities for formatting current time and date.
    """

    def __init__(self, tz=None):
        """
        Initialize with optional timezone (not implemented here, but placeholder for future extension).
        :param tz: (Optional) Timezone string, e.g. 'Europe/London'
        """
        self.tz = tz

    def get_time_str(self):
        """
        Returns current time as a string, e.g. "03:45 PM".
        """
        now = datetime.now()
        return now.strftime('%I:%M %p')

    def get_time_24h(self):
        """
        Returns current time in 24-hour format, e.g. "15:45".
        """
        now = datetime.now()
        return now.strftime('%H:%M')

    def get_full_time_response(self):
        """
        Returns a friendly, randomized string about the current time.
        """
        now = datetime.now()
        options = [
            f"It's {now.strftime('%I:%M %p')}.",
            f"The time is {now.strftime('%H:%M')}.",
            f"Right now, it's {now.strftime('%I:%M %p')}.",
            f"It's currently {now.strftime('%H:%M')}.",
            f"Let me check... It's {now.strftime('%I:%M %p')}."
        ]
        return random.choice(options)

    def get_date_response(self):
        """
        Returns today's date as a string, e.g. "Today is Tuesday, May 28, 2025."
        """
        now = datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}."

    def get_time_and_date(self):
        """
        Returns a combined string with current time and date.
        """
        now = datetime.now()
        return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}."

# Singleton instance for convenience import elsewhere
chapo_time_engine = ChapoTimeEngine()

# Example CLI block for onboarding/testing
if __name__ == "__main__":
    print("Chapo Time Engine Demo")
    print("Time (12h):", chapo_time_engine.get_time_str())
    print("Time (24h):", chapo_time_engine.get_time_24h())
    print("Full Time Response:", chapo_time_engine.get_full_time_response())
    print("Date:", chapo_time_engine.get_date_response())
    print("Time and Date:", chapo_time_engine.get_time_and_date())



# ------- Standalone CLI Test Harness -------
if __name__ == "__main__":
    print("Chapo Time Engine CLI Test")
    engine = ChapoTimeEngine()
    print("Type: time, date, datetime, or exit")
    while True:
        try:
            user_input = input("\nYou: ").strip().lower()
            if user_input == "exit":
                print("👋 Goodbye!")
                break
            elif user_input == "time":
                print(engine.get_full_time_response())
            elif user_input == "date":
                print(engine.get_date_response())
            elif user_input == "datetime":
                print(engine.get_time_and_date())
            else:
                print("Commands: time, date, datetime, exit")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

"""
How it works:
- User: time      # ("What's the time?")
- User: date      # ("What's the date?")
- User: datetime  # ("What's the time and date?")
- User: exit
"""
