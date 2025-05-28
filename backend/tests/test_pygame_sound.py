import pygame
from pathlib import Path
import time

ALARM_SOUND = Path.home() / "chapo-bot-backend" / "alarm.mp3"
pygame.mixer.init()
pygame.mixer.music.load(str(ALARM_SOUND))
pygame.mixer.music.play()
print("🔊 Should be playing!")
while pygame.mixer.music.get_busy():
    time.sleep(0.1)
print("DONE")
