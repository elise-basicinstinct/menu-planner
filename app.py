#!/usr/bin/env python3
"""
Menu Planner CLI

A simple tool to generate weekly meal plans and shopping lists.

Usage:
    python3 app.py

The application will prompt for:
    - Household size
    - Number of nights (1-7)
    - Cooking time preference (quick/long/mixed)

It will then generate a meal plan with recipes and an aggregated shopping list.
"""

from cli import run_cli


if __name__ == "__main__":
    run_cli()
