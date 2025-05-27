# chapo_engines/trivia_engine.py

import json
import random
import os

TRIVIA_FILE = "/Users/user/chapo-bot-backend/backend/trivia_questions.json"

def load_trivia_questions():
    if not os.path.exists(TRIVIA_FILE):
        return []
    with open(TRIVIA_FILE, "r") as f:
        return json.load(f)

def format_trivia_question(question):
    options_text = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(question["options"])])
    return f"🤔 {question['question']}\n{options_text}"

def ask_trivia_question(session_id, session_memory):
    questions = load_trivia_questions()
    if not questions:
        return "❗ No trivia questions are available."
    question = random.choice(questions)
    session = session_memory.setdefault(session_id, {})
    session["pending_trivia_answer"] = question
    return format_trivia_question(question)

def check_trivia_answer(user_input, session_id, session_memory):
    session = session_memory.setdefault(session_id, {})
    current = session.get("pending_trivia_answer")
    if not current:
        return "❗ No trivia question has been asked yet. Say 'Let's play trivia' to start."

    correct = current["answer"].strip().lower()
    user_ans = user_input.strip().lower()

    options = [opt.strip().lower() for opt in current["options"]]
    option_letters = [chr(65 + i).lower() for i in range(len(options))]
    guessed_letter = None
    for letter in option_letters:
        if f"{letter}." in user_ans or f"{letter} " in user_ans or user_ans.strip() == letter:
            guessed_letter = letter
            break

    # Remove the trivia from memory regardless of outcome
    session.pop("pending_trivia_answer", None)

    prompt_next = "You could say something like, 'Tell me the next trivia question.'"

    if user_ans == correct:
        return f"🎉 Correct! Well done. {prompt_next}"
    if guessed_letter:
        idx = option_letters.index(guessed_letter)
        if options[idx] == correct:
            return f"🎉 Correct! Well done. {prompt_next}"
    if any(correct == opt and opt in user_ans for opt in options):
        return f"🎉 Correct! Well done. {prompt_next}"
    if correct in user_ans:
        return f"🎉 Correct! Well done. {prompt_next}"

    return f"❌ Oops, the correct answer was '{current['answer']}'. {prompt_next}"


# Optionally: A handle_trivia for backward compatibility
def handle_trivia(intent, user_input, session_id, session_memory):
    if session_id not in session_memory:
        session_memory[session_id] = {}
    if intent in ["play_trivia", "trivia_question", "start_trivia"]:
        return ask_trivia_question(session_id, session_memory)
    if intent == "answer_trivia":
        return check_trivia_answer(user_input, session_id, session_memory)
    return "❓ I'm not sure what you meant. Want to play trivia?"

def handle_trivia_answer(session_id, user_input, session_memory):
    session = session_memory.get(session_id, {})
    current = session.get("current_trivia")
    if not current:
        return "❗ No trivia question has been asked yet. Say 'Let's play trivia' to start."

    correct = current["answer"].strip().lower()
    user_ans = user_input.strip().lower()
    options = [opt.strip().lower() for opt in current["options"]]
    option_letters = [chr(65 + i).lower() for i in range(len(options))]
    guessed_letter = None
    for letter in option_letters:
        if f"{letter}." in user_ans or f"{letter} " in user_ans or user_ans.strip() == letter:
            guessed_letter = letter
            break

    session.pop("current_trivia", None)

    prompt_next = "You could say something like, 'Tell me the next trivia question.'"

    if user_ans == correct:
        return f"🎉 Correct! Well done. {prompt_next}"
    if guessed_letter:
        idx = option_letters.index(guessed_letter)
        if options[idx] == correct:
            return f"🎉 Correct! Well done. {prompt_next}"
    if any(correct == opt and opt in user_ans for opt in options):
        return f"🎉 Correct! Well done. {prompt_next}"
    if correct in user_ans:
        return f"🎉 Correct! Well done. {prompt_next}"

    return f"❌ Oops, the correct answer was '{current['answer']}'. {prompt_next}"

