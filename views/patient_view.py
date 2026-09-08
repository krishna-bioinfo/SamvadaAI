# views/patient_view.py
import os
import sys

# Ensure parent directory is in sys.path to find root modules (db, ai_engine, etc.)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import hashlib
import streamlit as st
from ai_engine import process_patient_input
from db import get_patient_history, save_intake_record

def render_patient_view():
    patient = st.session_state.patient_user
    h_m = patient["height_cm"] / 100.0
    bmi = round(patient["weight_kg"] / (h_m ** 2), 1) if h_m > 0 else "N/A"

    # Patient Card Header
    st.markdown(f"""
    <div class="patient-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="margin:0; color:#004D40;">Namaste, {patient['name']}! 👋</h3>
                <p style="margin:4px 0 0 0; color:#555; font-size:0.9rem;">
                    📱 <b>Phone:</b> {patient['phone_number']} | <b>Age:</b> {patient['age']} | <b>Sex:</b> {patient['sex']} | 
                    <b>Height:</b> {patient['height_cm']} cm | <b>Weight:</b> {patient['weight_kg']} kg | <b>BMI:</b> {bmi}
                </p>
            </div>
            <div>
                <span class="patient-badge">ABHA Verified</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Session States for Chat
    if "chat_history" not in st.session_state or not st.session_state.chat_history:
        st.session_state.chat_history = [
            {"role": "assistant", "content": f"Namaste {patient['name']}! What health concerns bring you in today? You can speak or type in English, Hindi, Hinglish, or Telugu."}
        ]
    if "audio_key_count" not in st.session_state:
        st.session_state.audio_key_count = 0
    if "last_audio_hash" not in st.session_state:
        st.session_state.last_audio_hash = None
    if "is_done" not in st.session_state:
        st.session_state.is_done = False

    p_tab1, p_tab2 = st.tabs(["🎙️ AI Voice Consultation & Triage", "📜 My Medical History & OPD Slips"])

    with p_tab1:
        # Display Consultation Timeline
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                with st.chat_message("user", avatar="🧑"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant", avatar="🌿"):
                    st.write(msg["content"])

        if st.session_state.is_done:
            st.success("✅ **Intake Consultation Complete!** Your clinical summary has been routed to the OPD Doctor Dashboard.")
            if st.button("🔄 Start New Symptom Intake"):
                st.session_state.chat_history = []
                st.session_state.is_done = False
                st.rerun()
        else:
            st.divider()
            
            audio_file = st.audio_input(
                "🎙️ Speak your symptoms (English, Hindi, Telugu, Hinglish)",
                key=f"audio_recorder_{st.session_state.audio_key_count}"
            )
            user_text = st.chat_input("Or type your response here...")

            audio_bytes_to_process = None
            text_to_process = None
            detected_mime_type = "audio/wav"

            if audio_file is not None:
                audio_bytes = audio_file.read()
                detected_mime_type = getattr(audio_file, "type", "audio/wav") or "audio/wav"
                current_hash = hashlib.md5(audio_bytes).hexdigest()
                
                if st.session_state.last_audio_hash != current_hash:
                    st.session_state.last_audio_hash = current_hash
                    audio_bytes_to_process = audio_bytes

            if user_text:
                text_to_process = user_text

            if audio_bytes_to_process or text_to_process:
                with st.spinner("Processing symptoms & evaluating intake..."):
                    ai_res = process_patient_input(
                        chat_history=st.session_state.chat_history,
                        user_text=text_to_process,
                        audio_bytes=audio_bytes_to_process,
                        mime_type=detected_mime_type,
                        patient_info=patient
                    )

                    transcription = ai_res.get("patient_transcription", "Voice Message")
                    assistant_msg = ai_res.get("assistant_message", "Could you elaborate further on your symptoms?")

                    st.session_state.chat_history.append({
                        "role": "user", 
                        "content": f"🎙️ {transcription}" if audio_bytes_to_process else transcription
                    })
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": assistant_msg
                    })

                    if audio_bytes_to_process:
                        st.session_state.audio_key_count += 1

                    if ai_res.get("is_done"):
                        st.session_state.is_done = True
                        summary = ai_res.get("summary", {})
                        save_intake_record(
                            patient_id=patient["id"],
                            summary_dict=summary,
                            chat_history=st.session_state.chat_history
                        )

                st.rerun()

    # Medical History Tab
    with p_tab2:
        st.subheader("📜 Past Consultations & Doctor Notes")
        history = get_patient_history(patient["id"])
        
        if not history:
            st.info("No prior medical records found for this account.")
        else:
            for visit in history:
                with st.expander(f"🗓️ Visit #{visit['id']} — Date: {visit['timestamp']} [{visit['status']}]"):
                    st.markdown(f"**Chief Complaint:** {visit['chief_complaint']}")
                    st.markdown(f"**AYUSH Recommendation:** {visit['suggested_ayush_focus']}")
                    st.markdown(f"**Doctor Notes / Prescription:** {visit['doctor_notes'] or 'Pending doctor review.'}")