"""
AI Engine with Single-Pass Multimodal Audio Processing & API Key Rotation.
Demographic-Aware Clinical Analysis (Age, Sex, Height, Weight).
"""

import json
import time
import streamlit as st
from google import genai
from google.genai import types
from config import PRIMARY_MODEL, FALLBACK_MODELS, INTAKE_SYSTEM_PROMPT, RED_FLAGS


def get_gemini_clients():
    """Retrieves all available Gemini API clients from secrets for failover."""
    raw_keys = [
        st.secrets.get("GEMINI_API_KEY"),
        st.secrets.get("GEMINI_BACKUP_KEY"),
        st.secrets.get("GEMINI_KEY_2")
    ]
    unique_keys = []
    for k in raw_keys:
        if k and k not in unique_keys:
            unique_keys.append(k)

    return [genai.Client(api_key=k) for k in unique_keys]

def check_red_flags(text_content: str) -> str | None:
    """Scans text for immediate emergency keywords."""
    if not text_content:
        return None
    text = text_content.lower()
    for flag in RED_FLAGS:
        if flag in text:
            return f"🚨 EMERGENCY WARNING: '{flag.title()}' detected. Please seek emergency medical care immediately."
    return None


def parse_ai_json(response_text: str) -> dict:
    """Safely extracts JSON from model response string."""
    clean_text = response_text.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(clean_text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return {
        "patient_transcription": "Voice input received",
        "assistant_message": clean_text if clean_text else "Could you elaborate further on your symptoms?",
        "is_done": False,
        "summary": {}
    }


def process_patient_input(chat_history: list, user_text: str = None, audio_bytes: bytes = None, mime_type: str = "audio/wav", patient_info: dict = None) -> dict:
    """
    Single-pass multimodal handler with demographic context.
    Processes audio or text input in ONE API call.
    """
    # 1. Check Red Flags for Text Input
    if user_text:
        red_flag_alert = check_red_flags(user_text)
        if red_flag_alert:
            return {
                "patient_transcription": user_text,
                "assistant_message": red_flag_alert,
                "is_done": True,
                "summary": {"red_flags": [red_flag_alert]}
            }

    clients = get_gemini_clients()
    if not clients:
        return {
            "patient_transcription": user_text or "Voice Input",
            "assistant_message": "Error: API Key missing. Please configure GEMINI_KEY in .streamlit/secrets.toml.",
            "is_done": False,
            "summary": {}
        }

    # Format full conversation history
    formatted_history = ""
    for msg in chat_history:
        role = "Patient" if msg["role"] == "user" else "Assistant"
        formatted_history += f"{role}: {msg['content']}\n"

    # Format Patient Profile context string
    patient_context = ""
    if patient_info:
        age = patient_info.get("age", "N/A")
        sex = patient_info.get("sex", "N/A")
        h = patient_info.get("height_cm", 0)
        w = patient_info.get("weight_kg", 0)
        bmi = round(w / ((h / 100) ** 2), 1) if h and w else "N/A"
        patient_context = f"PATIENT DEMOGRAPHICS: Age: {age}, Sex: {sex}, Height: {h}cm, Weight: {w}kg (BMI: {bmi})\nConsider age/sex/body constitution during clinical evaluation."

    multimodal_prompt = f"""
{INTAKE_SYSTEM_PROMPT}

{patient_context}

Recent Conversation History:
{formatted_history}

INSTRUCTIONS FOR THIS TURN:
1. Listen carefully to the attached audio clip (if present). The patient may speak in English, Hindi, Telugu, or Hinglish/Teluglish.
2. Provide a verbatim or clean transcription of what the patient said in 'patient_transcription'. If spoken in Hindi or Telugu, translate it into clear English in 'patient_transcription'.
3. Respond as an empathetic AYUSH clinical assistant with a relevant follow-up question in 'assistant_message'.
4. Return ONLY JSON structured as:
{{
  "patient_transcription": "Exact transcription or English translation of spoken audio",
  "assistant_message": "Your relevant clinical follow-up question",
  "is_done": false,
  "summary": {{}}
}}
"""

    # Assemble request payload
    contents = [multimodal_prompt]
    if audio_bytes:
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        contents.append(audio_part)
    elif user_text:
        contents.append(f"Patient Text Input: {user_text}")

    # 2. Key-Rotation & Model Fallback Loop
    models_to_try = [PRIMARY_MODEL] + FALLBACK_MODELS
    last_error_msg = ""

    for client in clients:
        for model in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                resp_text = getattr(response, "text", None)
                if resp_text:
                    parsed = parse_ai_json(resp_text)
                    
                    # Late-check red flags on transcribed voice text
                    transcribed = parsed.get("patient_transcription", "")
                    rf = check_red_flags(transcribed)
                    if rf:
                        parsed["assistant_message"] = rf
                        parsed["is_done"] = True
                        parsed["summary"] = {"red_flags": [rf]}

                    if len(chat_history) >= 10:
                        parsed["is_done"] = True
                        
                    return parsed
            except Exception as e:
                last_error_msg = str(e)
                print(f"API Error with model {model}: {e}")
                time.sleep(0.5)
                continue

    # 3. Fallback if all keys/models fail (Displays exact error)
    return {
        "patient_transcription": f"[API Call Failed: {last_error_msg}]" if last_error_msg else "[Audio received, but transcription service was unavailable]",
        "assistant_message": f"Unable to process audio. Error details: `{last_error_msg}`. Please verify your API key in Google AI Studio.",
        "is_done": False,
        "summary": {}
    }