"""
shopping_list_engine.py

Handles CRUD operations for the shopping list using a JSON file as a persistence layer.

Author: [Your Name], 2025-05-28
"""

import json
from pathlib import Path
import logging

class ShoppingListEngine:
    """
    Manages a user's shopping list (add, remove, fetch, clear) with persistent storage.
    """
    def __init__(self, memory_file='/Users/user/chapo-bot-backend/backend/shopping_list.json'):
        """
        Load existing shopping list or initialize a new one.
        """
        self.memory_path = Path(memory_file)
        self.list = self.load_list()
        logging.info("🛒 ShoppingListEngine initialized.")

    def load_list(self):
        """
        Load the list from disk.
        """
        try:
            if self.memory_path.exists():
                with open(self.memory_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading shopping list: {e}")
        return []

    def save_list(self):
        """
        Persist the current list to disk.
        """
        try:
            with open(self.memory_path, 'w') as f:
                json.dump(self.list, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving shopping list: {e}")

    def add_items(self, items):
        """
        Add items (list or comma-separated string). Avoids duplicates.
        """
        if isinstance(items, str):
            items = [item.strip() for item in items.split(',')]
        count_before = len(self.list)
        for item in items:
            if item.lower() not in [x.lower() for x in self.list]:
                self.list.append(item)
        self.save_list()
        count_added = len(self.list) - count_before
        return f"Added {count_added} item(s) to your shopping list." if count_added else "No new items added (already present)."

    def get_list(self):
        """
        Return the latest shopping list (refreshes from file).
        """
        self.list = self.load_list()
        return self.list

    def clear_list(self):
        """
        Remove all items from the list.
        """
        self.list = []
        self.save_list()
        return "Your shopping list has been cleared."

    def remove_item(self, item):
        """
        Remove an item (case-insensitive). Returns result message.
        """
        item_lower = item.lower()
        for i in self.list:
            if i.lower() == item_lower:
                self.list.remove(i)
                self.save_list()
                return f"Removed '{item}' from your shopping list."
        return f"'{item}' not found in your shopping list."

# Example usage for routers/services:
shopping_list_engine = ShoppingListEngine()

def handle_shopping_intent(intent, entities, user_input):
    """
    Router for shopping list intents.
    """
    if intent == "add_to_shopping_list":
        # Try to get items from entities; fallback to text
        items = []
        if "item" in entities:
            items = [ent.get("value") for ent in entities["item"] if ent.get("value")]
        if not items:
            # fallback: parse from text (very basic)
            text = user_input.replace("add", "").replace("to my shopping list", "").strip()
            items = [t.strip() for t in text.split(",") if t.strip()]
        return shopping_list_engine.add_items(items)
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



# ------- Standalone CLI Test Harness -------
if __name__ == "__main__":
    print("Shopping List Engine CLI Test")
    print("Type: add [items], remove [item], get, clear, or exit")
    engine = ShoppingListEngine()
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() == "exit":
                print("👋 Goodbye!")
                break
            elif user_input.lower().startswith("add "):
                items = user_input[4:]
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


# How it works:
# add apples, oranges, milk → Adds items

# remove apples → Removes "apples"

# get → Prints the list

# clear → Empties the list

# exit → Ends the session