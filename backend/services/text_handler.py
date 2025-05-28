"""
text_handler.py

Handles user text input: detects intent via NLU, routes to correct feature engine,
and returns assistant response.

Author: [Your Name], 2025-05-28
"""



# What’s Improved?
# Explicit intent routing: Each supported intent is clear, and others are passed to the router.

# Async compatible: For fastapi, so you can await route_intent if it’s async.

# Commented, readable, easily extensible for new interns.

# Fallbacks: Any unknown/low-confidence input gets a gentle, branded assistant reply.


import logging
import random
import re
from datetime import datetime, timezone

from backend.services.memory import session_memory, prune_memory
from backend.services.music import play_music
from backend.services.weather import get_weather
#from backend.services.reminder import handle_reminder
from backend.services.news import get_news
from backend.services import shopping_list_service
from backend.intent.intent_router import route_intent

# Central dictionary of fallback/canned responses
INTENT_RESPONSES = {
    # ... (same as before, keep all canned responses here) ...
    # "get_weather": [...], etc.
}

def _extract_city(entities, user_input):
    """
    Attempts to extract a city/location from entities or user text.
    """
    if "wit$location" in entities:
        return entities["wit$location"][0].get("value")
    match = re.search(r"(?:in|for)\s+([A-Za-z\s,]+)", user_input, re.IGNORECASE)
    if match:
        return match.group(1).strip(" ?,")
    return None

async def process_text_input(user_input: str, session_id: str = None):
    """
    Processes a user text input, routes to the appropriate engine, and returns a response.

    Args:
        user_input (str): The text the user sent.
        session_id (str, optional): For session-based context/memory.

    Returns:
        dict: Response, intent, and any meta info.
    """
    # --- 1. Sanity & Preprocessing ---
    user_input = user_input.strip()
    if not user_input:
        return {"response": "Please say or type something!", "intent": "none"}

    # --- 2. Intent Detection ---
    from backend.services.nlp import get_intent_from_wit
    intent, confidence, entities = get_intent_from_wit(user_input)
    logging.info(f"NLU Intent: {intent} (confidence={confidence:.2f}) | Entities: {entities}")

    # --- 3. Session/Memory Management ---
    if not session_id:
        session_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    prune_memory(session_id)
    memory = session_memory.get(session_id, {}).get("data", {})
    memory.update(entities)
    session_memory[session_id] = {"data": memory, "last_updated": datetime.now(timezone.utc)}

    # --- 4. Intent Routing & Response Generation ---
    if not intent or confidence < 0.75:
        # Fallback for uncertain intent: canned response or GPT fallback
        return {
            "response": "🤖 I'm not sure how to respond to that. Could you rephrase?",
            "intent": "unknown",
            "confidence": confidence
        }

    # Explicit intent routing (expand this as needed)
    if intent == "set_reminder":
        response = handle_reminder(session_id, entities)
    elif intent in ("time_now",):
        resp_func = random.choice(INTENT_RESPONSES["time_now"])
        response = resp_func() if callable(resp_func) else resp_func
    elif intent in ("get_weather", "wit$get_weather"):
        city = _extract_city(entities, user_input)
        response = get_weather(city) if city else "I couldn't find the city. Try asking again with a location."
    elif intent == "play_music":
        song_name = entities.get("song", [{}])[0].get("value")
        response = play_music(song_name) if song_name else "Sorry, I couldn't detect the song name."
    elif intent in INTENT_RESPONSES:
        resp = random.choice(INTENT_RESPONSES[intent])
        response = resp() if callable(resp) else resp
    else:
        # Any other intent: Route to feature engines/routers
        response = await route_intent(intent, entities, session_id=session_id, user_input=user_input)

    # --- 5. Log and Return ---
    log = {
        "input": user_input,
        "intent": intent,
        "confidence": confidence,
        "entities": entities,
        "response": response,
        "source": "text",
        "timestamp": datetime.utcnow()
    }
    logging.info(f"Text interaction: {log}")
    return log
