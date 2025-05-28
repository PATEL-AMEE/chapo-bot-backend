# chapo_engines/emotion_detector_engine.py

"""
EmotionDetectorEngine
---------------------
Detects and responds to user emotions based on simple keyword heuristics.

Usage Example:
    from chapo_engines.emotion_detector_engine import EmotionDetectorEngine

    engine = EmotionDetectorEngine()
    emotion = engine.detect_emotion("I feel sad today")
    response = engine.generate_emotion_response()

Author: [Your Name]
Date: 2025-05-28
"""

import random

class EmotionDetectorEngine:
    """
    Tracks user emotions and produces empathy-driven responses.
    Emotion is detected from keywords in the user's input.
    """

    def __init__(self):
        self.current_emotion = "neutral"
        self.emotion_history = []

    def detect_emotion(self, text: str) -> str:
        """
        Detects the user's emotion from keywords.
        Updates emotion history.
        :param text: User input text
        :return: Detected emotion string (e.g., 'sad', 'happy', etc.)
        """
        text = text.lower()
        emotion = "neutral"
        if any(word in text for word in ["sad", "depressed", "unhappy", "lonely", "down", "blue"]):
            emotion = "sad"
        elif any(word in text for word in ["happy", "excited", "glad", "joyful", "great", "awesome"]):
            emotion = "happy"
        elif any(word in text for word in ["angry", "mad", "furious", "upset", "pissed"]):
            emotion = "angry"
        elif any(word in text for word in ["tired", "sleepy", "exhausted", "fatigued", "drained"]):
            emotion = "tired"
        elif any(word in text for word in ["anxious", "worried", "nervous", "stressed", "panicky"]):
            emotion = "anxious"
        elif any(word in text for word in ["okay", "fine", "alright", "neutral"]):
            emotion = "neutral"
        # Extend as needed

        self.update_emotion(emotion)
        return emotion

    def update_emotion(self, new_emotion: str):
        """
        Updates emotion history and current emotion.
        Keeps only the last 5 entries.
        :param new_emotion: Newly detected emotion
        """
        self.emotion_history.append(new_emotion)
        if len(self.emotion_history) > 5:
            self.emotion_history.pop(0)
        self.current_emotion = new_emotion

    def generate_emotion_response(self) -> str:
        """
        Produces a natural language response based on the latest detected emotion.
        :return: A chatbot reply string
        """
        if self.current_emotion == "sad":
            return random.choice([
                "I'm here for you. Remember, tough times don't last.",
                "Sending you a virtual hug. Want to talk about it?",
                "You're not alone, and things can get better. Let me know if you want a distraction or a fun fact."
            ])
        elif self.current_emotion == "happy":
            return random.choice([
                "I love seeing you in high spirits!",
                "That's awesome! Keep enjoying your day!",
                "Yay, your happiness is contagious!"
            ])
        elif self.current_emotion == "angry":
            return random.choice([
                "That sounds frustrating. I'm here to listen if you want to talk.",
                "Sometimes venting helps. Do you want to share more?",
                "Take a deep breath. You're stronger than you think."
            ])
        elif self.current_emotion == "tired":
            return random.choice([
                "Rest is important. Maybe take a short break if you can.",
                "Take it easy—your well-being matters.",
                "It's okay to pause and recharge. Let me know if I can help with anything."
            ])
        elif self.current_emotion == "anxious":
            return random.choice([
                "Let's take a deep breath together. You're not alone.",
                "You're doing better than you think. Would a fun fact help distract you?",
                "Remember, this feeling will pass. Let me know if you want to chat."
            ])
        else:  # Neutral or unknown
            return random.choice([
                "I'm here whenever you need me.",
                "Let me know if you'd like to chat or just hang out.",
                "How can I support you today?"
            ])

# ---- Standalone CLI Test Harness (for onboarding) ----
if __name__ == "__main__":
    engine = EmotionDetectorEngine()
    print("Emotion Detector Engine CLI Test")
    print("Type your feelings (or Ctrl+C to exit):")
    while True:
        try:
            user_input = input("You: ")
            emotion = engine.detect_emotion(user_input)
            print(f"[Detected Emotion]: {emotion}")
            print("Chapo:", engine.generate_emotion_response())
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break



# ------- Standalone CLI Test Harness -------
if __name__ == "__main__":
    detector = EmotionDetector()
    print("Emotion Detector CLI Test")
    print("Type how you feel (e.g. 'I'm sad', 'I'm happy', 'I'm tired'), or exit.")
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() == "exit":
                print("👋 Goodbye!")
                break
            emotion = detector.detect_emotion(user_input)
            print(f"[Detected Emotion]: {emotion}")
            print("Chapo:", detector.generate_emotion_response())
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

"""
How it works:
- User: I'm sad
- User: I'm happy
- User: I'm angry
- User: I'm tired
- User: exit
"""
