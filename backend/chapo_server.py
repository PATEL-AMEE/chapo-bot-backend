from flask import Flask, request, jsonify
import asyncio
from test_voice import respond, get_intent_from_wit, emotion_tracker

app = Flask(__name__)

@app.route('/voice-command', methods=['POST'])
def handle_voice_command():
    data = request.get_json()
    user_input = data.get("text", "")
    session_id = data.get("session_id", "default_user")

    intent, confidence, entities = get_intent_from_wit(user_input)
    user_emotion = emotion_tracker.detect_emotion(user_input)
    response = asyncio.run(respond(intent, entities, session_id, user_input, user_emotion))

    return jsonify({
        "response": response,
        "intent": intent,
        "confidence": confidence,
        "emotion": user_emotion
    })

@app.route('/')
def health_check():
    return "✅ Chapo Server is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
