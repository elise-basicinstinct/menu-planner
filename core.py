"""
Menu Planner Core Business Logic

This module contains pure business logic for meal planning with no I/O operations.
All functions return data structures that can be used by any interface (CLI, Web, GUI).
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any


class MenuPlanner:
    """Core business logic for meal planning and recipe management."""

    def __init__(self, recipes_path: str = "recipes.json"):
        """
        Initialize the menu planner with recipes.

        Args:
            recipes_path: Path to recipes JSON file
        """
        self.recipes_path = Path(recipes_path)
        self.recipes = self._load_recipes()
        self.temp_recipes = []  # Temporary recipes for current session only

    def _load_recipes(self) -> List[Dict[str, Any]]:
        """Load recipes from JSON file."""
        with open(self.recipes_path, "r") as f:
            return json.load(f)

    def filter_recipes(self, preference: str) -> List[Dict[str, Any]]:
        """
        Filter recipes based on cooking time preference.
        Includes both permanent and temporary recipes.

        Args:
            preference: "quick", "long", or "mixed"

        Returns:
            Filtered list of recipes
        """
        # Combine permanent and temporary recipes
        all_recipes = self.recipes + self.temp_recipes

        if preference == "mixed":
            return all_recipes
        return [r for r in all_recipes if r["cooking_time"] == preference]

    def select_recipes(self, nights: int, preference: str) -> tuple[List[Dict[str, Any]], bool]:
        """
        Select recipes for the meal plan based on preferences.

        Args:
            nights: Number of nights to plan for
            preference: Cooking time preference

        Returns:
            Tuple of (selected recipes, had_to_add_other_category)
        """
        filtered = self.filter_recipes(preference)
        had_to_mix = False

        # If insufficient recipes, add from other category
        if len(filtered) < nights and preference != "mixed":
            had_to_mix = True
            other_pref = "long" if preference == "quick" else "quick"
            other_recipes = self.filter_recipes(other_pref)
            filtered.extend(other_recipes)

        # Randomly select recipes without replacement
        selected = random.sample(filtered, min(nights, len(filtered)))
        return selected, had_to_mix

    def scale_recipe(self, recipe: Dict[str, Any], household_size: int) -> Dict[str, Any]:
        """
        Scale recipe ingredients based on household size.

        Args:
            recipe: Recipe dictionary
            household_size: Number of people to serve

        Returns:
            Recipe with scaled ingredients
        """
        scaled_recipe = recipe.copy()
        scale_factor = household_size / recipe["servings"]

        scaled_ingredients = []
        for ingredient in recipe["ingredients"]:
            scaled_ingredient = ingredient.copy()
            scaled_ingredient["amount"] = round(ingredient["amount"] * scale_factor, 1)
            scaled_ingredients.append(scaled_ingredient)

        scaled_recipe["ingredients"] = scaled_ingredients
        scaled_recipe["scaled_servings"] = household_size
        return scaled_recipe

    def aggregate_shopping_list(self, menu: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        Aggregate ingredients from all recipes into a shopping list.

        Args:
            menu: List of recipes in the meal plan

        Returns:
            Dictionary mapping ingredient names to {amount, unit}
        """
        shopping_list = {}

        for recipe in menu:
            for ingredient in recipe["ingredients"]:
                name = ingredient["name"]
                amount = ingredient["amount"]
                unit = ingredient["unit"]

                if name not in shopping_list:
                    shopping_list[name] = {"amount": 0, "unit": unit}

                # Simple aggregation - assumes same units
                shopping_list[name]["amount"] += amount

        # Round amounts for cleaner display
        for item in shopping_list.values():
            item["amount"] = round(item["amount"], 1)

        return shopping_list

    def generate_plan(self, household_size: int, nights: int,
                     preference: str) -> Dict[str, Any]:
        """
        Generate a complete meal plan.

        Args:
            household_size: Number of people to serve
            nights: Number of nights to plan for (1-7)
            preference: Cooking time preference ("quick", "long", "mixed")

        Returns:
            Dictionary containing:
                - preferences: User input preferences
                - menu: List of scaled recipes
                - shopping_list: Aggregated ingredients
                - warnings: List of warning messages (if any)
        """
        # Select recipes
        selected_recipes, had_to_mix = self.select_recipes(nights, preference)

        # Scale recipes for household size
        menu = [
            self.scale_recipe(recipe, household_size)
            for recipe in selected_recipes
        ]

        # Generate shopping list
        shopping_list = self.aggregate_shopping_list(menu)

        # Build result
        plan = {
            "preferences": {
                "household_size": household_size,
                "nights": nights,
                "cooking_time_preference": preference
            },
            "menu": menu,
            "shopping_list": shopping_list,
            "warnings": []
        }

        # Add warning if we had to mix categories
        if had_to_mix:
            filtered_count = len(self.filter_recipes(preference))
            other_pref = "quick" if preference == "long" else "long"
            plan["warnings"].append(
                f"Only {filtered_count} {preference} recipes available. "
                f"Added some {other_pref} recipes."
            )

        return plan

    def add_temp_recipe(self, recipe: Dict[str, Any]) -> None:
        """
        Add a recipe to the temporary recipe list for current session only.
        Temporary recipes are included in plan generation but not persisted.

        Args:
            recipe: Recipe dictionary (must be validated before calling)
        """
        self.temp_recipes.append(recipe)

    def clear_temp_recipes(self) -> None:
        """Clear all temporary recipes from current session."""
        self.temp_recipes = []

    def get_next_recipe_id(self) -> int:
        """
        Generate the next available recipe ID.

        Returns:
            Next sequential ID number
        """
        all_recipes = self.recipes + self.temp_recipes
        if not all_recipes:
            return 1

        max_id = max(recipe["id"] for recipe in all_recipes)
        return max_id + 1

    def save_recipe_to_file(self, recipe: Dict[str, Any],
                           file_path: str = None) -> None:
        """
        Save a recipe permanently to the recipes JSON file.
        Validates recipe schema and checks for duplicates before saving.

        Args:
            recipe: Recipe dictionary to save
            file_path: Path to recipes file (defaults to self.recipes_path)

        Raises:
            ValueError: If recipe fails validation or is a duplicate
        """
        from services.web_scraper import validate_recipe_schema

        # Validate recipe schema
        validate_recipe_schema(recipe)

        # Use default path if none provided
        if file_path is None:
            file_path = str(self.recipes_path)

        # Load current recipes
        path = Path(file_path)
        if path.exists():
            with open(path, "r") as f:
                existing_recipes = json.load(f)
        else:
            existing_recipes = []

        # Check for duplicate by name (case-insensitive)
        recipe_name_lower = recipe["name"].lower()
        for existing in existing_recipes:
            if existing["name"].lower() == recipe_name_lower:
                raise ValueError(
                    f"Recipe '{recipe['name']}' already exists in {file_path}"
                )

        # Append recipe
        existing_recipes.append(recipe)

        # Save back to file with pretty formatting
        with open(path, "w") as f:
            json.dump(existing_recipes, f, indent=2)

        # Reload recipes to include the new one
        self.recipes = self._load_recipes()

    def save_temp_recipes_to_file(self, file_path: str = None) -> int:
        """
        Save all temporary recipes permanently to the recipes JSON file.

        Args:
            file_path: Path to recipes file (defaults to self.recipes_path)

        Returns:
            Number of recipes successfully saved

        Raises:
            ValueError: If any recipe fails validation or is a duplicate
        """
        if not self.temp_recipes:
            return 0

        saved_count = 0
        for recipe in self.temp_recipes:
            try:
                self.save_recipe_to_file(recipe, file_path)
                saved_count += 1
            except ValueError:
                # Skip duplicates but continue with others
                pass

        # Clear temp recipes after saving
        self.clear_temp_recipes()

        return saved_count
