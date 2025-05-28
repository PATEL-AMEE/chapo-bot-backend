# chapo_engines/joke_engine.py

"""
JokeEngine
----------
Handles joke-telling intent for Chapo voice assistant.

Usage:
    from chapo_engines.joke_engine import handle_joke

    reply = handle_joke("tell_joke", "Tell me a joke", {}, memory={})
    # -> returns a random joke string

Author: [amee]
Date: 2025-05-28
"""

from pprint import pprint
import random

# List of canned jokes to serve for "tell_joke" intent
JOKES = [
    "Why don’t scientists trust atoms? Because they make up everything!",
    "What do you get if you cross a snowman and a dog? Frostbite.",
    "I told my computer I needed a break, and it said: 'Why? I’m not doing anything!'",
]

def handle_joke(intent, user_input, entities, memory=None):
    """
    Handles the joke-telling functionality based on detected intent.

    Parameters
    ----------
    intent : str
        The intent detected from user input (typically "tell_joke").
    user_input : str
        The raw user utterance text.
    entities : dict
        (Optional) Wit.ai or NLU-detected entities (not used here).
    memory : dict or None
        (Optional) Conversation memory or session state (unused but provided for interface consistency).

    Returns
    -------
    str
        The assistant's response: either a random joke, or a fallback message.
    """
    print(f"\nYou said: {user_input}")
    print("Wit.ai response:")
    pprint({'intent': intent, 'entities': entities})

    if intent == "tell_joke":
        # Pick a random joke from the list
        return random.choice(JOKES)
    else:
        # Fallback if intent not recognized as joke
        return "😅 I'm only here to tell jokes. Want to hear one?"

# ------- Standalone CLI Test Harness -------
if __name__ == "__main__":
    print("Joke Engine CLI Test")
    print("Type: joke (or 'tell me a joke'), or exit")
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() == "exit":
                print("👋 Goodbye!")
                break
            # Voice example: "Tell me a joke"
            intent = "tell_joke" if "joke" in user_input.lower() else "unknown"
            response = handle_joke(intent, user_input, entities={})
            print("Chapo:", response)
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

"""
How it works:
- User: joke            # ("Tell me a joke")
- User: exit
"""


