Absolutely! Here’s an **updated README** for your Chapo Bot, reflecting the **new reminder/alarms engine (async, timezone-aware), improved intent fallback, robust shopping, metrics, and enhanced architecture** as per your recent work.

Key changes:

* Reminders & alarms are now fully implemented, async, and timezone robust (Europe/London, BST).
* GPT fallback logic is clarified in the pipeline and usage.
* Shopping list/intent keyword fallback and all new features are properly described.
* Bugfix notes and best-practices are mentioned for contributors.
* File list and project architecture reflect your actual codebase.

---

````markdown
# Chapo Bot – Voice-Controlled Humanoid Home Assistant

Chapo is a next-generation voice-controlled home assistant built with Whisper, Wit.ai, HuggingFace, and a modular “engine” system. It supports real-time conversation, multi-turn logic, robust intent fallback, emotion detection, shopping lists, reminders/alarms, and more—backed by MongoDB and extensible by design.

---

##  Features

###  Core Features (Implemented)
- **Voice Recognition**: Real-time transcription via Whisper + PyAudio/Pygame  
- **Intent Detection**: Wit.ai (primary), HuggingFace (zero-shot fallback), and OpenAI GPT fallback for open-ended queries  
- **GPT Fallback**: Seamlessly handles unclear/unknown queries with GPT-4  
- **Emotion Detection**: Real-time speech and (optionally) facial emotion analysis  
- **Reminders & Alarms**: Persistent, async, timezone-aware (BST/Europe-London), notification & sound  
- **Shopping List**: Add, check, remove, and clear with persistent JSON storage  
- **News**: Real-time headlines with keyword fallback  
- **MongoDB Logging**: All interactions and evaluation metrics, for precision/recall reporting  
- **Evaluation**: Tracks accuracy, precision, and recall for every interaction

###  Planned Integrations
- **IoT Control**: Home Assistant and device APIs  
- **Music Playback**: Spotify integration (Spotipy)  
- **Object Detection**: YOLOv8 + OpenCV camera feed  
- **Dashboard**: Streamlit/Dash real-time insights  
- **Location & Maps**: Google Maps API  
- **Calendar Sync**: Google Calendar for reminders/events  

---

##  System Architecture

```mermaid
graph TD
    UserVoice[ User Voice Input]
    Whisper[ Whisper STT]
    Wit[ Wit.ai Intent Detection]
    HuggingFace[ HuggingFace Fallback]
    GPT[ OpenAI GPT Fallback]
    Router[ Intent Router & Fallbacks]
    Engines[ Chapo Modular Engines]
    DB[ MongoDB Logging]
    Camera[ Vision Engine]
    Emotion[ Emotion Detector]
    Notification[ Async Reminders/Alarms]
    
    UserVoice --> Whisper
    Whisper --> Wit
    Wit --> Router
    Router --> Engines
    Router --> HuggingFace
    Router --> GPT
    Engines --> Notification
    Engines --> DB
    Camera --> Emotion
    Emotion --> Router
````

---

## Tech Stack

| Category      | Technology                               |
| ------------- | ---------------------------------------- |
| **Language**  | Python 3.12+                             |
| **Backend**   | FastAPI                                  |
| **NLP**       | Whisper, Wit.ai, HuggingFace, OpenAI GPT |
| **Voice I/O** | PyAudio, Pygame, gTTS, pyttsx3           |
| **Storage**   | MongoDB, JSON                            |
| **Vision**    | OpenCV, YOLOv8, ONNX                     |
| **Dev Tools** | dotenv, asyncio, logging, pytz           |
| **Testing**   | pytest, custom eval scripts              |

---

## Project Structure

```
chapo-bot-backend/
├── backend/
│   ├── app.py / main.py                  # FastAPI entrypoints
│   ├── test_voice.py                     # 🎙️ Voice CLI main loop
│   ├── response_generator.py             # Multi-turn & GPT fallback logic
│   ├── emotion_detector.py               # Speech & facial emotion analysis
│   ├── realtime_emotion_detect.py        # Webcam-based FER
│   ├── realtime_object_detect.py         # YOLOv8 + OpenCV
│   ├── spotify_handler.py                # Spotipy auth & playback
│   ├── shopping_list_engine.py           # JSON-based shopping manager
│   ├── reminder_engine.py                # Async, timezone-safe reminders & alarms
│   ├── alarm_engine.py                   # (If separated: async alarm triggers)
│   ├── feedback.py                       # User feedback logging
│   ├── multi_turn_manager.py             # Session/context tracking
│   ├── evaluate_model.py                 # Precision/recall/F1 metrics
│   └── db/
│       └── mongo.py                      # MongoDB connection & handlers
├── logs/                                  # Raw session & feedback logs
├── requirements.txt                       # Python deps
├── .env.example                           # Sample env vars
└── README.md                              # This file
```

---

## Setup & Usage

1. **Clone & Activate**

   ```bash
   git clone https://github.com/Web8080/chapo-bot-backend.git
   cd chapo-bot-backend
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**

   ```bash
   cp .env.example .env
   # Edit .env with your keys:
   # WIT_TOKEN=...
   # MONGODB_URI=...
   # OPENAI_API_KEY=...
   # (plus others for weather/news/maps/spotify, if used)
   ```

4. **Run Locally**

   ```bash
   python backend/test_voice.py   # Voice CLI interface
   uvicorn backend.app:app --reload   # (Optional: FastAPI app)
   ```

---

## Roadmap

* Home Assistant & IoT device control
* Google Calendar event/reminder sync
* Finalize Spotify integration & robust playback
* More granular, reliable JSON/task storage
* Streamlit/Dash dashboard for real-time evaluation & stats
* YOLO-based object/facial recognition pipeline
* Visual debugger for intent/flow tracing

---

## Challenges & Lessons Learned

* **Timezone Handling:** All reminders/alarms are BST (Europe/London) aware to prevent “offset-naive and offset-aware” datetime bugs.
* **Intent Fallback:** Keyword-based fallback, HuggingFace, and GPT fallback used to maximize robustness—unclear requests get meaningful replies.
* **Shopping List Reliability:** Addressed race conditions and improved item extraction.
* **Async Scheduling:** Alarms/reminders are now triggered with async tasks (no missed triggers on restart).
* **Natural Language Parsing:** Handling of ambiguous or fuzzy date/time phrases improved, but always being refined.
* **Testing:** Built-in precision, recall, F1 scoring after every session for data science evaluation.

---

## Testing & Evaluation

* **Intent Accuracy**:

  ```bash
  python backend/evaluate_model.py
  ```

  Precision/recall/F1-score reports saved in `eval_metrics.py`.

---

## Contributing

Pull requests welcome! For major changes, please open an issue first.

*Please ensure timezone safety and async best practices for reminders and alarms before submitting PRs involving time logic.*

---

## 🪪 License

MIT © 2025 — Islington Robotica Team

```

---

**If you want this even more visual (with a diagram of the Reminder/Alarm async flow, etc), just ask!**
```
