import os
import requests

class CookingEngine:
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        self.api_key = os.getenv("SPOONACULAR_API_KEY")
        self.base_url = "https://api.spoonacular.com"
        if not self.api_key:
            print("⚠️ SPOONACULAR_API_KEY not set in .env")

    def get_recipe(self, dish_name):
        if not self.api_key:
            return "❗ Recipe service is not available right now."

        try:
            print(f"[DEBUG] Querying recipe for dish: {dish_name}")

            # Step 1: Search recipes
            response = requests.get(
                f"{self.base_url}/recipes/complexSearch",
                params={
                    "query": dish_name,
                    "number": 1,
                    "apiKey": self.api_key
                }
            )

            if response.status_code == 402:
                return "🔒 I've hit my daily recipe limit. Please try again tomorrow."
            if response.status_code != 200:
                return f"❗ Recipe search error: {response.status_code} — {response.text}"

            data = response.json()
            results = data.get("results", [])
            if not results:
                return f"Sorry, I couldn't find any recipe for {dish_name}."

            recipe = results[0]
            recipe_id = recipe["id"]
            title = recipe.get("title", dish_name)

            # Step 2: Fetch full instructions using recipe ID
            details_response = requests.get(
                f"{self.base_url}/recipes/{recipe_id}/information",
                params={
                    "includeNutrition": False,
                    "apiKey": self.api_key
                }
            )

            if details_response.status_code != 200:
                return f"I found a recipe called {title}, but couldn't fetch the instructions."

            details = details_response.json()
            instructions = details.get("instructions")

            if not instructions or instructions.strip() == "":
                print(f"[DEBUG] Recipe found but no instructions: {title}")
                return f"I found a recipe called {title}, but it doesn't include step-by-step instructions."

            print(f"[DEBUG] Recipe found: {title}")
            return f"Here's how to make {title}: {instructions}"

        except Exception as e:
            print(f"[get_recipe error]: {e}")
            return "❗ I had trouble finding that recipe. Please try again later."

    def suggest_recipe(self, ingredients):
        """
        Suggest up to 3 recipes using one or more ingredients.
        Accepts a string like: 'eggs, cheese'
        """
        if not self.api_key:
            return "❗ Recipe service is not available right now."

        try:
            ingredients = ingredients.lower()
            print(f"[DEBUG] Suggesting recipe with ingredients: {ingredients}")

            response = requests.get(
                f"{self.base_url}/recipes/findByIngredients",
                params={
                    "ingredients": ingredients,
                    "number": 3,
                    "ranking": 1,
                    "apiKey": self.api_key
                }
            )

            if response.status_code == 402:
                return "🔒 Daily limit reached. Try again tomorrow!"
            if response.status_code != 200:
                return f"❗ Suggestion error: {response.status_code}"

            data = response.json()
            if not data:
                return f"Sorry, I couldn't find anything with {ingredients}."

            suggestions = []
            for item in data:
                title = item.get("title")
                if title:
                    suggestions.append(title)

            if not suggestions:
                return f"I found recipes with {ingredients}, but couldn't get the names."

            recipe_list = "\n".join([f"- {r}" for r in suggestions])
            print(f"[DEBUG] Suggested recipes:\n{recipe_list}")

            return f"You can try these recipes using {ingredients}:\n{recipe_list}\nWant instructions for any of them?"

        except Exception as e:
            print(f"[suggest_recipe error]: {e}")
            return "❗ I had trouble suggesting recipes. Try again later."
