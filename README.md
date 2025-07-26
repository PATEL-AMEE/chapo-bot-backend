# Chapo Bot – Voice-Controlled Humanoid Home Assistant

## Recent Updates

* Reminder Engine: Asynchronous scheduling with BST-aware timestamps, persistent JSON storage, and sound notifications.
* Calendar Integration: Google OAuth2 device flow with support for fuzzy natural language time parsing.
* GPT-4 Fallback: Handles ambiguous or unsupported queries with conversational intelligence.
* Modular Engine Design: Each intent engine (e.g., news, cooking, fitness, jokes) is independent and reusable.
* Text-to-Speech Enhancements: ElevenLabs integration for high-quality voice synthesis.
* Evaluation Framework: Tracks intent classification metrics including precision, recall, and fallback activation.

## Features

### Core Implemented Features

* Voice Input: Real-time speech-to-text via Whisper and PyAudio.
* Intent Detection: Wit.ai as primary engine with HuggingFace fallback.
* GPT-4 Integration: Supports open-domain queries and fallback responses.
* Calendar: Natural language scheduling with Google Calendar integration.
* Reminders and Alarms: Timezone-aware scheduling with persistent state.
* News: Real-time news headlines via NewsAPI with keyword fallback.
* Cooking and Recipes: Meal suggestions and preparation steps via Spoonacular.
* Fitness and Nutrition: Workout routines and calorie tracking via Nutritionix.
* Knowledge Q\&A: Wikipedia, WolframAlpha, and GPT integration.
* Emotion Detection: Sentiment detection for empathetic response adaptation.
* Jokes: Static humor engine to support light conversational interaction.
* Evaluation: Runtime tracking of classification and fallback metrics.

### In Progress

* IoT and Home Assistant integration.
* Spotify music playback.
* Object and facial recognition using YOLOv8.
* Streamlit dashboard for real-time logs and metrics.
* Location-aware capabilities using Google Maps.

## System Architecture

Voice Input → Whisper STT → Wit.ai → Intent Router
Intent Router → HuggingFace (fallback) → GPT-4 (fallback)
Intent Router → Engine Layer → (Reminders, Calendar, Cooking, Fitness, etc.)
Engine Layer → MongoDB Logging, ElevenLabs Text-to-Speech

## Technology Stack

| Category  | Technology                                      |
| --------- | ----------------------------------------------- |
| Language  | Python 3.10+                                    |
| Voice I/O | PyAudio, Pygame, Whisper                        |
| NLP       | Wit.ai, HuggingFace Transformers, OpenAI GPT    |
| TTS       | ElevenLabs API                                  |
| Calendar  | Google Calendar API (OAuth2)                    |
| Reminders | Async Scheduling, Dateparser, Plyer             |
| APIs      | NewsAPI, Spoonacular, Nutritionix, WolframAlpha |
| Database  | MongoDB, JSON Logs                              |
| Testing   | CLI Scripts, evaluate\_model.py                 |

## Project Structure (Core Engines Only)

```
chapo-bot-backend/
└── backend/
    ├── test_voice.py                   # Voice CLI entry point
    ├── calendar_engine.py              # Event scheduling logic
    ├── calendar_auth.py                # Google OAuth setup
    ├── cooking_engine.py               # Recipe recommendations
    ├── emotion_detector_engine.py      # Sentiment and emotion detection
    ├── fitness_engine.py               # Fitness routines and nutrition
    ├── joke_engine.py                  # Static jokes engine
    ├── knowledge_engine.py             # General knowledge retrieval
    ├── news_engine.py                  # News headlines retriever
    ├── reminder_engine.py              # Reminders and alarms (async)
    ├── core_conversation_engine.py     # Central routing and fallback logic
    └── db/
        └── mongo.py                    # MongoDB log storage
```

## Setup Instructions

1. Clone the repository and create a virtual environment:

```bash
git clone https://github.com/Web8080/chapo-bot-backend.git
cd chapo-bot-backend
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
cp .env.example .env
# Add values for the following:
# WIT_TOKEN=
# OPENAI_API_KEY=
# ELEVEN_API_KEY=
# SPOONACULAR_API_KEY=
# GOOGLE_CLIENT_ID=, GOOGLE_CLIENT_SECRET=
# NEWS_API_KEY=, NUTRITIONIX_APP_ID/KEY=
```

4. Run the application:

```bash
python backend/test_voice.py     # Start the CLI-based voice assistant
uvicorn backend.app:app --reload # Optionally run the FastAPI server
```

## Evaluation and Metrics

Run the evaluation script to assess model performance:

```bash
python backend/evaluate_model.py
```

Outputs include accuracy, precision, and recall calculated from logs.

## Roadmap

* Integration with smart home devices
* Wake-word activation support
* Enhanced fallback model fine-tuning
* Streamlit-based dashboard
* Retrieval-Augmented Generation (RAG)
* Personalized memory and context persistence
* Automated feedback-based improvement

## Lessons and Best Practices

* All time-related functions must use BST-aware timestamps.
* Fallback strategy follows this sequence: Wit.ai → HuggingFace → GPT-4.
* Use dateparser and regular expressions to normalize fuzzy inputs.
* All reminder/trigger logic is designed to be asynchronous.
* ElevenLabs streaming TTS significantly reduces output latency.
* Session-level metrics are logged in both MongoDB and local JSON.
* Emotion detection is currently rule-based and extendable with ML models.

## Contributing

Contributions are welcome. Please open an issue before submitting substantial changes. Pay special attention to timezone handling and async-safe design when working on scheduling modules.

## License

MIT License © 2025 – Islington Robotica Team
