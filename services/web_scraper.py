"""
Recipe Web Scraper Service

Handles fetching, parsing, and validating recipes from URLs.
Uses schema.org Recipe structured data for reliable extraction.
For protected sites like Coles, uses Selenium with headless browser.
"""

from typing import Dict, Any, Optional, List
from recipe_scrapers import scrape_me
import json
import re
from urllib.parse import urlparse


class RecipeScraperError(Exception):
    """Base exception for recipe scraping errors."""
    pass


class RecipeValidationError(RecipeScraperError):
    """Raised when a recipe fails validation."""
    pass


class RecipeNotFoundError(RecipeScraperError):
    """Raised when no recipe data is found at the URL."""
    pass


def is_coles_url(url: str) -> bool:
    """Check if URL is from Coles Australia recipe site."""
    parsed = urlparse(url)
    return 'coles.com.au' in parsed.netloc and ('recipe' in url.lower() or 'inspiration' in url.lower())


def fetch_coles_recipe(url: str) -> Dict[str, Any]:
    """
    Fetch recipe from Coles Australia using Selenium to bypass WAF.

    Args:
        url: Coles recipe URL

    Returns:
        Raw recipe dictionary

    Raises:
        RecipeNotFoundError: If recipe data cannot be extracted
        RecipeScraperError: For browser or parsing errors
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager

        # Setup headless Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Initialize driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            # Load page
            driver.get(url)

            # Wait for page to load (wait for recipe content)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Try to extract JSON-LD data first
            recipe_data = None
            try:
                scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
                for script in scripts:
                    try:
                        data = json.loads(script.get_attribute('innerHTML'))
                        # Handle both single recipe and list of items
                        if isinstance(data, list):
                            for item in data:
                                if item.get('@type') == 'Recipe':
                                    recipe_data = item
                                    break
                        elif isinstance(data, dict) and data.get('@type') == 'Recipe':
                            recipe_data = data

                        if recipe_data:
                            break
                    except json.JSONDecodeError:
                        continue
            except Exception:
                pass

            # If JSON-LD found, extract data
            if recipe_data:
                return {
                    "name": recipe_data.get('name', ''),
                    "ingredients": recipe_data.get('recipeIngredient', []),
                    "instructions": '\n'.join([
                        step.get('text', '') if isinstance(step, dict) else str(step)
                        for step in recipe_data.get('recipeInstructions', [])
                    ]),
                    "total_time": _parse_iso_duration(recipe_data.get('totalTime', '')),
                    "yields": recipe_data.get('recipeYield', '4'),
                    "image": recipe_data.get('image', {}).get('url', '') if isinstance(recipe_data.get('image'), dict) else recipe_data.get('image', ''),
                    "host": "coles.com.au",
                    "url": url
                }

            # Fallback: Try HTML parsing
            try:
                # Get title
                title = driver.find_element(By.CSS_SELECTOR, 'h1').text

                # Get ingredients
                ingredient_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="ingredient"], .ingredient, [class*="ingredient"]')
                ingredients = [elem.text for elem in ingredient_elements if elem.text.strip()]

                # Get instructions
                instruction_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="instruction"], .instruction, [class*="method"] li, [class*="instruction"]')
                instructions = '\n'.join([elem.text for elem in instruction_elements if elem.text.strip()])

                if title and (ingredients or instructions):
                    return {
                        "name": title,
                        "ingredients": ingredients,
                        "instructions": instructions,
                        "total_time": 0,
                        "yields": "4",
                        "image": "",
                        "host": "coles.com.au",
                        "url": url
                    }
            except Exception:
                pass

            raise RecipeNotFoundError(f"Could not extract recipe data from Coles page: {url}")

        finally:
            driver.quit()

    except ImportError as e:
        raise RecipeScraperError(
            f"Selenium not installed. Run: pip install -r requirements.txt\n"
            f"Error: {str(e)}"
        )
    except Exception as e:
        raise RecipeScraperError(f"Failed to fetch Coles recipe: {str(e)}")


def _parse_iso_duration(duration_str: str) -> int:
    """Parse ISO 8601 duration (PT30M) to minutes."""
    if not duration_str:
        return 0

    match = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?', duration_str)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        return hours * 60 + minutes
    return 0


def fetch_recipe_from_url(url: str) -> Dict[str, Any]:
    """
    Fetch and parse a recipe from a URL using schema.org Recipe data.
    Routes Coles URLs to custom Selenium-based scraper to bypass WAF.

    Args:
        url: URL of the recipe page

    Returns:
        Raw recipe dictionary with fields from schema.org

    Raises:
        RecipeNotFoundError: If no recipe data found at URL
        RecipeScraperError: For network errors or parsing failures
    """
    # Check if this is a Coles URL and use custom scraper
    if is_coles_url(url):
        return fetch_coles_recipe(url)

    # Use standard recipe-scrapers library for other sites
    try:
        scraper = scrape_me(url)

        # Extract all available recipe data
        recipe_data = {
            "name": scraper.title(),
            "ingredients": scraper.ingredients(),
            "instructions": scraper.instructions(),
            "total_time": scraper.total_time(),
            "yields": scraper.yields(),
            "image": scraper.image(),
            "host": scraper.host(),
            "url": url
        }

        return recipe_data

    except Exception as e:
        error_msg = str(e).lower()
        if "no recipe found" in error_msg or "not implemented" in error_msg or "not supported" in error_msg:
            raise RecipeNotFoundError(
                f"No recipe data found at {url}. The page may not contain "
                "schema.org Recipe structured data or is from an unsupported site."
            )
        raise RecipeScraperError(f"Failed to fetch recipe from {url}: {str(e)}")


def validate_recipe_schema(recipe: Dict[str, Any]) -> None:
    """
    Validate that a recipe has all required fields with correct types.

    Args:
        recipe: Recipe dictionary to validate

    Raises:
        RecipeValidationError: If recipe is missing required fields or has invalid data
    """
    required_fields = {
        "name": str,
        "cooking_time": str,
        "servings": (int, float),
        "ingredients": list,
        "steps": list
    }

    # Check required fields exist
    for field, expected_type in required_fields.items():
        if field not in recipe:
            raise RecipeValidationError(f"Recipe is missing required field: {field}")

        if not isinstance(recipe[field], expected_type):
            raise RecipeValidationError(
                f"Recipe field '{field}' must be of type {expected_type.__name__}, "
                f"got {type(recipe[field]).__name__}"
            )

    # Validate ingredients structure
    if not recipe["ingredients"]:
        raise RecipeValidationError("Recipe must have at least one ingredient")

    for i, ingredient in enumerate(recipe["ingredients"]):
        if not isinstance(ingredient, dict):
            raise RecipeValidationError(
                f"Ingredient {i+1} must be a dictionary, got {type(ingredient).__name__}"
            )

        required_ing_fields = {"name": str, "amount": (int, float), "unit": str}
        for field, expected_type in required_ing_fields.items():
            if field not in ingredient:
                raise RecipeValidationError(
                    f"Ingredient {i+1} is missing required field: {field}"
                )
            if not isinstance(ingredient[field], expected_type):
                raise RecipeValidationError(
                    f"Ingredient {i+1} field '{field}' must be of type "
                    f"{expected_type.__name__}"
                )

    # Validate steps
    if not recipe["steps"]:
        raise RecipeValidationError("Recipe must have at least one cooking step")

    for i, step in enumerate(recipe["steps"]):
        if not isinstance(step, str) or not step.strip():
            raise RecipeValidationError(
                f"Cooking step {i+1} must be a non-empty string"
            )

    # Validate cooking_time
    valid_cooking_times = ["quick", "long"]
    if recipe["cooking_time"] not in valid_cooking_times:
        raise RecipeValidationError(
            f"cooking_time must be one of {valid_cooking_times}, "
            f"got '{recipe['cooking_time']}'"
        )

    # Validate servings is positive
    if recipe["servings"] <= 0:
        raise RecipeValidationError("servings must be a positive number")


# Imperial to metric conversions
IMPERIAL_TO_METRIC = {
    # Volume
    "cup": ("ml", 240),
    "cups": ("ml", 240),
    "tablespoon": ("ml", 15),
    "tablespoons": ("ml", 15),
    "tbsp": ("ml", 15),
    "teaspoon": ("ml", 5),
    "teaspoons": ("ml", 5),
    "tsp": ("ml", 5),
    "fluid ounce": ("ml", 30),
    "fluid ounces": ("ml", 30),
    "fl oz": ("ml", 30),
    "ounce": ("ml", 30),
    "ounces": ("ml", 30),
    "oz": ("ml", 30),
    "pint": ("ml", 473),
    "pints": ("ml", 473),
    "quart": ("ml", 946),
    "quarts": ("ml", 946),
    "gallon": ("ml", 3785),
    "gallons": ("ml", 3785),

    # Weight
    "pound": ("g", 454),
    "pounds": ("g", 454),
    "lb": ("g", 454),
    "lbs": ("g", 454),
}


def convert_to_metric(amount: float, unit: str) -> tuple:
    """
    Convert imperial units to metric.

    Args:
        amount: Amount in imperial units
        unit: Unit name

    Returns:
        Tuple of (new_amount, new_unit)
    """
    unit_lower = unit.lower().strip()

    if unit_lower in IMPERIAL_TO_METRIC:
        new_unit, conversion_factor = IMPERIAL_TO_METRIC[unit_lower]
        new_amount = round(amount * conversion_factor, 1)
        return new_amount, new_unit

    # Already metric or unit like "pcs", "cloves", etc.
    return amount, unit


def normalize_recipe(raw_recipe: Dict[str, Any], recipe_id: int) -> Dict[str, Any]:
    """
    Convert a raw scraped recipe into the application's standard format.
    Automatically scales to 2 servings and converts imperial units to metric.

    Args:
        raw_recipe: Raw recipe data from scraper
        recipe_id: Unique ID to assign to this recipe

    Returns:
        Normalized recipe dictionary matching application schema
    """
    # Parse instructions into steps
    instructions_text = raw_recipe.get("instructions", "")
    steps = parse_instructions_to_steps(instructions_text)

    # Parse ingredients into structured format
    ingredients_list = raw_recipe.get("ingredients", [])
    ingredients = parse_ingredients(ingredients_list)

    # Determine cooking time category based on total_time
    total_time = raw_recipe.get("total_time", 0)
    cooking_time = "quick" if total_time <= 30 else "long"

    # Parse servings from yields string
    original_servings = parse_servings(raw_recipe.get("yields", "4"))

    # Scale to 2 servings and convert to metric
    scale_factor = 2 / original_servings
    scaled_ingredients = []
    for ingredient in ingredients:
        scaled_ing = ingredient.copy()

        # Scale amount
        scaled_amount = ingredient["amount"] * scale_factor

        # Convert to metric if needed
        metric_amount, metric_unit = convert_to_metric(scaled_amount, ingredient["unit"])

        scaled_ing["amount"] = round(metric_amount, 1)
        scaled_ing["unit"] = metric_unit

        scaled_ingredients.append(scaled_ing)

    # Build normalized recipe
    normalized = {
        "id": recipe_id,
        "name": raw_recipe.get("name", "Imported Recipe"),
        "cooking_time": cooking_time,
        "servings": 2,  # Always normalize to 2 servings
        "ingredients": scaled_ingredients,
        "steps": steps
    }

    # Add optional metadata
    if "url" in raw_recipe:
        normalized["source_url"] = raw_recipe["url"]
    if "image" in raw_recipe:
        normalized["image_url"] = raw_recipe["image"]

    return normalized


def parse_instructions_to_steps(instructions: str) -> List[str]:
    """
    Parse instruction text into a list of individual steps.

    Args:
        instructions: Raw instruction text (may contain newlines, numbers, etc.)

    Returns:
        List of individual cooking steps
    """
    if not instructions:
        return ["No cooking instructions provided"]

    # Split by common delimiters
    steps = []

    # Try splitting by numbered steps first (1. 2. or 1) 2) patterns)
    import re
    numbered_pattern = r'\d+[\.\)]\s*'
    parts = re.split(numbered_pattern, instructions)

    # Filter out empty parts
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) > 1:
        steps = parts
    else:
        # Try splitting by newlines
        lines = instructions.split('\n')
        steps = [line.strip() for line in lines if line.strip()]

    # If still only one step, try splitting by sentences
    if len(steps) == 1 and len(steps[0]) > 200:
        sentences = re.split(r'(?<=[.!?])\s+', steps[0])
        if len(sentences) > 1:
            steps = sentences

    return steps


def parse_ingredients(ingredients_list: List[str]) -> List[Dict[str, Any]]:
    """
    Parse ingredient strings into structured format.

    Args:
        ingredients_list: List of ingredient strings (e.g., "2 cups flour")

    Returns:
        List of ingredient dictionaries with name, amount, and unit
    """
    import re

    parsed_ingredients = []

    for ing_str in ingredients_list:
        # Try to extract amount and unit using regex
        # Pattern: optional number (int or fraction), optional unit, ingredient name
        pattern = r'^([\d\/\.\s]+)?\s*([a-zA-Z]+)?\s+(.+)$'
        match = re.match(pattern, ing_str.strip())

        if match:
            amount_str, unit, name = match.groups()

            # Parse amount
            amount = parse_amount(amount_str) if amount_str else 1.0

            # Use unit if found, otherwise use "pcs"
            unit = unit if unit else "pcs"

            parsed_ingredients.append({
                "name": name.strip(),
                "amount": amount,
                "unit": unit
            })
        else:
            # Fallback: treat entire string as name with default values
            parsed_ingredients.append({
                "name": ing_str.strip(),
                "amount": 1.0,
                "unit": "pcs"
            })

    return parsed_ingredients


def parse_amount(amount_str: str) -> float:
    """
    Parse amount string to float, handling fractions.

    Args:
        amount_str: Amount string (e.g., "2", "1.5", "1/2", "2 1/2")

    Returns:
        Parsed amount as float
    """
    amount_str = amount_str.strip()

    # Handle fractions
    if '/' in amount_str:
        # Handle mixed fractions like "2 1/2"
        parts = amount_str.split()
        if len(parts) == 2:
            whole = float(parts[0])
            frac_parts = parts[1].split('/')
            fraction = float(frac_parts[0]) / float(frac_parts[1])
            return whole + fraction
        else:
            # Simple fraction like "1/2"
            frac_parts = amount_str.split('/')
            return float(frac_parts[0]) / float(frac_parts[1])

    # Handle decimal or integer
    try:
        return float(amount_str)
    except ValueError:
        return 1.0


def parse_servings(yields_str: str) -> int:
    """
    Parse servings from yields string.

    Args:
        yields_str: Yields string (e.g., "4 servings", "Serves 6", "8")

    Returns:
        Number of servings as integer
    """
    import re

    # Extract first number from string
    match = re.search(r'\d+', str(yields_str))
    if match:
        return int(match.group())

    # Default to 4 servings if can't parse
    return 4
