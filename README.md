````markdown
# Chapo Bot – Voice-Controlled Humanoid Home Assistant

Chapo is an advanced voice-controlled home assistant built with Whisper, Wit.ai, HuggingFace, and modular intent engines. It supports real-time voice interaction, emotion detection, smart home control, music playback, shopping list and reminder management, and more—backed by MongoDB logging and easily extensible with new “engines.”

---

##  Features

###  Core Features (Implemented)
- **Voice Recognition**: Real-time transcription via Whisper + PyAudio/Pygame  
- **Intent Detection**: Wit.ai primary, HuggingFace fallback  
- **GPT Fallback**: OpenAI GPT for open-ended queries  
- **Emotion Detection**: Facial & speech emotion analysis  
- **Shopping List**: Persistent JSON storage & retrieval
- **Real time news**
- **MongoDB Logging**: Stores all interactions & evaluation metrics  

###  Planned Integrations
- **Reminders & Alarms**: Google Calendar API  
- **IoT Control**: Home Assistant token & APIs  
- **Music Playback**: Spotify integration (Spotipy)  
- **Object Detection**: YOLOv8 + OpenCV camera feed  
- **Dashboard**: Streamlit/Dash real-time insights  
- **Location & Maps**: Google Maps API  

---

##  System Architecture

```mermaid
graph TD
    UserVoice[ User Voice Input]
    Whisper[ Whisper STT]
    Wit[ Wit.ai Intent Detection]
    GPT[ GPT Fallback]
    Router[ Intent Router]
    Engines[ Chapo Engines]
    DB[ MongoDB Logs]
    Camera[ Vision Engine]
    Emotion[ Emotion Detector]

    UserVoice --> Whisper
    Whisper --> Wit
    Wit --> Router
    Router --> Engines
    Router --> GPT
    Engines --> DB
    Camera --> Emotion
    Emotion --> Router
````

---

##  Tech Stack

| Category      | Technology                               |
| ------------- | ---------------------------------------- |
| **Language**  | Python 3.12                              |
| **Backend**   | FastAPI                                  |
| **NLP**       | Whisper, Wit.ai, HuggingFace, OpenAI GPT |
| **Voice I/O** | PyAudio, Pygame, gTTS, pyttsx3           |
| **Storage**   | MongoDB, JSON                            |
| **Vision**    | OpenCV, YOLOv8, ONNX                     |
| **Dev Tools** | dotenv, asyncio, logging                 |
| **Testing**   | pytest, custom evaluation scripts        |

---

##  Project Structure

```
chapo-bot-backend/
├── backend/
│   ├── app.py / main.py                  # FastAPI entrypoints
│   ├── test_voice.py                     # 🎙️ Voice loop & intent dispatch
│   ├── realtime_voice.py                 # Streaming voice capture
│   ├── response_generator.py             # Multi-turn & GPT fallback logic
│   ├── emotion_detector.py               # Speech & facial emotion analysis
│   ├── realtime_emotion_detect.py        # Webcam-based FER
│   ├── realtime_object_detect.py         # YOLOv8 + OpenCV
│   ├── spotify_handler.py                # Spotipy auth & playback
│   ├── shopping_list_engine.py           # JSON-based list manager
│   ├── reminder_engine.py                # Reminders & alarms (planned)
│   ├── feedback.py                       # User feedback logging
│   ├── multi_turn_manager.py             # Context tracking
│   ├── evaluate_model.py                 # Precision/recall/F1 metrics
│   └── db/
│       └── mongo.py                      # MongoDB connection & handlers
├── logs/                                  # Raw session & feedback logs
├── requirements.txt                       # Python deps
├── .env.example                           # Sample env vars
└── README.md                              # This file
```

---

##  Setup & Usage

1. **Clone & Activate**

   ```bash
   git clone https://github.com/Web8080/chapo-bot-backend.git
   cd chapo-bot-backend
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**

   ```bash
   # Option A: requirements.txt
   pip install -r requirements.txt

   # Option B: fetch & run installer
   git fetch origin main
   git checkout origin/main -- backend/install_requirements.py
   python backend/install_requirements.py
   ```

3. **Configure Environment**

   ```bash
   cp .env.example .env
   # Edit .env with your credentials:
   # WIT_TOKEN=
   # MONGODB_URI=
   # SPOTIPY_CLIENT_ID=
   # SPOTIPY_CLIENT_SECRET=
   # SPOTIPY_REDIRECT_URI=
   # OPENAI_API_KEY=
   # WEATHER_API_KEY=
   # GOOGLE_CALENDAR_API_KEY=
   # NEWS_API_KEY=
   # GOOGLE_MAPS_API_KEY=
   # HOME_ASSISTANT_TOKEN=
   ```

4. **Run Locally**

   ```bash
   # Voice-only interface
   python backend/test_voice.py

   # (If enabled) FastAPI app
   uvicorn backend.app:app --reload
   ```

---

##  Roadmap

* Home Assistant & IoT device control
* Google Calendar reminders & event sync
* Stabilize Spotify module & token refresh
* JSON storage for tasks & alarms
* Streamlit/Dash dashboard for metrics
* Enhanced YOLO object recognition

---

##  Challenges Faced

* Race conditions updating shopping\_list.json
* Overlapping intents (e.g., “Add milk and remind me…” )
* Spotify auth & token refresh bugs
* GPT fallback responses not triggering actions
* Unreliable natural-language date/time parsing
* Lack of visual UI for debugging flows

---

##  Testing & Evaluation

* **Intent Accuracy**:

  ```bash
  python backend/evaluate_model.py
  ```

  Generates precision, recall, and F1-score reports in `eval_metrics.py`.

---

##  Contributing

Pull requests welcome! For major changes, please open an issue first to discuss the scope.

---

## 🪪 License

MIT © 2025 — Islington Robotica Team

```
```
