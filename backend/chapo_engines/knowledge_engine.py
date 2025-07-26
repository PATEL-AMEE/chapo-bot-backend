# chapo_engines/knowledge_engine.py

import os
import wikipedia
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

WOLFRAMALPHA_APP_ID = os.getenv("WOLFRAMALPHA_APP_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


def query_wolframalpha(question):
    try:
        url = "http://api.wolframalpha.com/v1/result"
        params = {"appid": WOLFRAMALPHA_APP_ID, "i": question}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.text.strip()
            if result and "Wolfram|Alpha" not in result:
                print("[Wolfram Result]:", result)
                return result
            else:
                print("[Wolfram Returned Empty or Branding]")
    except Exception as e:
        print(f"[Wolfram Error]: {e}")
    return None


def query_wikipedia(topic):
    try:
        topic = topic.strip().title()
        summary = wikipedia.summary(topic, sentences=2, auto_suggest=True)
        print("[Wikipedia Result]:", summary)
        return summary
    except wikipedia.DisambiguationError as e:
        print(f"[Wiki Disambiguation]: Trying first option: {e.options[0]}")
        try:
            summary = wikipedia.summary(e.options[0], sentences=2, auto_suggest=True)
            print("[Wikipedia Disambiguation Resolved]:", summary)
            return summary
        except Exception as inner_e:
            print(f"[Secondary Wiki Error]: {inner_e}")
    except wikipedia.PageError:
        print("[Wikipedia Page Not Found]")
    except Exception as e:
        print(f"[Wiki Error]: {e}")
    return None


def fallback_with_openai_gpt(question):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are Chapo, a helpful assistant. Give short and factual answers to general knowledge questions."
                },
                {"role": "user", "content": question}
            ],
            temperature=0.5,
            max_tokens=100
        )
        answer = response.choices[0].message.content.strip()
        print("[GPT Fallback Answer]:", answer)
        return answer
    except Exception as e:
        print(f"[OpenAI Fallback Error]: {e}")
        return "Sorry, I couldn't find the answer."


def get_knowledge_answer(question):
    print(f"\U0001f9e0 Searching for: {question}")

    # Try WolframAlpha first
    result = query_wolframalpha(question)
    if result:
        print("[Wolfram Success]")
        return result
    else:
        print("[Wolfram Failed or No Answer]")

    # Try Wikipedia next
    result = query_wikipedia(question)
    if result:
        print("[Wikipedia Success]")
        return result
    else:
        print("[Wikipedia Failed or No Answer]")

    # Fallback to GPT if both fail
    print("[Fallback to GPT]")
    return fallback_with_openai_gpt(question)