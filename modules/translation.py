"""
Translation Module for eFile Sathi
Handles translation between English and Hindi using AI
"""
from typing import Optional
import os
try:
    from openai import OpenAI
    PERPLEXITY_AVAILABLE = True
except ImportError:
    PERPLEXITY_AVAILABLE = False

from config import PERPLEXITY_API_KEY, PERPLEXITY_BASE_URL, PERPLEXITY_MODEL

class Translator:
    """AI-powered translator for government documents"""
    
    def __init__(self):
        self.api_key = PERPLEXITY_API_KEY
        self.client = None
        
        if PERPLEXITY_AVAILABLE and self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=PERPLEXITY_BASE_URL
            )
    
    def translate_to_hindi(self, text: str) -> str:
        """Translate text to Hindi using LLM"""
        if not self.client or not text:
            return "Translation unavailable. Please check API configuration."
            
        try:
            # Chunking not implemented for simplicity, but for large docs we might need it
            # Truncate if too long to avoid token limits
            text_to_translate = text[:4000] if len(text) > 4000 else text
            
            response = self.client.chat.completions.create(
                model=PERPLEXITY_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional government translator. Translate the following official document text into formal Hindi (Devanagari script). Maintain the tone and structure. Just provide the translation, no introductory text."
                    },
                    {"role": "user", "content": text_to_translate}
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Translation error: {e}")
            return f"Error occurred during translation: {str(e)}"

# Singleton instance
translator = Translator()
