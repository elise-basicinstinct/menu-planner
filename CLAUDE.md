# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Menu Planner is a Python CLI and Web application for generating weekly meal plans and shopping lists. Features include:
- Recipe selection from local database (recipes.json)
- **Recipe import from URLs** using schema.org structured data
- Recipe scaling based on household size
- Automatic shopping list aggregation
- Both CLI and Web (Flask) interfaces

## Running the Application

**CLI:**
```bash
python3 app.py
```
Prompts for URL imports (optional), household size, nights (1-7), and cooking preference (quick/long/mixed).

**Web Interface:**
```bash
pip3 install -r requirements.txt
python3 web.py
```
Access at `http://localhost:5001` (port 5001 to avoid macOS AirPlay conflicts).

## Testing the Application

**Dependencies:**
```bash
pip3 install -r requirements.txt
```
Required: Flask 3.0.0, recipe-scrapers >=15.9.0

**Manual CLI testing (skip URL import):**
```bash
echo -e "n\n2\n3\nquick" | python3 app.py
```

**Testing core logic independently:**
```python
from core import MenuPlanner

planner = MenuPlanner('recipes.json')

# Test basic plan generation
plan = planner.generate_plan(household_size=2, nights=3, preference='quick')
assert 'menu' in plan and 'shopping_list' in plan
assert len(plan['menu']) == 3

# Test recipe import functionality
assert len(planner.temp_recipes) == 0
test_recipe = {"id": 99, "name": "Test", "cooking_time": "quick",
               "servings": 4, "ingredients": [{"name": "test", "amount": 1, "unit": "g"}],
               "steps": ["Test step"]}
planner.add_temp_recipe(test_recipe)
assert len(planner.temp_recipes) == 1
assert planner.get_next_recipe_id() == 100
```

**Testing web scraper:**
```python
from services.web_scraper import validate_recipe_schema

# Valid recipe passes
recipe = {"id": 1, "name": "Test", "cooking_time": "quick", "servings": 4,
          "ingredients": [{"name": "salt", "amount": 1.0, "unit": "tsp"}],
          "steps": ["Cook it"]}
validate_recipe_schema(recipe)  # Should not raise

# Invalid recipe raises RecipeValidationError
try:
    validate_recipe_schema({"name": "Incomplete"})
except RecipeValidationError:
    pass  # Expected
```

## Code Architecture

### Module Structure

The application follows a clean **separation of concerns** architecture with three layers:

**1. Core Business Logic (core.py)**
- `MenuPlanner` class - Pure business logic, no I/O
- Manages both permanent recipes (from recipes.json) and temporary recipes (from URL imports)
- Key methods:
  - `generate_plan()` - Orchestrates plan generation
  - `add_temp_recipe()` - Add recipe for current session only
  - `save_recipe_to_file()` - Validate and save recipe permanently (with duplicate checking)
  - `get_next_recipe_id()` - Generate unique IDs for new recipes
- Returns data structures, never prints or reads files directly
- Testable without UI interaction

**2. Interface Layers**

**cli.py** - Command-Line Interface
- Handles user I/O via prompts and formatted output
- Recipe import workflow: prompt → fetch → validate → add temp → save prompt after plan
- Uses `services.web_scraper` for URL imports
- Key functions:
  - `run_cli()` - Main orchestration
  - `prompt_for_recipe_urls()` / `import_recipes_from_urls()` - URL import flow
  - `prompt_to_save_recipes()` - Post-plan save prompt

**web.py** - Flask Web Application
- RESTful API endpoints for plan generation and recipe import
- Four recipe import endpoints:
  - `POST /api/import-recipe-url` - Import single URL
  - `GET /api/temp-recipes` - View temp recipes
  - `POST /api/save-temp-recipes` - Save all permanently
  - `POST /api/clear-temp-recipes` - Discard temp recipes
- Frontend: templates/index.html + static/js/app.js + static/css/style.css

**3. Services Layer (services/)**

**web_scraper.py** - Recipe Import Service
- `fetch_recipe_from_url()` - Uses `recipe-scrapers` library (supports 500+ sites)
- `normalize_recipe()` - Converts to app schema (categorizes cooking time, parses ingredients/steps)
- `validate_recipe_schema()` - Validates required fields and types
- Custom exceptions: `RecipeScraperError`, `RecipeNotFoundError`, `RecipeValidationError`

**app.py** - Entry Point
- Simple launcher: `from cli import run_cli; run_cli()`

### Data Flow

**Standard Flow:**
1. **User Input** → Collect preferences (household size, nights, cooking preference)
2. **Plan Generation** → `MenuPlanner.generate_plan()` orchestrates:
   - Combine permanent recipes + temp recipes
   - Filter by cooking time preference
   - Random selection of N recipes (no duplicates)
   - Scale ingredients for household size
   - Aggregate shopping list
3. **Display** → Show menu and shopping list
4. **Persistence** → Save plan to `last_plan.json`

**Recipe Import Flow (CLI):**
1. **Prompt** → "Import recipes from URLs? (y/n)"
2. **URL Collection** → Enter URLs one per line (Enter to finish)
3. **Fetch & Validate** → For each URL:
   - `fetch_recipe_from_url()` - Extract using schema.org data
   - `normalize_recipe()` - Convert to app format
   - `add_temp_recipe()` - Add to session (not saved yet)
4. **Plan Generation** → Temp recipes included in selection pool
5. **Post-Plan Prompt** → "Save recipes? (y/n)"
   - Yes → `save_temp_recipes_to_file()` - Validate, check duplicates, append to recipes.json
   - No → `clear_temp_recipes()` - Discard

**Recipe Import Flow (Web):**
1. **Import Section** → User enters URL, clicks "Import Recipe"
2. **API Call** → `POST /api/import-recipe-url` → fetch, normalize, add temp recipe
3. **Display** → Show imported recipe card (removable)
4. **Plan Generation** → User submits form, temp recipes included
5. **Modal Prompt** → "Save imported recipes?" (Yes/No buttons)
   - Yes → `POST /api/save-temp-recipes`
   - No → `POST /api/clear-temp-recipes`

### Key Design Patterns

**Separation of Concerns**: Business logic (core) is independent of presentation layers:
- Multiple interfaces (CLI, Web) use the same core
- Business logic testable without UI
- Features added to core work everywhere automatically

**Temporary vs Permanent Recipes**:
- `MenuPlanner.recipes` - Loaded from recipes.json (permanent)
- `MenuPlanner.temp_recipes` - Session-only imports from URLs
- `filter_recipes()` and `select_recipes()` combine both lists
- Temp recipes only saved if user explicitly confirms

**Recipe Import & Validation**:
- `fetch_recipe_from_url()` extracts using recipe-scrapers library
- `normalize_recipe()` converts to app schema:
  - Cooking time: ≤30 min → "quick", >30 min → "long"
  - Instructions parsed into steps (handles numbered lists, newlines)
  - Ingredients parsed from strings to {name, amount, unit}
- `validate_recipe_schema()` checks required fields before saving
- `save_recipe_to_file()` performs duplicate checking (case-insensitive name match)

**Scaling Logic**: Recipes have base `servings`. Scaling = `household_size / servings`. The scaled recipe gets `scaled_servings` field set to `household_size`.

**Recipe Filtering**: `filter_recipes()` returns all if "mixed", otherwise filters by `cooking_time`. If insufficient recipes, `select_recipes()` adds from opposite category and returns warning flag.

**Shopping List Aggregation**: Assumes same-named ingredients use same unit. No unit conversion. Amounts rounded to 1 decimal.

## Data Schema

### recipes.json (Array)
```json
{
  "id": number,           // Unique sequential ID
  "name": string,
  "cooking_time": "quick" | "long",
  "servings": number,
  "ingredients": [
    {"name": string, "amount": number, "unit": string}
  ],
  "steps": [string],      // Ordered cooking instructions
  "source_url": string,   // Optional: URL imported from
  "image_url": string     // Optional: Recipe image
}
```

**Important:** When adding recipes via URL import:
- ID must be unique (use `get_next_recipe_id()`)
- `cooking_time` categorized automatically (≤30 min = "quick")
- `source_url` and `image_url` preserved from imported data
- Duplicate detection by name (case-insensitive)

### last_plan.json
Auto-generated output:
- `preferences`: {household_size, nights, cooking_time_preference}
- `menu`: Array of scaled recipes with `scaled_servings` field
- `shopping_list`: {ingredient_name: {amount, unit}}

### specials.json
Placeholder for future supermarket specials feature. Currently empty array.

## Extension Points

### Implemented Features

**✅ Recipe URL Import** (COMPLETED)
- Services layer: `services/web_scraper.py` with `fetch_recipe_from_url()`, `normalize_recipe()`, `validate_recipe_schema()`
- Core methods: `add_temp_recipe()`, `save_recipe_to_file()`, `get_next_recipe_id()`
- CLI workflow: prompt → fetch → validate → temp add → save prompt
- Web workflow: import section → API endpoints → modal save prompt
- Supports 500+ recipe websites via `recipe-scrapers` library

### Future Extensions

**Favorites System:**
1. Add `favorites.json` for persistent storage
2. Add methods to `MenuPlanner`: `mark_favorite()`, `get_favorites()`, `is_favorite()`
3. Modify `select_recipes()` to weight favorites 2x in random selection
4. Update CLI to prompt for favoriting after plan generation
5. Add star/heart UI to Web interface recipe cards

**Specials Bias:**
1. Extend `services/web_scraper.py` for fetching specials from grocery sites
2. Add `score_recipe_by_specials()` to `MenuPlanner`
3. Modify `select_recipes()` to use weighted scoring (prioritize recipes with ingredients on sale)
4. Add CLI prompt for specials URL
5. Add "Show me recipes using sale items" checkbox to Web form

**AI Recipe Generation:**
1. Create `services/ai_recipes.py` module (use OpenAI/Anthropic API)
2. Add `generate_ai_recipe(constraints)` to `MenuPlanner`
3. Add CLI command for custom recipe generation (prompt for dietary restrictions, ingredients on hand)
4. Store generated recipes as temp recipes, prompt to save
5. Add "Generate Custom Recipe" button to Web interface

### Adding Alternative Interfaces

The Web interface already exists (web.py). For other interfaces:

**Desktop GUI (Textual TUI):**
```python
from textual.app import App
from core import MenuPlanner

class MenuPlannerApp(App):
    def __init__(self):
        self.planner = MenuPlanner('recipes.json')

    def on_button_pressed(self):
        plan = self.planner.generate_plan(...)
        self.update_display(plan)
```

**REST API (FastAPI):**
```python
from fastapi import FastAPI
from core import MenuPlanner

app = FastAPI()
planner = MenuPlanner('recipes.json')

@app.post("/api/plan")
def create_plan(household_size: int, nights: int, preference: str):
    return planner.generate_plan(household_size, nights, preference)
```

All interfaces share the same core business logic.

## Important Implementation Notes

### Dependencies
- **CLI**: Python 3.6+, `recipe-scrapers>=15.9.0` (for URL imports)
- **Web**: Flask 3.0.0, `recipe-scrapers>=15.9.0`
- Install: `pip3 install -r requirements.txt`

### Code Conventions
- File paths use `Path(__file__).parent` for portability
- Random selection uses `random.sample()` to avoid duplicates
- Display functions print directly (no return values)
- Core methods return data structures (dicts/lists)
- Temp recipes stored in memory only (not persisted unless user confirms)

### Web Interface Notes
- Port 5001 by default (5000 conflicts with macOS AirPlay)
- Flask debug mode enabled for development
- Single `planner` instance shared across requests (stateless recipes, stateful temp_recipes)
- **Important**: Temp recipes are session-persistent but not multi-user safe. For production, use session storage or database.

### Recipe Import Notes
- `recipe-scrapers` library supports 500+ sites (AllRecipes, Food Network, Bon Appétit, etc.)
- Relies on schema.org Recipe structured data
- Unsupported sites will raise `RecipeNotFoundError`
- Ingredient parsing is best-effort (may not perfectly extract amounts/units)
- Cooking time categorization: ≤30 min = "quick", >30 min = "long"
- Duplicate detection is case-insensitive by name only (doesn't compare ingredients)

### Known Recipe Import Limitations
- **Coles Australia (coles.com.au)**: NOT supported. Uses Incapsula WAF that blocks automated scraping. The recipe-scrapers library does not include a Coles scraper.
- **Alternative Australian sites**: Use taste.com.au, womensweeklyfood.com.au, or bestrecipes.com.au instead - all fully supported.
- **Custom scrapers**: For unsupported sites with anti-bot protection, you may need to:
  1. Manually inspect the page HTML/JSON-LD structure using browser DevTools
  2. Create a custom scraper function in services/web_scraper.py
  3. Handle anti-bot protections (may require browser automation with Selenium/Playwright)
  4. Add site-specific error handling for WAF/Incapsula blocks
