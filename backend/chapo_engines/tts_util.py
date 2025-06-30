# chapo_engines/tts_util.py

import os
import tempfile
import pygame
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

api_key = os.getenv("ELEVEN_API_KEY")
if not api_key:
    raise ValueError("❌ ELEVEN_API_KEY is missing in .env")

VOLUME_LEVEL = 0.6
client = ElevenLabs(api_key=api_key)

def speak(text):
    if not text or not isinstance(text, str) or not text.strip():
        return  # Skip empty/null text

    print(f"🗣️ Chapo: {text}")
    try:
        audio = client.text_to_speech.convert(
            text=text.strip(),
            voice_id="EXAVITQu4vr4xnSDxMaL",
            model_id="eleven_turbo_v2",
            output_format="mp3_44100_128"
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            for chunk in audio:
                tmp.write(chunk)
            tmp_path = tmp.name

        pygame.mixer.init()
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.set_volume(VOLUME_LEVEL)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.quit()
        os.remove(tmp_path)

    except Exception as e:
        print(f"[TTS Error]: {e}")
