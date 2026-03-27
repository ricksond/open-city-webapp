import pandas as pd
import os
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    """Initializes and returns the ChatGoogleGenerativeAI model."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "❌ GOOGLE_API_KEY not found. Please set it in your `.env` file."
        )
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        google_api_key=api_key,
        response_mime_type="application/json"
    )
