import json
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

from backend.config import get_settings
from backend.utils.logger import app_logger

settings = get_settings()


class LLMService:
    def __init__(self):
        self.model_id = settings.bedrock_llm_model_id
        self.use_fallback = False

        is_placeholder = (
            settings.aws_access_key_id == "your_access_key_here"
            or not settings.aws_access_key_id
            or not settings.aws_secret_access_key
        )

        if is_placeholder:
            app_logger.warning("AWS Bedrock credentials not configured for LLM. Using mock Claude response generator.")
            self.use_fallback = True
            self.bedrock_client = None
        else:
            try:
                self.bedrock_client = boto3.client(
                    "bedrock-runtime",
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.bedrock_region,
                )
                app_logger.info("AWS Bedrock Runtime client initialized for LLM (Claude).")
            except Exception as e:
                app_logger.error(f"Failed to initialize Bedrock client: {e}. Using mock Claude response generator.")
                self.use_fallback = True
                self.bedrock_client = None

    def _generate_mock_reasoning(self, dish_name: str, restaurant_name: str, query: str) -> str:
        """Helper to generate premium mock reasoning for local dev testing."""
        return (
            f"The '{dish_name}' from '{restaurant_name}' matches your preference for '{query}'. "
            f"It features exceptional taste, premium ingredients, and has received outstanding ratings from local foodies."
        )

    def _generate_mock_chat_response(self, user_message: str, context_dishes: List[Dict[str, Any]]) -> str:
        """Helper to generate helpful mock conversational replies."""
        dishes_text = ""
        for i, d in enumerate(context_dishes[:3]):
            dishes_text += f"\n{i+1}. **{d['name']}** at *{d['restaurant_name']}* (${d['price']}, Rating: {d['rating']}⭐) - {d['description']}"
            
        if not dishes_text:
            dishes_text = "\nI couldn't find any specific dishes matching that description in our local database."

        return (
            f"Hi there! Based on your query '{user_message}', here are my top recommendations for you:\n{dishes_text}\n\n"
            f"Let me know if you would like to filter by specific cuisines, diet types (e.g., Veg-only), or check out other pricing options!"
        )

    def get_recommendation_reasoning(
        self, query: str, dish_meta: Dict[str, Any]
    ) -> str:
        """
        Explain why a specific dish/restaurant is a good match for the user query.
        """
        if self.use_fallback:
            return self._generate_mock_reasoning(
                dish_meta.get("name", "Special Dish"),
                dish_meta.get("restaurant_name", "Local Bistro"),
                query
            )

        system_prompt = (
            "You are an expert culinary critic and assistant for a Zomato/Swiggy style application. "
            "Explain in 2-3 sentences why the recommended dish matches the user's preferences. Be specific, enthusiastic, and helpful."
        )

        user_content = (
            f"User Preference Query: '{query}'\n"
            f"Recommended Item details:\n"
            f"- Name: {dish_meta.get('name')}\n"
            f"- Description: {dish_meta.get('description')}\n"
            f"- Restaurant: {dish_meta.get('restaurant_name')}\n"
            f"- Cuisine: {dish_meta.get('cuisine')}\n"
            f"- Price: ${dish_meta.get('price')}\n"
            f"- Rating: {dish_meta.get('rating')} Stars"
        )

        try:
            messages = [
                {
                    "role": "user",
                    "content": [{"text": user_content}]
                }
            ]
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": 150,
                    "temperature": 0.7,
                }
            )
            reply = response["output"]["message"]["content"][0]["text"]
            return reply.strip()
        except Exception as e:
            app_logger.error(f"Failed to generate reasoning with Claude: {e}")
            return self._generate_mock_reasoning(
                dish_meta.get("name", "Special Dish"),
                dish_meta.get("restaurant_name", "Local Bistro"),
                query
            )

    def chat_recommendation(
        self, user_message: str, history: List[Dict[str, str]], retrieved_dishes: List[Dict[str, Any]]
    ) -> str:
        """
        Conversational assistant that takes context of retrieved dishes and generates a helpful reply.
        """
        if self.use_fallback:
            return self._generate_mock_chat_response(user_message, retrieved_dishes)

        system_prompt = (
            "You are a friendly, conversational restaurant recommendation assistant (similar to Zomato & ChatGPT combined). "
            "You have access to a list of retrieved dishes matching the user's query. Discuss the recommended items and "
            "help the user decide. Be conversational, concise, and structured. Include price, rating, and restaurant name."
        )

        # Build context of retrieved dishes
        context_items = []
        for d in retrieved_dishes:
            context_items.append({
                "name": d.get("name"),
                "restaurant": d.get("restaurant_name"),
                "cuisine": d.get("cuisine"),
                "price": d.get("price"),
                "rating": d.get("rating"),
                "description": d.get("description"),
            })

        user_content = (
            f"Retrieved Context Dishes:\n{json.dumps(context_items, indent=2)}\n\n"
            f"User Message: {user_message}"
        )

        # Map history to Bedrock message structure
        messages = []
        for msg in history:
            role = msg["role"]
            content = msg["content"]
            # Map role to Bedrock syntax (must be user/assistant)
            messages.append({
                "role": "user" if role == "user" else "assistant",
                "content": [{"text": content}]
            })

        # Append current user message
        messages.append({
            "role": "user",
            "content": [{"text": user_content}]
        })

        try:
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": 500,
                    "temperature": 0.7,
                }
            )
            reply = response["output"]["message"]["content"][0]["text"]
            return reply.strip()
        except Exception as e:
            app_logger.error(f"Failed to converse with Claude: {e}")
            return self._generate_mock_chat_response(user_message, retrieved_dishes)


# Singleton instance
llm_service = LLMService()
