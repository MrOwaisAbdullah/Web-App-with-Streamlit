from google import genai
from google.genai import types
import streamlit as st

def get_ai_suggestions(data_summary: str) -> str:
    """
    Uses the Gemini API to generate detailed data cleaning suggestions.
    The response is configured to provide up to 500 characters of output.
    """
    prompt = (
        f"Using the data summary below, provide clear, actionable, and detailed data cleaning recommendations. "
        f"Focus on steps to remove duplicates, fill missing values, and improve overall data quality. "
        f"Please provide a concise understandable response, under 300 words.\n\nData Summary:\n{data_summary}"
    )
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=500,
                top_k=2,
                top_p=0.5,
                temperature=0.5,
            )
        )
        return response.text
    except Exception as e:
        return f"Error calling Gemini API: {e}"
