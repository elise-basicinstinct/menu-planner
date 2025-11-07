# Menu Planner

A simple Python CLI tool for generating weekly meal plans and shopping lists.

## Features

- Generate meal plans for 1-7 nights
- Scale recipes based on household size
- Filter by cooking time preference (quick/long/mixed)
- **Import recipes from URLs** - Add recipes from any website
- Automatic shopping list aggregation
- Save plans to `last_plan.json` for reference
- Optionally save imported recipes permanently

## Usage

### Command Line Interface (CLI)

Run the CLI application:

```bash
python3 app.py
```

You'll be prompted for:
1. **Household size** - Number of people to cook for
2. **Number of nights** - How many meals to plan (1-7)
3. **Cooking time preference** - Choose from:
   - `quick` - Fast recipes only
   - `long` - Longer cooking time recipes
   - `mixed` - Mix of both

The app will:
- **Optionally prompt to import recipes from URLs** (enter URLs one per line, press Enter to finish)
- Display your weekly menu with detailed ingredients and cooking steps for each recipe
- Generate an aggregated shopping list
- Save the plan to `last_plan.json`
- **Ask if you want to save imported recipes permanently** (only if you imported recipes)

### Web Interface

Run the web application:

```bash
# Install dependencies (first time only)
pip3 install -r requirements.txt

# Start the web server
python3 web.py
```

Then open your browser and navigate to:
```
http://localhost:5001
```

**Note:** Port 5000 is often used by macOS AirPlay Receiver. If you encounter port conflicts, the app uses port 5001 by default.

The web interface provides:
- Beautiful, modern UI for generating meal plans
- **Recipe import from URLs** - Add recipes from any website with automatic scraping
- Interactive form to input preferences
- Visual display of recipes with ingredients and cooking steps
- Organized shopping list
- **Save imported recipes** - Option to keep imported recipes permanently after generating a plan
- Automatic saving to `last_plan.json`

The web app runs on `http://0.0.0.0:5001` by default, making it accessible from other devices on your network.

## Project Structure

```
.
├── app.py              # Entry point (runs the CLI)
├── web.py              # Flask web application
├── core.py             # Business logic (MenuPlanner class)
├── cli.py              # CLI interface (user interaction)
├── services/           # Service modules
│   ├── __init__.py
│   └── web_scraper.py  # Recipe URL scraping and parsing
├── recipes.json        # Recipe database
├── specials.json       # Placeholder for supermarket specials
├── last_plan.json      # Most recent meal plan (auto-generated)
├── requirements.txt   # Python dependencies
├── templates/          # HTML templates for web interface
│   └── index.html
├── static/             # Static files for web interface
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── README.md          # This file
```

### Code Architecture

The application follows a clean separation of concerns:

- **core.py** - Pure business logic with no I/O operations. The `MenuPlanner` class handles recipe selection, scaling, shopping list generation, and recipe import/save functionality. Can be used by any interface (CLI, Web, GUI).

- **cli.py** - Command-line interface that handles user input/output. Uses `MenuPlanner` for all business logic and `web_scraper` for recipe imports.

- **app.py** - Simple entry point that launches the CLI interface.

- **services/web_scraper.py** - Recipe scraping service that fetches recipes from URLs using schema.org structured data. Handles parsing, normalization, and validation of imported recipes.

## Data Files

### recipes.json
Contains recipe data with:
- Recipe name and ID
- Cooking time category (quick/long)
- Base servings
- Ingredients with amounts and units
- Step-by-step cooking instructions

### specials.json
Placeholder for future feature to bias recipe selection based on supermarket specials.

### last_plan.json
Auto-generated file containing:
- User preferences
- Selected menu with scaled recipes
- Aggregated shopping list

## Extending the Application

The code is structured for easy extension. The separation between `core.py` (business logic) and `cli.py` (interface) means:

- New features added to `core.py` automatically work with any interface
- Multiple interfaces (Web, GUI, API) can share the same core logic
- Business logic can be tested independently of UI

### Planned Extensions

**Favorites System:**
- Add favorites tracking to `core.py`
- Modify `select_recipes()` to prioritize favorites
- Update `cli.py` to allow marking recipes as favorites

**External Recipe Import:**
- Add `import_recipe(url)` method to `MenuPlanner`
- Validate against recipe schema
- Append to `recipes.json`

**Supermarket Specials:**
- Populate `specials.json` with ingredient discounts
- Add `score_recipe_by_specials()` to `core.py`
- Weight recipe selection by specials score

**AI Recipe Generation:**
- Create `services/ai_recipes.py` module
- Generate custom recipes based on constraints
- Integrate with `MenuPlanner` class

### Adding Alternative Interfaces

To add a new interface (Web, GUI, etc.):
1. Import `MenuPlanner` from `core.py`
2. Create your interface-specific code
3. Call `planner.generate_plan()` for business logic
4. Display results in your interface format

Example for a web interface:
```python
from core import MenuPlanner
from flask import Flask, render_template, request

app = Flask(__name__)
planner = MenuPlanner('recipes.json')

@app.route('/generate', methods=['POST'])
def generate():
    plan = planner.generate_plan(
        int(request.form['household_size']),
        int(request.form['nights']),
        request.form['preference']
    )
    return render_template('menu.html', plan=plan)
```

## Requirements

### CLI Application
- Python 3.6+
- `recipe-scrapers` 15.9.0+ (for URL import feature)
- Install via `pip3 install -r requirements.txt`

### Web Application
- Python 3.6+
- Flask 3.0.0+
- `recipe-scrapers` 15.9.0+
- Install via `pip3 install -r requirements.txt`

## Recipe URL Import Feature

### How It Works

Both the CLI and Web interfaces support importing recipes from URLs. The app uses the `recipe-scrapers` library to automatically extract recipe information from websites that include schema.org Recipe structured data.

**Supported Websites:** Over 500+ popular recipe websites including AllRecipes, Food Network, Bon Appétit, Serious Eats, and many more.

### CLI Workflow

1. When you run the app, it asks: "Import recipes from URLs? (y/n)"
2. If yes, enter recipe URLs one per line (press Enter on empty line to finish)
3. The app fetches and validates each recipe
4. Imported recipes are used for the current meal plan generation
5. After showing the plan, you're asked: "Save recipes? (y/n)"
   - **Yes** - Recipes are permanently added to `recipes.json`
   - **No** - Recipes are discarded after this session

### Web Workflow

1. At the top of the page, there's a "📥 Import Recipes from URLs" section
2. Enter a recipe URL and click "Import Recipe"
3. Successfully imported recipes appear as cards below the input
4. Generate your meal plan as usual
5. After plan generation, a modal asks: "Save imported recipes?"
   - **Yes, Save Them** - Recipes are permanently added to `recipes.json`
   - **No, Discard** - Recipes are cleared and not saved

### Recipe Normalization

Imported recipes are automatically normalized to match the app's format:
- Cooking time is categorized as "quick" (≤30 min) or "long" (>30 min)
- Instructions are parsed into numbered steps
- Ingredients are extracted with amounts and units
- Recipes are assigned unique IDs
- Optional metadata (source URL, image URL) is preserved

## Example Output

```
Welcome to Menu Planner!

============================================================
Import recipes from URLs? (y/n): y

============================================================
IMPORT RECIPES FROM URLS
============================================================
Enter recipe URLs (one per line).
Press Enter on an empty line when done.
------------------------------------------------------------
Recipe URL (or press Enter to finish): https://example.com/recipe
  ✓ Added: https://example.com/recipe
Recipe URL (or press Enter to finish):

============================================================
IMPORTING RECIPES...
============================================================

[1/1] Fetching: https://example.com/recipe
  ✓ Successfully imported: Thai Green Curry
    - Servings: 4
    - Cooking time: quick
    - Ingredients: 8
    - Steps: 9

============================================================
SUCCESSFULLY IMPORTED 1 RECIPE(S)
============================================================

• Thai Green Curry
  Cooking time: quick | Servings: 4

How many people in your household? 2
How many nights do you need meals for? (1-7): 3
Cooking time preference (quick/long/mixed): quick

============================================================
YOUR WEEKLY MENU
============================================================

============================================================
NIGHT 1: THAI GREEN CURRY
============================================================
Cooking time: quick | Servings: 2

Ingredients:
  • chicken breast: 125.0 g
  • coconut milk: 100.0 ml
  • green curry paste: 12.5 g
  • rice: 75.0 g
  • bamboo shoots: 50.0 g
  • Thai basil: 7.5 g

Cooking Steps:
  1. Cook rice according to package directions
  2. Cut chicken into bite-sized pieces
  3. Heat oil in a wok or large pan
  ...

============================================================
NIGHT 2: SPAGHETTI CARBONARA
============================================================
Cooking time: quick | Servings: 2

Ingredients:
  • spaghetti: 200.0 g
  • bacon: 100.0 g
  ...

...

============================================================
SHOPPING LIST
============================================================
  • bamboo shoots: 50.0 g
  • bacon: 100.0 g
  • chicken breast: 125.0 g
  • coconut milk: 100.0 ml
  • eggs: 2.0 pcs
  • green curry paste: 12.5 g
  • rice: 75.0 g
  • spaghetti: 200.0 g
  • Thai basil: 7.5 g
  ...

✓ Plan saved to /Users/eliseverdonck/Desktop/CC_menu_app/last_plan.json

============================================================
SAVE IMPORTED RECIPES?
============================================================

You have 1 imported recipe(s).
Would you like to save them permanently to recipes.json?

Save recipes? (y/n): y

✓ Successfully saved 1 recipe(s) to recipes.json
```
