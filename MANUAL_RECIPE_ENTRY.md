# Manual Recipe Entry for Coles (and other protected sites)

## Why Manual Entry?

Coles Australia uses enterprise-grade Incapsula WAF protection that blocks automated scrapers, including Selenium. This is intentional anti-bot protection that's very difficult to bypass without:
- Residential proxy networks ($$$)
- CAPTCHA solving services ($$$)
- Advanced browser fingerprint spoofing

## Solution: Quick Manual Entry

### Option 1: Use the Recipe JSON Format

Create a file `my_coles_recipe.json`:

```json
{
  "name": "Lamb with Grilled Cauliflower Steaks",
  "cooking_time": "long",
  "servings": 4,
  "ingredients": [
    {"name": "lamb backstrap", "amount": 600, "unit": "g"},
    {"name": "cauliflower", "amount": 1, "unit": "head"},
    {"name": "olive oil", "amount": 3, "unit": "tbsp"},
    {"name": "garlic", "amount": 2, "unit": "cloves"},
    {"name": "lemon", "amount": 1, "unit": "whole"}
  ],
  "steps": [
    "Preheat oven to 200°C",
    "Cut cauliflower into thick steaks",
    "Season lamb with salt and pepper",
    "Grill cauliflower until golden",
    "Pan-fry lamb to desired doneness",
    "Rest lamb before slicing",
    "Serve lamb over cauliflower steaks"
  ]
}
```

Then load it:
```bash
python3 -c "
import json
from core import MenuPlanner

with open('my_coles_recipe.json') as f:
    recipe = json.load(f)

planner = MenuPlanner('recipes.json')
recipe['id'] = planner.get_next_recipe_id()
planner.save_recipe_to_file(recipe)
print(f'✓ Saved: {recipe[\"name\"]}')
"
```

### Option 2: Quick Web Form (Coming Soon)

We could add a "Manual Entry" button in the web interface that opens a form where you paste:
- Recipe name
- Ingredients (one per line)
- Instructions (one per line)
- Cooking time, servings

### Option 3: Use Supported Australian Sites

These work perfectly with automated import:
- **taste.com.au** - Huge Australian recipe collection
- **womensweeklyfood.com.au** - Australian Women's Weekly recipes
- **bestrecipes.com.au** - Best Recipes Australia

## Quick Test with taste.com.au

Try this instead:
```bash
# In web interface, paste this URL:
https://www.taste.com.au/recipes/grilled-lamb-cauliflower-steaks/abc123
```

The automated scraper will work perfectly!
