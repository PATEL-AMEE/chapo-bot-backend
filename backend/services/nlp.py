"""
nlp.py

Handles communication with Wit.ai for NLU (intent/entity detection).
All calls are logged for traceability.

Author: [Your Name], 2025-05-28
"""

import requests
import os
import logging

# --- Configuration ---
WIT_API_URL = "https://api.wit.ai/message?v=20230228"
WIT_TOKEN = os.getenv("WIT_TOKEN")  # Must be in .env

if not WIT_TOKEN or WIT_TOKEN == "Bearer your-wit-token":
    logging.warning("⚠️ WIT_TOKEN not set! NLP will not work. Check your .env file.")

def get_intent_from_wit(text: str):
    """
    Query Wit.ai to extract intent and entities from user text.
    
    Args:
        text (str): The user's utterance.

    Returns:
        tuple: (intent_name, confidence, entities_dict)
    """
    if not text:
        return None, 0.0, {}

    headers = {"Authorization": WIT_TOKEN}
    params = {"q": text}

    try:
        response = requests.get(WIT_API_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        intents = data.get("intents", [])
        entities = data.get("entities", {})
        if intents:
            # Use top intent
            intent = intents[0].get("name")
            confidence = intents[0].get("confidence", 0.0)
            logging.info(f"✅ Wit.ai intent: {intent} ({confidence:.2f}) | Entities: {entities}")
            return intent, confidence, entities
        else:
            logging.info("❌ Wit.ai returned no intent.")
            return None, 0.0, entities
    except Exception as e:
        logging.error(f"Wit.ai API error: {e}")
        return None, 0.0, {}

# Example usage for intern onboarding
# if __name__ == "__main__":
#     sample = "Set an alarm for 8 AM"
#     print(get_intent_from_wit(sample))
