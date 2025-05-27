import random

class EpisodicMemory:
    """Stores user facts, recent dialogue, etc."""
    def __init__(self):
        self.memory = {}

    def remember(self, key, value):
        self.memory[key] = value

    def recall(self, key, default=None):
        return self.memory.get(key, default)

    def forget(self, key):
        if key in self.memory:
            del self.memory[key]

class CoreConversationEngine:
    def __init__(self):
        self.responses = {
            "greeting": [
                "Hello! How can I help you today?",
                "Hi there! What's on your mind?",
                "Hey! Ready to chat whenever you are."
            ],
            "goodbye": [
                "Goodbye! Talk soon!",
                "See you later! Stay safe.",
                "Take care! I'm always here if you need me."
            ],
            "how_are_you": [
                "I'm just a bunch of code, but I'm doing great!",
                "Feeling fantastic and ready to assist!",
                "Running smoothly—thanks for asking!"
            ],
            "what_can_you_do": [
                "I can manage your shopping list, set reminders, tell jokes, answer trivia, and more. What would you like to try?",
                "Need help with reminders, music, or daily info? Just ask!",
                "I can chat, help with tasks, and keep you company!"
            ],
            "tell_me_about_you": [
                "I'm Chapo, your personal assistant. Here to make your day easier!",
                "I'm your AI companion—trained to assist, chat, and be helpful!"
            ],
            "small_talk": [
                "That's interesting! Tell me more.",
                "I'm always here to chat if you want.",
                "I love learning new things—want to share something?",
                "Hmm, I'm not sure what you mean, but I'm listening.",
                "You can ask me to set reminders, check the weather, or just chat!"
            ],
            "unknown": [
                "I'm not sure how to respond to that, but I'm learning!",
                "Sorry, I didn't catch that—could you try rephrasing?",
                "I'm still learning. Can you say that a different way?",
                "You can ask me about shopping lists, reminders, or just chat!",
                "I'm here to help however I can!"
            ],
        }
        self.memory = EpisodicMemory()
        self.turns = []  # Stores recent dialog (for context/follow-up)

    def detect_intent(self, user_input):
        user_input = user_input.lower()
        if any(greet in user_input for greet in ["hello", "hi", "hey"]):
            return "greeting"
        if "how are you" in user_input:
            return "how_are_you"
        if "what can you do" in user_input or "help" in user_input:
            return "what_can_you_do"
        if "about you" in user_input:
            return "tell_me_about_you"
        if any(bye in user_input for bye in ["bye", "goodbye", "see you", "later"]):
            return "goodbye"
        if "my name is" in user_input:
            return "save_name"
        # ...add more rule-based intent detectors as you expand
        return "small_talk"

    def process(self, user_input):
        # Save utterance for context/episodic memory
        self.turns.append({"user": user_input})

        # --- Episodic memory: capture name ---
        if "my name is" in user_input.lower():
            name = user_input.lower().split("my name is")[-1].strip().split()[0].capitalize()
            self.memory.remember("user_name", name)
            return f"Hi {name}, nice to meet you!"

        # --- Retrieve user name in response ---
        if self.memory.recall("user_name") and (
            "how are you" in user_input.lower() or "hello" in user_input.lower() or "hi" in user_input.lower()
        ):
            name = self.memory.recall("user_name")
            return f"Hi {name}, I'm just a bunch of code, but I'm here to help!"

        # --- Intent detection ---
        intent = self.detect_intent(user_input)

        # --- Personalized reply if possible ---
        if intent == "greeting" and self.memory.recall("user_name"):
            name = self.memory.recall("user_name")
            return f"Hi {name}! What's on your mind?"

        # --- Generic reply for supported intents ---
        if intent in self.responses:
            return random.choice(self.responses[intent])

        # --- Fallback to small talk or unknown ---
        if intent == "small_talk":
            return random.choice(self.responses["small_talk"])
        else:
            return random.choice(self.responses["unknown"])

    def summarize_conversation(self):
        # Example: return the last few turns as a recap
        print("\n=== Conversation Recap ===")
        for turn in self.turns[-10:]:
            print("User:", turn.get("user"))
        print("=========================\n")

# === CLI Testing ===
if __name__ == "__main__":
    engine = CoreConversationEngine()
    print("Chapo (Core Conversation) Ready! Type 'exit' to quit.")
    while True:
        user = input("You: ")
        if user.lower().strip() == "exit":
            print("Chapo: Goodbye! 👋")
            break
        reply = engine.process(user)
        print("Chapo:", reply)
