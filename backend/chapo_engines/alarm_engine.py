import asyncio
import datetime
from plyer import notification
import pygame
import os
import json

ALARM_FILE = "alarms.json"
alarm_tasks = []
## this is how you comment a line of code
async def set_alarm(text: str, entities: dict, session_id: str, context: dict) -> dict:
    global alarm_tasks

    try:
        datetime_entity = entities.get('wit$datetime:datetime', [{}])[0].get('value')
        if not datetime_entity:
            return {"text": "I couldn't find the alarm time you want. Please try again.", "session_id": session_id}

        alarm_time = datetime.datetime.fromisoformat(datetime_entity.replace('Z', '+00:00'))
        now = datetime.datetime.now(datetime.timezone.utc)
        delay = (alarm_time - now).total_seconds()

        if delay <= 0:
            return {"text": "The time you set is already passed! Please set a future time.", "session_id": session_id}

        # For testing purposes, override long delays with 5 seconds
        if delay > 60:
            print("Test mode active: replacing delay with 5 seconds for testing.")
            delay = 5

        # Save alarm info to file
        alarm_record = {"time": alarm_time.isoformat(), "session_id": session_id}
        existing_alarms = []
        if os.path.exists(ALARM_FILE):
            with open(ALARM_FILE, "r") as f:
                try:
                    existing_alarms = json.load(f)
                except json.JSONDecodeError:
                    existing_alarms = []
        existing_alarms.append(alarm_record)
        with open(ALARM_FILE, "w") as f:
            json.dump(existing_alarms, f, indent=2)

        task = asyncio.create_task(trigger_alarm_after_delay(delay))
        alarm_tasks.append(task)

        response_text = f"Ok, your alarm is set for {alarm_time.strftime('%I:%M %p')}."
        return {"text": response_text, "session_id": session_id}

    except Exception as e:
        print(f"Alarm setting error: {str(e)}")
        return {"text": "Sorry, I couldn't set the alarm. Please try again.", "session_id": session_id}


async def trigger_alarm_after_delay(delay_seconds: float):
    await asyncio.sleep(delay_seconds)

    try:
        notification.notify(
            title='Chapo Alarm',
            message='Wake up! Your alarm is ringing!',
            timeout=10
        )

        pygame.mixer.init()
        audio_path = "/Users/user/chapo-bot-backend/backend/my_ringtone.mp3"
        if not os.path.exists(audio_path):
            print(f"Audio file not found: {audio_path}")
            return

        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        print("🔊 Alarm sound playing...")

        while pygame.mixer.music.get_busy():
            await asyncio.sleep(1)

    except Exception as e:
        print(f"Error playing alarm sound: {str(e)}")


async def stop_alarm(text: str, entities: dict, session_id: str, context: dict) -> dict:
    global alarm_tasks

    try:
        for task in alarm_tasks:
            task.cancel()
        alarm_tasks.clear()

        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()

        # Clear alarm file
        if os.path.exists(ALARM_FILE):
            with open(ALARM_FILE, "w") as f:
                json.dump([], f)

        return {"text": "Alarm stopped successfully.", "session_id": session_id}

    except Exception as e:
        print(f"Error stopping alarm: {str(e)}")
        return {"text": "I couldn't stop the alarm properly.", "session_id": session_id}
