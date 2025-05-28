"""
core/wit_client.py

Handles all requests to Wit.ai for intent and entity extraction.
Abstracts API calls behind a single function for maintainability.

Author: [Your Name], 2025-05-28
"""

import os
import requests
import logging
from dotenv import load_dotenv

# Load environment vars (e.g. WIT_TOKEN)
load_dotenv()
WIT_TOKEN = os.getenv("WIT_TOKEN")
WIT_API_URL = "https://api.wit.ai/message?v=20230228"

def get_intent_from_wit(text):
    """
    Calls Wit.ai API and extracts primary intent, confidence, and entities.

    Args:
        text (str): User's utterance.

    Returns:
        tuple: (intent_name: str or None, confidence: float, entities: dict)
    """
    if not text:
        return None, 0.0, {}

    headers = {"Authorization": WIT_TOKEN}
    params = {"q": text}
    try:
        resp = requests.get(WIT_API_URL, headers=headers, params=params, timeout=5)
        if not resp.ok:
            logging.error(f"Wit.ai API error: {resp.status_code} {resp.text}")
            return None, 0.0, {}

        data = resp.json()
        intents = data.get("intents", [])
        entities = data.get("entities", {})

        if intents:
            intent_name = intents[0]["name"]
            confidence = intents[0]["confidence"]
            logging.info(f"✅ Detected intent: {intent_name} (Confidence: {confidence:.2f})")
            return intent_name, confidence, entities

        logging.warning(f"No intent detected in text: '{text}'")
        return None, 0.0, entities

    except Exception as e:
        logging.error(f"Wit.ai client exception: {e}")
        return None, 0.0, {}

