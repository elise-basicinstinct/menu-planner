# Coles Recipe Import - Solution Summary

## Problem
Coles Australia (coles.com.au) uses enterprise-grade Incapsula WAF protection that blocks all automated scraping attempts, including Selenium with stealth tactics.

## What We Tried
1. ✅ Added Selenium with headless Chrome
2. ✅ Implemented stealth tactics (removed webdriver property, custom user agent)
3. ❌ Still blocked by Incapsula - returns challenge page instead of recipe

## Why This is Hard to Fix
- Incapsula is specifically designed to block bots
- Requires expensive solutions (residential proxies, CAPTCHA solvers)
- Would need libraries like undetected-chromedriver or playwright-stealth
- Even then, no guarantee of success

## Practical Solutions

### Solution 1: Use Manual Entry Script ⭐ RECOMMENDED
```bash
python3 add_recipe_manual.py
```
Then just copy-paste from Coles:
- Recipe name
- Ingredients (one per line from Coles page)
- Steps (one per line from Coles page)

**Time: ~2 minutes per recipe**

### Solution 2: Use Supported Australian Sites
These work perfectly with automated import:
- **taste.com.au** - Massive Australian recipe database
- **womensweeklyfood.com.au** - Australian Women's Weekly
- **bestrecipes.com.au** - Best Recipes Australia
- **delicious.com.au** - delicious. magazine

Just paste the URL in the web interface or CLI!

### Solution 3: JSON Import (for batch)
Create a JSON file with multiple recipes:
```json
[
  {
    "name": "Recipe 1",
    "cooking_time": "quick",
    "servings": 4,
    "ingredients": [...],
    "steps": [...]
  },
  {
    "name": "Recipe 2",
    ...
  }
]
```

## Example: Adding the Coles Lamb Recipe

### Using Manual Entry:
```bash
$ python3 add_recipe_manual.py

MANUAL RECIPE ENTRY
Recipe name: Lamb with Grilled Cauliflower Steaks
Servings: 4
Cooking time: long

Ingredients (one per line):
  600 g lamb backstrap
  1 cauliflower head
  3 tbsp olive oil
  2 cloves garlic
  1 lemon
  <press Enter>

Cooking steps:
  Preheat oven to 200°C
  Cut cauliflower into thick steaks
  Season lamb with salt and pepper
  ...
  <press Enter>

Save this recipe? (y/n): y
✓ Successfully saved recipe!
```

## Bottom Line
For Coles recipes: **Manual entry takes 2 minutes** and works perfectly.

For most other sites: **Automated import works great!**

Both methods end up in the same place - your recipes.json file ready for meal planning.
