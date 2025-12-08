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
    validate_recipe_schema,
    RecipeScraperError,
    RecipeNotFoundError,
    RecipeValidationError
)
from services.ai_assistant import AIAssistant, APIKeyMissingError, AIAssistantError
import json
from pathlib import Path
import os

app = Flask(__name__)
planner = MenuPlanner("recipes.json")

# Initialize AI assistant (will be None if no API key is configured)
try:
    ai_assistant = AIAssistant()
except (ValueError, APIKeyMissingError):
    ai_assistant = None
    print("Warning: GEMINI_API_KEY not found. AI assistant features will be disabled.")
    print("Get your free API key from https://aistudio.google.com/app/apikey")


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/recipes')
def recipes():
    """Render the recipe library page."""
    return render_template('recipes.html')


@app.route('/api/generate-plan', methods=['POST'])
def generate_plan():
    """API endpoint to generate a meal plan."""
    try:
        data = request.json

        household_size = int(data.get('household_size', 2))
        nights = int(data.get('nights', 3))
        preference = data.get('cooking_time_preference', 'mixed')
        selected_recipe_ids = data.get('selected_recipe_ids', [])

        # Validate inputs
        if household_size < 1:
            return jsonify({'error': 'Household size must be at least 1'}), 400

        if nights < 1 or nights > 7:
            return jsonify({'error': 'Number of nights must be between 1 and 7'}), 400

        if preference not in ['quick', 'long', 'mixed']:
            return jsonify({'error': 'Invalid cooking time preference'}), 400

        # Add selected library recipes to temp_recipes if provided
        if selected_recipe_ids:
            for recipe_id in selected_recipe_ids:
                # Find recipe in permanent library
                recipe = next((r for r in planner.recipes if r['id'] == recipe_id), None)
                if recipe:
                    # Only add if not already in temp_recipes
                    if not any(tr['id'] == recipe_id for tr in planner.temp_recipes):
                        planner.add_temp_recipe(recipe)

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


@app.route('/api/recipes', methods=['POST'])
def add_recipe():
    """API endpoint to add a new recipe manually."""
    try:
        data = request.json

        # Validate required fields
        required_fields = ['name', 'cooking_time', 'servings', 'ingredients', 'steps']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Generate new recipe ID
        recipe_id = planner.get_next_recipe_id()

        # Create recipe object
        new_recipe = {
            'id': recipe_id,
            'name': data['name'].strip(),
            'cooking_time': data['cooking_time'],
            'servings': int(data['servings']),
            'ingredients': data['ingredients'],
            'steps': data['steps']
        }

        # Add optional fields if provided
        if 'source_url' in data and data['source_url']:
            new_recipe['source_url'] = data['source_url']
        if 'image_url' in data and data['image_url']:
            new_recipe['image_url'] = data['image_url']

        # Validate recipe schema
        validate_recipe_schema(new_recipe)

        # Save recipe to file
        planner.save_recipe_to_file(new_recipe)

        return jsonify({
            'success': True,
            'recipe': new_recipe,
            'message': f'Successfully added recipe: {new_recipe["name"]}'
        })

    except RecipeValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/api/recipes', methods=['DELETE'])
def delete_recipes():
    """API endpoint to delete recipes by IDs."""
    try:
        data = request.json
        recipe_ids = data.get('recipe_ids', [])

        if not recipe_ids:
            return jsonify({'error': 'No recipe IDs provided'}), 400

        if not isinstance(recipe_ids, list):
            return jsonify({'error': 'recipe_ids must be an array'}), 400

        # Convert to integers
        recipe_ids = [int(id) for id in recipe_ids]

        # Delete recipes
        deleted_count = planner.delete_recipes_by_ids(recipe_ids)

        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} recipe(s)'
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    """API endpoint for AI-powered recipe recommendations."""
    try:
        # Check if AI assistant is available
        if ai_assistant is None:
            return jsonify({
                'error': 'AI assistant not configured. Please set GEMINI_API_KEY environment variable.',
                'setup_url': 'https://aistudio.google.com/app/apikey'
            }), 503

        data = request.json
        user_message = data.get('message', '').strip()
        conversation_history = data.get('history', [])

        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        # Get AI response and extract recipe URLs
        ai_response, recipe_urls = ai_assistant.chat(user_message, conversation_history)

        return jsonify({
            'success': True,
            'message': ai_response,
            'recipe_urls': recipe_urls,
            'recipe_count': len(recipe_urls)
        })

    except AIAssistantError as e:
        return jsonify({'error': f'AI error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


if __name__ == '__main__':
    import os
    # Use PORT environment variable for deployment platforms (Render, Railway, etc.)
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)

