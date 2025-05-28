"""
services/voice_handler.py

Handles processing of uploaded voice/audio files:
- Saves temp file
- Transcribes to text using Whisper
- Extracts intent/entities from Wit.ai
- Routes request to the appropriate engine/intent handler via IntentRouter
- Logs interaction to MongoDB

Author: [Your Name], 2025-05-28
"""

import whisper
import os
import tempfile
import logging
from fastapi import UploadFile
from backend.services.nlp import get_intent_from_wit
from backend.intent.intent_router import route_intent
from backend.db.mongo import save_interaction
from datetime import datetime

# --- Whisper model is loaded once (for efficiency) ---
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model("base")
    return _whisper_model

async def process_voice_file(file: UploadFile):
    """
    Full processing pipeline for a voice file:
    1. Save temp file.
    2. Transcribe to text using Whisper.
    3. Query Wit.ai for intent/entities.
    4. Route intent to proper handler.
    5. Log result.
    6. Return structured response.
    """
    try:
        # -- Step 1: Save file to temp for Whisper input --
        suffix = os.path.splitext(file.filename)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        logging.info(f"🎤 Received voice file: {file.filename}")

        # -- Step 2: Transcribe with Whisper --
        whisper_model = get_whisper_model()
        result = whisper_model.transcribe(tmp_path, language='en')
        transcribed_text = result['text'].strip()
        logging.info(f"📝 Transcribed: {transcribed_text}")

        # -- Step 3: Query Wit.ai --
        intent, confidence, entities = get_intent_from_wit(transcribed_text)

        # -- Step 4: Fallback/routing --
        if not intent or confidence < 0.75:
            # ChatGPT fallback could go here if desired
            response = "🤖 I'm not sure how to respond to that. Could you rephrase?"
        else:
            response = await route_intent(
                intent=intent, 
                entities=entities, 
                user_input=transcribed_text,
                source="voice"
            )

        # -- Step 5: Log the interaction to MongoDB --
        log = {
            "input": transcribed_text,
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "response": response,
            "source": "voice",
            "timestamp": datetime.utcnow()
        }
        save_interaction(log)

        return log

    except Exception as e:
        logging.error(f"Voice processing failed: {e}")
        return {
            "input": "",
            "intent": "error",
            "response": f"Voice processing error: {str(e)}"
        }
    finally:
        # -- Step 6: Clean up temp file --
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception as cleanup_err:
            logging.warning(f"Could not delete temp file: {tmp_path} - {cleanup_err}")
