"""
AI Assistant Service for Recipe Recommendations

Uses Google Gemini API (free tier) to help users find BBC Good Food recipes
through natural conversation.
"""

import os
import re
from typing import List, Dict, Any, Tuple
import google.generativeai as genai


# System prompt to guide the AI
SYSTEM_PROMPT = """You are a helpful meal planning assistant that specializes in recommending recipes from BBC Good Food (bbcgoodfood.com).

Your role is to:
1. Have a natural conversation with users about their meal preferences
2. Ask clarifying questions about:
   - Cooking time preferences (quick meals under 30 min, or longer recipes)
   - Main ingredients they want (chicken, beef, vegetarian, etc.)
   - Cuisine types (Italian, Asian, Mexican, etc.)
   - Dietary restrictions or preferences
   - Number of people to feed
3. Recommend specific BBC Good Food recipes with their FULL URLs

CRITICAL RULES:
- ONLY recommend recipes that you are highly confident currently exist on BBC Good Food
- NEVER recommend archived, deleted, or older recipes that may no longer be available
- Focus on well-known, popular, evergreen recipes that are likely to still be active
- When in doubt about whether a recipe still exists, choose a different recipe instead
- ALWAYS include the complete BBC Good Food URL when suggesting recipes
- Format recipe suggestions like this: "I recommend [Recipe Name] - https://www.bbcgoodfood.com/recipes/[recipe-slug]"
- Only recommend recipes from bbcgoodfood.com
- Be concise and friendly
- Ask follow-up questions if the user's preferences are unclear
- Suggest 2-3 recipes at a time maximum
- Prioritize recipes with simple, common names (e.g., "chicken-curry", "spaghetti-carbonara") over very specific or seasonal ones

Example conversation:
User: "I want something quick with chicken"
You: "Great! Do you prefer Asian-style stir-fries, Mediterranean dishes, or something else? And are you cooking for 2 or more people?"

User: "Asian stir-fry for 2"
You: "Perfect! Here are some popular quick chicken stir-fry recipes:

1. **Chicken stir-fry** - A classic, ready in 20 mins
   https://www.bbcgoodfood.com/recipes/chicken-stir-fry

2. **Sweet & sour chicken** - Ready in 30 mins
   https://www.bbcgoodfood.com/recipes/sweet-sour-chicken

Would you like to add any of these to your meal plan?"

Remember: Only recommend recipes you're confident are current and active on BBC Good Food. Avoid niche, seasonal, or very specific recipe names that may have been archived."""


class AIAssistant:
    """AI-powered recipe recommendation assistant using Google Gemini."""

    def __init__(self, api_key: str = None):
        """
        Initialize the AI assistant.

        Args:
            api_key: Google AI API key. If not provided, reads from GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. "
                "Get your free API key from https://aistudio.google.com/app/apikey"
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        # Use models/gemini-2.5-flash - the free tier model
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')

    def chat(self, user_message: str, conversation_history: List[Dict[str, str]] = None) -> Tuple[str, List[str]]:
        """
        Send a message to the AI and get a response with recipe URLs.

        Args:
            user_message: The user's message
            conversation_history: List of previous messages [{"role": "user"/"assistant", "content": "..."}]

        Returns:
            Tuple of (AI response text, List of extracted BBC Good Food URLs)
        """
        conversation_history = conversation_history or []

        # Build conversation for Gemini
        messages = [{"role": "user", "parts": [SYSTEM_PROMPT]}]

        # Add conversation history
        for msg in conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            messages.append({"role": role, "parts": [msg["content"]]})

        # Add current user message
        messages.append({"role": "user", "parts": [user_message]})

        # Start chat
        chat = self.model.start_chat(history=messages[:-1])

        # Get response
        response = chat.send_message(user_message)
        ai_response = response.text

        # Extract BBC Good Food URLs
        recipe_urls = self.extract_bbc_recipe_urls(ai_response)

        return ai_response, recipe_urls

    @staticmethod
    def extract_bbc_recipe_urls(text: str) -> List[str]:
        """
        Extract BBC Good Food recipe URLs from text.

        Args:
            text: Text containing potential URLs

        Returns:
            List of unique BBC Good Food recipe URLs
        """
        # Pattern to match BBC Good Food recipe URLs
        pattern = r'https?://(?:www\.)?bbcgoodfood\.com/recipes/[a-z0-9-]+'

        urls = re.findall(pattern, text, re.IGNORECASE)

        # Return unique URLs, preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            # Normalize URL (lowercase, remove www)
            normalized = url.lower().replace('www.', '')
            if normalized not in seen:
                seen.add(normalized)
                unique_urls.append(url)

        return unique_urls


# Error classes
class AIAssistantError(Exception):
    """Base exception for AI assistant errors."""
    pass


class APIKeyMissingError(AIAssistantError):
    """Raised when the API key is missing."""
    pass


class APICallError(AIAssistantError):
    """Raised when the API call fails."""
    pass
