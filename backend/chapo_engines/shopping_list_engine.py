import json
from pathlib import Path

class ShoppingListEngine:
    """
    Engine for managing a shopping list using a JSON file as persistent memory.
    Supports adding, removing, retrieving, and clearing items on the list.
    """

    def __init__(self, memory_file='/Users/user/chapo-bot-backend/backend/shopping_list.json'):
        """
        Initialize the ShoppingListEngine.
        Loads the existing shopping list from file, or creates a new list if file doesn't exist.
        """
        self.memory_path = Path(memory_file)  # Path to the JSON file used as memory
        self.list = self.load_list()          # Load shopping list into memory

    def load_list(self):
        """
        Load the shopping list from the JSON file.
        Returns an empty list if the file does not exist.
        """
        if self.memory_path.exists():
            with open(self.memory_path, 'r') as f:
                return json.load(f)
        return []

    def save_list(self):
        """
        Save the current shopping list to the JSON file.
        """
        with open(self.memory_path, 'w') as f:
            json.dump(self.list, f, indent=2)

    def add_items(self, items):
        """
        Add one or more items to the shopping list.
        Accepts a string of comma-separated items or a list of items.
        Avoids duplicates (case-insensitive).
        Saves the updated list to memory.
        Returns a confirmation message.
        """
        if isinstance(items, str):
            items = [item.strip() for item in items.split(',')]
        for item in items:
            if item.lower() not in [x.lower() for x in self.list]:
                self.list.append(item)
        self.save_list()
        return f"Added {', '.join(items)} to your shopping list."

    def get_list(self):
        """
        Retrieve the current shopping list from file.
        Reads directly from file for latest version.
        Returns the list (can be empty).
        """
        if self.memory_path.exists():
            with open(self.memory_path, 'r') as f:
                return json.load(f)
        return []

    def clear_list(self):
        """
        Clear all items from the shopping list.
        Saves the empty list to memory.
        Returns a confirmation message.
        """
        self.list = []
        self.save_list()
        return "Your shopping list has been cleared."

    def remove_item(self, item):
        """
        Remove a specific item from the shopping list (case-insensitive).
        Saves the updated list to memory.
        Returns a confirmation message or a not-found message.
        """
        item_lower = item.lower()
        for i in self.list:
            if i.lower() == item_lower:
                self.list.remove(i)
                self.save_list()
                return f"Removed {item} from your shopping list."
        return f"{item} was not found on your list."


# Instantiate the engine globally (only once)
shopping_list_engine = ShoppingListEngine()

# Utility function to add items to the shopping list
def save_to_shopping_list(items):
    """
    Add items to the shopping list using the global engine.
    Returns the engine's confirmation message.
    """
    return shopping_list_engine.add_items(items)

# Utility function to load the shopping list
def load_shopping_list():
    """
    Retrieve the current shopping list from memory.
    Returns the in-memory list (could be stale if file changed externally).
    """
    return shopping_list_engine.list

# Utility function to clear the shopping list
def clear_shopping_list():
    """
    Clear all items from the shopping list using the global engine.
    Returns the engine's confirmation message.
    """
    return shopping_list_engine.clear_list()
