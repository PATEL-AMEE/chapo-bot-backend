"""
trivia_engine.py

Handles trivia question game logic for Chapo: load questions, ask, check answers, and manage session state.
Interns: All trivia state is kept in session_memory; see the function docstrings for details.

Author: [x-tech], 2025-05-28
"""

import json
import random
import os

# Path to JSON file storing trivia questions
TRIVIA_FILE = r"C:\Users\LENOVO\chapo-bot-backend\backend\trivia_questions.json"

def load_trivia_questions():
    """
    Load trivia questions from the persistent JSON file.
    Returns: List of dicts, each with 'question', 'options', 'answer'
    """
    if not os.path.exists(TRIVIA_FILE):
        return []
    with open(TRIVIA_FILE, "r") as f:
        return json.load(f)

def format_trivia_question(question):
    """
    Format a single trivia question for display to user.
    Args:
        question (dict): {'question': str, 'options': [str], ...}
    Returns:
        str: Multi-line string ready for voice/text output.
    """
    options_text = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(question["options"])])
    return f"🤔 {question['question']}\n{options_text}"

def ask_trivia_question(session_id, session_memory):
    """
    Pick a random trivia question and save it to the session.
    Args:
        session_id (str): The user/session identifier
        session_memory (dict): Session dict for storing trivia state
    Returns:
        str: Formatted question to present to user
    """
    questions = load_trivia_questions()
    if not questions:
        return "❗ No trivia questions are available."
    question = random.choice(questions)
    session = session_memory.setdefault(session_id, {})
    session["pending_trivia_answer"] = question
    return format_trivia_question(question)

def check_trivia_answer(user_input, session_id, session_memory):
    """
    Check the user's answer against the stored pending question for their session.
    Args:
        user_input (str): User's raw answer
        session_id (str): User/session identifier
        session_memory (dict): Global session state
    Returns:
        str: Feedback to user
    """
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

    # Multiple checks for robust answer parsing
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

def handle_trivia(intent, user_input, session_id, session_memory):
    """
    Main entrypoint for trivia intents.
    Args:
        intent (str): 'play_trivia', 'trivia_question', 'answer_trivia', etc.
        user_input (str): User's utterance
        session_id (str): Session ID
        session_memory (dict): Session state dict
    Returns:
        str: Bot's response
    """
    if session_id not in session_memory:
        session_memory[session_id] = {}
    if intent in ["play_trivia", "trivia_question", "start_trivia"]:
        return ask_trivia_question(session_id, session_memory)
    if intent == "answer_trivia":
        return check_trivia_answer(user_input, session_id, session_memory)
    return "❓ I'm not sure what you meant. Want to play trivia?"

def handle_trivia_answer(session_id, user_input, session_memory):
    """
    Optional alternate handler for answer flow.
    Not used in most routers (use check_trivia_answer instead).
    """
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


# ------- Standalone CLI Test Harness -------
if __name__ == "__main__":
    print("Trivia Engine CLI Test")
    print("Type: play, answer [your answer], or exit")
    session_id = "cli_test"
    session_memory = {}
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() == "exit":
                print("👋 Goodbye!")
                break
            elif user_input.lower() == "play":
                # Example: "play trivia" (voice), or "start trivia"
                print(ask_trivia_question(session_id, session_memory))
            elif user_input.lower().startswith("answer "):
                # Example: "answer Paris" or "answer B"
                answer = user_input[7:]
                print(check_trivia_answer(answer, session_id, session_memory))
            else:
                print("Commands: play, answer [answer], exit")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

"""
How it works:
- User: play            # (or "Let's play trivia" by voice)
- User: answer Paris    # (or just say "Paris" or "B")
- User: exit
"""
