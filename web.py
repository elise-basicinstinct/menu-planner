"""
Menu Planner Web Interface

Flask web application for the Menu Planner.
Run with: python3 web.py
"""

from flask import Flask, render_template, request, jsonify
from core import MenuPlanner
from services.web_scraper import (
    fetch_recipe_from_url,
    normalize_recipe,
    RecipeScraperError,
    RecipeNotFoundError
)
import json
from pathlib import Path

app = Flask(__name__)
planner = MenuPlanner("recipes.json")


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/generate-plan', methods=['POST'])
def generate_plan():
    """API endpoint to generate a meal plan."""
    try:
        data = request.json
        
        household_size = int(data.get('household_size', 2))
        nights = int(data.get('nights', 3))
        preference = data.get('cooking_time_preference', 'mixed')
        
        # Validate inputs
        if household_size < 1:
            return jsonify({'error': 'Household size must be at least 1'}), 400
        
        if nights < 1 or nights > 7:
            return jsonify({'error': 'Number of nights must be between 1 and 7'}), 400
        
        if preference not in ['quick', 'long', 'mixed']:
            return jsonify({'error': 'Invalid cooking time preference'}), 400
        
        # Generate plan
        plan = planner.generate_plan(household_size, nights, preference)
        
        # Save plan to file
        save_data = {
            "preferences": plan["preferences"],
            "menu": plan["menu"],
            "shopping_list": plan["shopping_list"]
        }
        plan_path = Path(__file__).parent / "last_plan.json"
        with open(plan_path, "w") as f:
            json.dump(save_data, f, indent=2)
        
        return jsonify(plan)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/recipes')
def get_recipes():
    """API endpoint to get all available recipes."""
    try:
        return jsonify(planner.recipes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/import-recipe-url', methods=['POST'])
def import_recipe_url():
    """API endpoint to import a recipe from a URL."""
    try:
        data = request.json
        url = data.get('url', '').strip()

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Fetch recipe from URL
        raw_recipe = fetch_recipe_from_url(url)

        # Normalize to our format
        recipe_id = planner.get_next_recipe_id()
        normalized_recipe = normalize_recipe(raw_recipe, recipe_id)

        # Add to planner as temporary recipe
        planner.add_temp_recipe(normalized_recipe)

        return jsonify({
            'success': True,
            'recipe': normalized_recipe
        })

    except RecipeNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except RecipeScraperError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/api/temp-recipes', methods=['GET'])
def get_temp_recipes():
    """API endpoint to get all temporary recipes."""
    try:
        return jsonify({
            'temp_recipes': planner.temp_recipes,
            'count': len(planner.temp_recipes)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/save-temp-recipes', methods=['POST'])
def save_temp_recipes():
    """API endpoint to save all temporary recipes permanently."""
    try:
        if not planner.temp_recipes:
            return jsonify({'error': 'No temporary recipes to save'}), 400

        saved_count = planner.save_temp_recipes_to_file()

        return jsonify({
            'success': True,
            'saved_count': saved_count,
            'message': f'Successfully saved {saved_count} recipe(s)'
        })

    except Exception as e:
        return jsonify({'error': f'Failed to save recipes: {str(e)}'}), 500


@app.route('/api/clear-temp-recipes', methods=['POST'])
def clear_temp_recipes():
    """API endpoint to clear all temporary recipes."""
    try:
        planner.clear_temp_recipes()
        return jsonify({
            'success': True,
            'message': 'Temporary recipes cleared'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import os
    # Use PORT environment variable for deployment platforms (Render, Railway, etc.)
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)

