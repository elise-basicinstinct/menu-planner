"""
Menu Planner CLI Interface

This module handles all user interaction for the command-line interface.
It uses the core.MenuPlanner class for business logic.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from core import MenuPlanner
from services.web_scraper import (
    fetch_recipe_from_url,
    normalize_recipe,
    RecipeScraperError,
    RecipeNotFoundError
)


def get_user_input() -> Dict[str, Any]:
    """
    Collect user preferences for meal planning via CLI prompts.

    Returns:
        Dictionary with household_size, nights, and cooking_time_preference
    """
    print("Welcome to Menu Planner!\n")

    # Get household size
    while True:
        try:
            household_size = int(input("How many people in your household? "))
            if household_size > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")

    # Get number of nights
    while True:
        try:
            nights = int(input("How many nights do you need meals for? (1-7): "))
            if 1 <= nights <= 7:
                break
            print("Please enter a number between 1 and 7.")
        except ValueError:
            print("Please enter a valid number.")

    # Get cooking time preference
    while True:
        preference = input("Cooking time preference (quick/long/mixed): ").lower()
        if preference in ["quick", "long", "mixed"]:
            break
        print("Please enter 'quick', 'long', or 'mixed'.")

    return {
        "household_size": household_size,
        "nights": nights,
        "cooking_time_preference": preference
    }


def display_menu(menu: List[Dict[str, Any]]) -> None:
    """
    Display the weekly menu with ingredients and cooking steps.

    Args:
        menu: List of scaled recipes
    """
    print("\n" + "="*60)
    print("YOUR WEEKLY MENU")
    print("="*60)

    for i, recipe in enumerate(menu, 1):
        print(f"\n{'='*60}")
        print(f"NIGHT {i}: {recipe['name'].upper()}")
        print(f"{'='*60}")
        print(f"Cooking time: {recipe['cooking_time']} | Servings: {recipe['scaled_servings']}")

        print(f"\nIngredients:")
        for ingredient in recipe["ingredients"]:
            amount = ingredient["amount"]
            unit = ingredient["unit"]
            name = ingredient["name"]
            print(f"  • {name}: {amount} {unit}")

        if "steps" in recipe:
            print(f"\nCooking Steps:")
            for step_num, step in enumerate(recipe["steps"], 1):
                print(f"  {step_num}. {step}")


def display_shopping_list(shopping_list: Dict[str, Dict[str, float]]) -> None:
    """
    Display the aggregated shopping list.

    Args:
        shopping_list: Dictionary mapping ingredient names to {amount, unit}
    """
    print("\n" + "="*60)
    print("SHOPPING LIST")
    print("="*60)

    sorted_items = sorted(shopping_list.items())
    for name, details in sorted_items:
        amount = details["amount"]
        unit = details["unit"]
        print(f"  • {name}: {amount} {unit}")


def display_warnings(warnings: List[str]) -> None:
    """
    Display warning messages if any.

    Args:
        warnings: List of warning messages
    """
    if warnings:
        for warning in warnings:
            print(f"\nWarning: {warning}")


def save_plan(plan: Dict[str, Any], output_path: str = "last_plan.json") -> None:
    """
    Save the meal plan to a JSON file.

    Args:
        plan: Complete plan dictionary from MenuPlanner
        output_path: Path to save the plan (default: last_plan.json)
    """
    # Remove warnings from saved plan (they're for display only)
    save_data = {
        "preferences": plan["preferences"],
        "menu": plan["menu"],
        "shopping_list": plan["shopping_list"]
    }

    plan_path = Path(__file__).parent / output_path
    with open(plan_path, "w") as f:
        json.dump(save_data, f, indent=2)

    print(f"\n✓ Plan saved to {plan_path}")


def prompt_for_recipe_urls() -> List[str]:
    """
    Prompt user for recipe URLs to import.

    Returns:
        List of URLs entered by user (empty list if none)
    """
    print("\n" + "="*60)
    print("IMPORT RECIPES FROM URLS")
    print("="*60)
    print("Enter recipe URLs (one per line).")
    print("Press Enter on an empty line when done.")
    print("-"*60)

    urls = []
    while True:
        url = input("Recipe URL (or press Enter to finish): ").strip()
        if not url:
            break
        urls.append(url)
        print(f"  ✓ Added: {url}")

    return urls


def import_recipes_from_urls(planner: MenuPlanner, urls: List[str]) -> List[Dict[str, Any]]:
    """
    Import recipes from URLs and add them to the planner as temporary recipes.

    Args:
        planner: MenuPlanner instance
        urls: List of recipe URLs to import

    Returns:
        List of successfully imported recipes
    """
    imported_recipes = []

    print("\n" + "="*60)
    print("IMPORTING RECIPES...")
    print("="*60)

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Fetching: {url}")

        try:
            # Fetch recipe from URL
            raw_recipe = fetch_recipe_from_url(url)

            # Normalize to our format
            recipe_id = planner.get_next_recipe_id()
            normalized_recipe = normalize_recipe(raw_recipe, recipe_id)

            # Add to planner as temporary recipe
            planner.add_temp_recipe(normalized_recipe)
            imported_recipes.append(normalized_recipe)

            print(f"  ✓ Successfully imported: {normalized_recipe['name']}")
            print(f"    - Servings: {normalized_recipe['servings']}")
            print(f"    - Cooking time: {normalized_recipe['cooking_time']}")
            print(f"    - Ingredients: {len(normalized_recipe['ingredients'])}")
            print(f"    - Steps: {len(normalized_recipe['steps'])}")

        except RecipeNotFoundError as e:
            print(f"  ✗ Failed: {str(e)}")
        except RecipeScraperError as e:
            print(f"  ✗ Error: {str(e)}")
        except Exception as e:
            print(f"  ✗ Unexpected error: {str(e)}")

    return imported_recipes


def display_imported_recipes(recipes: List[Dict[str, Any]]) -> None:
    """
    Display summary of imported recipes.

    Args:
        recipes: List of imported recipe dictionaries
    """
    if not recipes:
        print("\nNo recipes were imported.")
        return

    print("\n" + "="*60)
    print(f"SUCCESSFULLY IMPORTED {len(recipes)} RECIPE(S)")
    print("="*60)

    for recipe in recipes:
        print(f"\n• {recipe['name']}")
        print(f"  Cooking time: {recipe['cooking_time']} | Servings: {recipe['servings']}")


def prompt_to_save_recipes(planner: MenuPlanner) -> bool:
    """
    Ask user if they want to save imported recipes permanently.

    Args:
        planner: MenuPlanner instance with temp recipes

    Returns:
        True if recipes were saved, False otherwise
    """
    if not planner.temp_recipes:
        return False

    print("\n" + "="*60)
    print("SAVE IMPORTED RECIPES?")
    print("="*60)
    print(f"\nYou have {len(planner.temp_recipes)} imported recipe(s).")
    print("Would you like to save them permanently to recipes.json?")

    while True:
        choice = input("\nSave recipes? (y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            try:
                saved_count = planner.save_temp_recipes_to_file()
                print(f"\n✓ Successfully saved {saved_count} recipe(s) to recipes.json")
                return True
            except Exception as e:
                print(f"\n✗ Error saving recipes: {str(e)}")
                return False
        elif choice in ['n', 'no']:
            print("\n✓ Recipes not saved (they were only used for this meal plan)")
            planner.clear_temp_recipes()
            return False
        else:
            print("Please enter 'y' or 'n'.")


def run_cli():
    """Main CLI orchestration function."""
    try:
        # Initialize core planner
        planner = MenuPlanner("recipes.json")

        # Ask if user wants to import recipes from URLs
        print("\n" + "="*60)
        while True:
            import_choice = input("Import recipes from URLs? (y/n): ").lower().strip()
            if import_choice in ['y', 'yes', 'n', 'no']:
                break
            print("Please enter 'y' or 'n'.")

        imported_recipes = []
        if import_choice in ['y', 'yes']:
            urls = prompt_for_recipe_urls()
            if urls:
                imported_recipes = import_recipes_from_urls(planner, urls)
                display_imported_recipes(imported_recipes)
            else:
                print("\nNo URLs entered. Continuing with existing recipes...")

        # Get user input
        user_input = get_user_input()

        # Generate plan
        plan = planner.generate_plan(
            user_input["household_size"],
            user_input["nights"],
            user_input["cooking_time_preference"]
        )

        # Display warnings if any
        display_warnings(plan["warnings"])

        # Display results
        display_menu(plan["menu"])
        display_shopping_list(plan["shopping_list"])

        # Save plan
        save_plan(plan)

        # If recipes were imported, ask user if they want to save them
        if imported_recipes:
            prompt_to_save_recipes(planner)

        # Success message
        print("\n" + "="*60)
        print("Happy cooking! 🍳")

    except FileNotFoundError as e:
        print(f"Error: Could not find required file - {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
