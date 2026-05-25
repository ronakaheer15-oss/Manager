import os
import google.generativeai as genai
import json
from config import GEMINI_API_KEY

def configure_ai():
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        genai.configure(api_key=GEMINI_API_KEY)
        return True
    return False

def analyze_screenshot_for_stats(image_path, user_prompt):
    """
    KreeRank Merge: Extracts detailed esports stats using Gemini Vision.
    """
    if not configure_ai():
        raise Exception("Gemini API key is missing. Please add GEMINI_API_KEY to your .env file.")
        
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    sample_file = genai.upload_file(path=image_path)
    
    system_prompt = """
    Extract the performance stats from this match screenshot into this exact JSON:
    {
        "kills": 0,
        "assists": 0,
        "survival_time": 0,
        "clutches": 0,
        "teamplay": 0,
        "communication": 0,
        "discipline": 0,
        "mistakes": 0,
        "mvp": 0
    }
    Rules: 
    - survival_time should be in minutes.
    - teamplay/comms/discipline should be on a scale of 1-10.
    - Return ONLY valid JSON.
    """
    
    response = model.generate_content([sample_file, system_prompt, f"Context: {user_prompt}"])
    sample_file.delete()
    
    try:
        text = response.text.strip()
        if text.startswith('```json'): text = text[7:-3]
        elif text.startswith('```'): text = text[3:-3]
        return json.loads(text.strip())
    except Exception as e:
        raise Exception(f"AI Parse Error: {str(e)}")

def parse_natural_language_command(text_prompt):
    """
    KreeRank Merge: Parses plain text into structured data.
    """
    if not configure_ai():
        raise Exception("Gemini API key is missing.")
        
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Parse this request into JSON: "{text_prompt}"
    
    1. If linking IGN: {"type": "link_ign", "ign": "name"}
    2. If match report: {"type": "report", "kills": 0, "assists": 0, ... (all KreeManager fields)}
    Return ONLY valid JSON.
    """
    response = model.generate_content(prompt)
    
    try:
        text = response.text.strip()
        if text.startswith('```json'): text = text[7:-3]
        elif text.startswith('```'): text = text[3:-3]
        return json.loads(text.strip())
    except Exception as e:
        raise Exception(f"AI Parse Error: {str(e)}")
