# Chapo Bot – Voice-Controlled Humanoid Home Assistant

---

## 🔧 Key Changes

* ✅ Reminders & alarms are now fully implemented, async, and timezone robust (Europe/London, BST).
* 🧠 GPT fallback logic is clarified in the pipeline and usage.
* 🛒 Shopping list/intent keyword fallback and all new features are properly described.
* 🐞 Bugfix notes and best-practices are mentioned for contributors.
* 🗓️ Google Calendar integration added with OAuth, intent parsing, and fuzzy date support.
* 🗣️ ElevenLabs TTS support added for high-quality speech synthesis.
* 📁 File list and project architecture reflect actual codebase.

---

## 💡 Features

### ✅ Core Features (Implemented)

- **Voice Recognition**: Real-time transcription via Whisper + PyAudio/Pygame  
- **Intent Detection**: Wit.ai (primary), HuggingFace (zero-shot fallback), and OpenAI GPT fallback for open-ended queries  
- **GPT Fallback**: Seamlessly handles unclear/unknown queries with GPT-4  
- **Emotion Detection**: Real-time speech and (optionally) facial emotion analysis  
- **Reminders & Alarms**: Persistent, async, timezone-aware (BST/Europe-London), notification & sound  
- **Shopping List**: Add, check, remove, and clear with persistent JSON storage  
- **News**: Real-time headlines with keyword fallback  
- **Google Calendar Integration**: Add events using natural voice commands. Supports fuzzy time/date parsing and timezone-aware scheduling  
- **MongoDB Logging**: All interactions and evaluation metrics, for precision/recall reporting  
- **Advanced TTS**: ElevenLabs Turbo V2 voice synthesis with high-quality, natural-sounding output  
- **Evaluation**: Tracks accuracy, precision, and recall for every interaction

### 🔄 Planned Integrations

- **IoT Control**: Home Assistant and device APIs  
- **Music Playback**: Spotify integration (Spotipy)  
- **Object Detection**: YOLOv8 + OpenCV camera feed  
- **Dashboard**: Streamlit/Dash real-time insights  
- **Location & Maps**: Google Maps API  
- **Calendar Sync**: Deeper Google Calendar bi-directional support  

---

## 🧱 System Architecture

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
    Calendar[ Calendar Engine (Google API)]
    Emotion[ Emotion Detector]
    Notification[ Async Reminders/Alarms]
    TTS[ ElevenLabs TTS Output]

    UserVoice --> Whisper
    Whisper --> Wit
    Wit --> Router
    Router --> Engines
    Router --> HuggingFace
    Router --> GPT
    Engines --> Notification
    Engines --> Calendar
    Engines --> DB
    Engines --> TTS
    Emotion --> Router
```

---

## 🧰 Tech Stack

| Category      | Technology                               |
| ------------- | ---------------------------------------- |
| **Language**  | Python 3.10+                             |
| **Backend**   | FastAPI                                  |
| **NLP**       | Whisper, Wit.ai, HuggingFace, OpenAI GPT |
| **Voice I/O** | PyAudio, Pygame, gTTS, pyttsx3, ElevenLabs |
| **Storage**   | MongoDB, JSON                            |
| **Calendar**  | Google Calendar API (OAuth2)             |
| **Vision**    | OpenCV, YOLOv8, ONNX                     |
| **Dev Tools** | dotenv, asyncio, logging, pytz           |
| **Testing**   | pytest, custom eval scripts              |

---

## 📂 Project Structure

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
│   ├── calendar_engine.py                # 🗓️ NLP-based calendar event creation (Google Calendar)
│   ├── calendar_auth.py                  # 🔐 OAuth2 device flow for Google Calendar API
│   ├── tts_util.py                       # 🗣️ ElevenLabs text-to-speech integration
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

## 🚀 Setup & Usage

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
# ELEVEN_API_KEY=...
# GOOGLE_CLIENT_ID=...
# GOOGLE_CLIENT_SECRET=...
```

4. **Run Locally**

```bash
python backend/test_voice.py         # Voice CLI interface
uvicorn backend.app:app --reload     # (Optional: FastAPI app)
```

---

## 🧪 Testing & Evaluation

### Evaluate Intent Accuracy

```bash
python backend/evaluate_model.py
```

Results saved in `eval_metrics.py`.

---

## 📅 Roadmap

* 🧠 Home Assistant & IoT device control
* 🎵 Finalize Spotify integration & robust playback
* 🧾 More granular, reliable JSON/task storage
* 📊 Streamlit/Dash dashboard for real-time evaluation & stats
* 🧠 YOLO-based object/facial recognition pipeline
* 🔍 Visual debugger for intent/flow tracing
* 📚 Continual Learning
* 🧠 Memory-Augmented Personalization
* 🔍 Retrieval-Augmented Generation (RAG)
* 🌐 Internet-Aware Responses
* 🤖 Auto-Evaluation with Self-Correction

---

## ⚠️ Challenges & Lessons Learned

* **Timezone Handling**: All reminders/alarms are BST (Europe/London) aware to prevent “offset-naive and offset-aware” datetime bugs.
* **Intent Fallback**: Keyword-based fallback, HuggingFace, and GPT fallback used to maximize robustness—unclear requests get meaningful replies.
* **Shopping List Reliability**: Addressed race conditions and improved item extraction.
* **Calendar Parsing**: Fuzzy time phrases (“next Monday at noon”) are normalized for consistent scheduling. Ambiguities are handled via user prompts.
* **Async Scheduling**: Alarms/reminders are now triggered with async tasks (no missed triggers on restart).
* **TTS Performance**: ElevenLabs' streaming API enables high-quality output with minimal delay.
* **Natural Language Parsing**: Handling of ambiguous or fuzzy date/time phrases improved, but always being refined.
* **Testing**: Built-in precision, recall, F1 scoring after every session for data science evaluation.

---

## 🤝 Contributing

Pull requests welcome! For major changes, please open an issue first.

> 🔁 *Please ensure timezone safety and async best practices for reminders and alarms before submitting PRs involving time logic.*

---

## 🪪 License

MIT © 2025 — Islington Robotica Team

