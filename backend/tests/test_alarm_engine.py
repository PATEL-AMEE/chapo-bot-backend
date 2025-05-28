import asyncio
import pygame
from pathlib import Path

ALARM_SOUND = Path.home() / "chapo-bot-backend" / "alarm.mp3"

async def play_alarm_after_delay(delay_seconds: int):
    print(f"[DEBUG] Waiting {delay_seconds} seconds before playing alarm...")
    await asyncio.sleep(delay_seconds)
    pygame.mixer.init()
    if not ALARM_SOUND.exists():
        print("Sound file not found!")
        return
    pygame.mixer.music.load(str(ALARM_SOUND))
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)
    print("Done playing sound.")

if __name__ == "__main__":
    asyncio.run(play_alarm_after_delay(5))
