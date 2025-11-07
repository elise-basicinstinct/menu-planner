#!/usr/bin/env python3
"""
Manual Recipe Entry Tool

For websites like Coles that block automated scraping,
use this script to quickly add recipes by copy-pasting.
"""

import json
from pathlib import Path
from core import MenuPlanner

def add_recipe_interactive():
    """Interactive recipe entry via command line."""
    print("="*60)
    print("MANUAL RECIPE ENTRY")
    print("="*60)
    print("For sites like Coles that block automated scraping\n")

    # Get recipe name
    name = input("Recipe name: ").strip()
    if not name:
        print("Error: Recipe name is required")
        return

    # Get servings
    while True:
        try:
            servings = int(input("Servings (e.g., 4): ").strip() or "4")
            if servings > 0:
                break
            print("Servings must be positive")
        except ValueError:
            print("Please enter a number")

    # Get cooking time
    while True:
        cooking_time = input("Cooking time (quick/long): ").strip().lower()
        if cooking_time in ['quick', 'long']:
            break
        print("Please enter 'quick' or 'long'")

    # Get ingredients
    print("\nIngredients (one per line, format: '2 cups flour' or just 'salt')")
    print("Press Enter on empty line when done:")
    ingredients = []
    while True:
        ing = input("  ").strip()
        if not ing:
            break
        ingredients.append(ing)

    if not ingredients:
        print("Error: At least one ingredient is required")
        return

    # Get steps
    print("\nCooking steps (one per line)")
    print("Press Enter on empty line when done:")
    steps = []
    while True:
        step = input("  ").strip()
        if not step:
            break
        steps.append(step)

    if not steps:
        print("Error: At least one step is required")
        return

    # Parse ingredients to structured format
    from services.web_scraper import parse_ingredients

    parsed_ingredients = parse_ingredients(ingredients)

    # Create recipe object
    planner = MenuPlanner('recipes.json')
    recipe = {
        "id": planner.get_next_recipe_id(),
        "name": name,
        "cooking_time": cooking_time,
        "servings": servings,
        "ingredients": parsed_ingredients,
        "steps": steps
    }

    # Show summary
    print("\n" + "="*60)
    print("RECIPE SUMMARY")
    print("="*60)
    print(f"Name: {recipe['name']}")
    print(f"Servings: {recipe['servings']}")
    print(f"Cooking time: {recipe['cooking_time']}")
    print(f"Ingredients: {len(recipe['ingredients'])}")
    print(f"Steps: {len(recipe['steps'])}")

    # Confirm
    confirm = input("\nSave this recipe? (y/n): ").lower().strip()
    if confirm in ['y', 'yes']:
        try:
            planner.save_recipe_to_file(recipe)
            print(f"\n✓ Successfully saved recipe #{recipe['id']}: {recipe['name']}")
            print(f"  Saved to: {Path('recipes.json').absolute()}")
        except Exception as e:
            print(f"\n✗ Error saving recipe: {e}")
    else:
        print("\n✗ Recipe not saved")


if __name__ == "__main__":
    try:
        add_recipe_interactive()
    except KeyboardInterrupt:
        print("\n\nCancelled")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
