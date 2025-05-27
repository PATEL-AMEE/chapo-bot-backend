

import random

class EmotionDetector:
    def __init__(self):
        self.current_emotion = "neutral"
        self.emotion_history = []

    def detect_emotion(self, text):
        """Detect user's emotion based on keywords."""
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
        # Add more as you wish

        self.update_emotion(emotion)
        return emotion

    def update_emotion(self, new_emotion):
        self.emotion_history.append(new_emotion)
        if len(self.emotion_history) > 5:
            self.emotion_history.pop(0)
        self.current_emotion = new_emotion

    def generate_emotion_response(self):
        """Respond based on latest detected emotion. No music suggestions unless relevant."""
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

# ------- Standalone Test Harness -------
if __name__ == "__main__":
    detector = EmotionDetector()
    print("Emotion Detector Standalone Test")
    print("Type your feelings (or Ctrl+C to exit):")
    while True:
        try:
            user_input = input("You: ")
            emotion = detector.detect_emotion(user_input)
            print(f"[Detected Emotion]: {emotion}")
            print("Chapo:", detector.generate_emotion_response())
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
