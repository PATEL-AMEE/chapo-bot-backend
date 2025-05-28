"""
text.py
POST endpoint for handling text-based user input and intent dispatch.
Author: x-tech, 2025-05-28
"""

from fastapi import APIRouter, Body, HTTPException
from backend.core.wit_client import get_intent_from_wit  # Wit.ai handler
from backend.main import IntentRouter                    # Our dispatcher
import logging

router = APIRouter(prefix="/text", tags=["Text Input"])
intent_router = IntentRouter()

@router.post("/")
async def handle_text(user_input: str = Body(..., embed=True)):
    """
    Receives user text, parses intent/entities, routes to feature engine,
    and returns the response.
    """
    if not user_input.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    try:
        # Step 1: NLP (Wit.ai)
        intent, confidence, entities = get_intent_from_wit(user_input)
        session_id = "web_" + str(hash(user_input))  # Customize per user/session
        logging.info(f"📝 NLP: '{user_input}' → intent='{intent}' confidence={confidence}")

        # Step 2: Use IntentRouter to process
        response = await intent_router.handle_intent(intent, entities, session_id, user_input)
        return {
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "response": response
        }
    except Exception as e:
        logging.error(f"❌ Error in /text/: {e}")
        raise HTTPException(status_code=500, detail=str(e))
