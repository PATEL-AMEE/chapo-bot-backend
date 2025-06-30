import json
import re
from pathlib import Path
import logging

class ShoppingListEngine:
    def __init__(self, memory_file='C:/Users/LENOVO/chapo-bot-backend/backend/shopping_list.json'):
        self.memory_path = Path(memory_file)
        self.list = self.load_list()
        logging.info("🛒 ShoppingListEngine initialized.")

    def load_list(self):
        try:
            if self.memory_path.exists():
                with open(self.memory_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading shopping list: {e}")
        return []

    def save_list(self):
        try:
            with open(self.memory_path, 'w') as f:
                json.dump(self.list, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving shopping list: {e}")

    def add_items(self, items):
        if isinstance(items, str):
            items = [items]

        count_before = len(self.list)
        for item in items:
            item_clean = item.strip().lower()
            if item_clean and item_clean not in [x.lower() for x in self.list]:
                self.list.append(item_clean)

        self.save_list()
        count_added = len(self.list) - count_before
        return f"Added {count_added} item(s) to your shopping list." if count_added else "No new items added (already present)."

    def get_list(self):
        self.list = self.load_list()
        return self.list

    def clear_list(self):
        self.list = []
        self.save_list()
        return "Your shopping list has been cleared."

    def remove_item(self, item):
        item_lower = item.lower()
        for i in self.list:
            if i.lower() == item_lower:
                self.list.remove(i)
                self.save_list()
                return f"Removed '{item}' from your shopping list."
        return f"'{item}' not found in your shopping list."


def extract_items_from_text(user_input):
    """
    Cleans natural language and extracts grocery items.
    Removes filler like 'add to my shopping list' and splits items.
    """
    stopwords = {"ads", "ad", "something", "stuff", "thing"}
    text = user_input.lower()

    # Remove common command phrases
    text = re.sub(r"^(add|put|buy|by)\s+", "", text)  # handle 'by bread' voice typo
    text = re.sub(r"\s*(to|into|in|on)?\s*(my|the)?\s*(shopping\s*list)\s*$", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Split into separate items
    raw_items = re.split(r",| and ", text)
    return [item.strip() for item in raw_items if item.strip() and item.strip() not in stopwords]


# Instance of the engine
shopping_list_engine = ShoppingListEngine()
def handle_shopping_intent(intent, entities, user_input):
    if intent == "add_to_shopping_list":
        raw_inputs = []

        # Step 1: Extract from entities, but clean every one
        if "item" in entities:
            for ent in entities["item"]:
                val = ent.get("value", "")
                if val:
                    raw_inputs.append(val)

        # Step 2: If entities failed or missing, use full input
        if not raw_inputs:
            raw_inputs = [user_input]

        # Step 3: Clean EVERYTHING before adding
        cleaned_items = []
        for input_text in raw_inputs:
            cleaned_items.extend(extract_items_from_text(input_text))

        print(f"[DEBUG] Cleaned items: {cleaned_items}")  # Optional: to verify
        return shopping_list_engine.add_items(cleaned_items)

    # Rest of intents...


    elif intent in ["get_shopping_list", "check_shopping_list"]:
        shopping_list = shopping_list_engine.get_list()
        if shopping_list:
            return f"🛒 Your shopping list: {', '.join(shopping_list)}."
        return "Your shopping list is empty."

    elif intent == "clear_shopping_list":
        return shopping_list_engine.clear_list()

    elif intent == "remove_from_shopping_list":
        item = user_input.replace("remove", "").replace("from my shopping list", "").strip()
        return shopping_list_engine.remove_item(item)

    else:
        return "Sorry, I didn't understand that shopping list command."


# CLI test (optional)
if __name__ == "__main__":
    print("🛒 Shopping List Engine CLI Test")
    print("Type: add [items], remove [item], get, clear, or exit")
    engine = ShoppingListEngine()
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() == "exit":
                print("👋 Goodbye!")
                break
            elif user_input.lower().startswith("add "):
                items = extract_items_from_text(user_input)
                print(engine.add_items(items))
            elif user_input.lower().startswith("remove "):
                item = user_input[7:]
                print(engine.remove_item(item))
            elif user_input.lower() == "get":
                lst = engine.get_list()
                print(f"🛒 Current shopping list: {', '.join(lst) if lst else 'Empty.'}")
            elif user_input.lower() == "clear":
                print(engine.clear_list())
            else:
                print("Commands: add [items], remove [item], get, clear, exit")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
