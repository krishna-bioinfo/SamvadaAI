# test_ai.py
import streamlit as st
from ai_engine import process_patient_input

st.title("AI Engine Test")

user_msg = st.text_input("Enter a test symptom:", "I have a sharp headache since yesterday")

if st.button("Test Gemini Call"):
    with st.spinner("Processing..."):
        result = process_patient_input([], user_msg)
        st.write("### AI Engine Output:")
        st.json(result)