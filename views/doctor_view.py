import sys
import os
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from db import get_all_intakes_for_doctor, update_doctor_notes, get_patient_history

def render_doctor_view():
    doctor = st.session_state.doctor_user

    # KPI Metrics
    records = get_all_intakes_for_doctor()

    if not records:
        st.info("📋 OPD Patient Queue is currently empty. Complete an intake on a Patient Account first.")
        return

    red_flag_count = sum(1 for r in records if r["red_flags"])
    pending_count = sum(1 for r in records if r["status"] == "Pending Review")

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown(f"""
        <div class="metric-box">
            <small style="color:#666;">Total OPD Queue</small>
            <h2 style="margin:0; color:#004D40;">{len(records)}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col_m2:
        st.markdown(f"""
        <div class="metric-box" style="border-left-color: #FFA000;">
            <small style="color:#666;">Pending Review</small>
            <h2 style="margin:0; color:#FFA000;">{pending_count}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col_m3:
        st.markdown(f"""
        <div class="metric-box" style="border-left-color: {'#D32F2F' if red_flag_count > 0 else '#2E7D32'};">
            <small style="color:#666;">Emergency Triage Alerts</small>
            <h2 style="margin:0; color:{'#D32F2F' if red_flag_count > 0 else '#2E7D32'};">{red_flag_count}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.subheader("📥 Active Patient Triage Queue")

    queue_options = {}
    for r in records:
        has_rf = "🚨 EMERGENCY" if r["red_flags"] else "🟢 ROUTINE"
        label = f"{has_rf} | Record #{r['record_id']} — {r['patient_name']} ({r['age']}y/{r['sex'][0]}) — {r['chief_complaint'][:40]}..."
        queue_options[label] = r

    selected_label = st.selectbox("Select Patient Record to Review:", list(queue_options.keys()))
    record = queue_options[selected_label]

    h_m = record["height_cm"] / 100.0
    bmi = round(record["weight_kg"] / (h_m ** 2), 1) if h_m > 0 else "N/A"

    st.divider()

    # Clinical Workbench Tabs
    st.markdown(f"## 👤 Patient File: **{record['patient_name']}**")
    st.write(f"📱 **Phone:** {record['phone_number']} | **Age:** {record['age']} | **Sex:** {record['sex']} | **Height:** {record['height_cm']} cm | **Weight:** {record['weight_kg']} kg | **BMI:** {bmi}")

    tab1, tab2, tab3 = st.tabs([
        "📋 Active Triage & AI Summary", 
        "📜 Longitudinal History & Past Visits", 
        "✍️ Consultation & Prescription Builder"
    ])

    # Tab 1: Active Triage
    with tab1:
        if record["red_flags"]:
            st.markdown("""
            <div class="alert-card-red">
                <h4 style="margin:0 0 8px 0;">🚨 CRITICAL SAFETY ALERTS / RED FLAGS DETECTED</h4>
            """, unsafe_allow_html=True)
            for flag in record["red_flags"]:
                st.write(f"- {flag}")
            st.markdown("</div>", unsafe_allow_html=True)

        st.subheader("📌 Chief Complaint")
        st.info(record["chief_complaint"] or "Not specified")

        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("📋 SOCRATES Framework Analysis")
            
            # --- FIX 1: CSS Injection to ensure disabled text area text is dark slate & visible ---
            st.markdown("""
            <style>
            textarea[aria-label="Detailed Notes:"] {
                color: #1E293B !important;
                -webkit-text-fill-color: #1E293B !important;
                background-color: #F8FAFC !important;
                font-weight: 500 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.text_area("Detailed Notes:", value=record['socrates_notes'] or "No detailed notes.", height=200, disabled=True)

        with col_right:
            st.subheader("🌿 AYUSH & Integrative Assessment")
            
            # --- FIX 2: Correctly embedding text INSIDE the styled container ---
            ayush_text = record["suggested_ayush_focus"] or "Standard evaluation recommended."
            st.markdown(f"""
            <div class="alert-card-green" style="background-color: #E8F5E9; border-left: 5px solid #2E7D32; padding: 15px; border-radius: 8px; color: #1B5E20; font-size: 15px;">
                {ayush_text}
            </div>
            """, unsafe_allow_html=True)

        st.write("") # spacing spacing
        with st.expander("📜 View Raw Patient-AI Conversation Transcript"):
            if record["chat_transcript"]:
                for msg in record["chat_transcript"]:
                    role = "Patient" if msg["role"] == "user" else "AI Assistant"
                    st.write(f"**{role}:** {msg['content']}")

    # Tab 2: Patient History
    with tab2:
        st.subheader(f"📜 Complete Encounters History for {record['patient_name']}")
        past_visits = get_patient_history(record["patient_id"])
        
        if len(past_visits) <= 1:
            st.info("ℹ️ This is the patient's first recorded OPD visit in the system.")
        else:
            for idx, visit in enumerate(past_visits):
                with st.expander(f"🗓️ Visit #{visit['id']} — {visit['timestamp']} [{visit['status']}]", expanded=(idx==0)):
                    st.write(f"**Chief Complaint:** {visit['chief_complaint']}")
                    st.write(f"**SOCRATES Summary:**\n{visit['socrates_notes']}")
                    st.write(f"**AYUSH Focus:** {visit['suggested_ayush_focus']}")
                    st.write(f"**Doctor Prescription:** {visit['doctor_notes'] or 'No prescription saved.'}")

    # Tab 3: Prescription Builder
    with tab3:
        st.subheader("✍️ Physician Assessment & Prescription")

        existing_notes = record["doctor_notes"] or ""
        doctor_notes_input = st.text_area(
            "Enter Diagnosis, Classical AYUSH Formulations, Pathya/Apathya Diet, and Prescription:",
            value=existing_notes,
            height=180,
            placeholder="e.g., Provisional Diagnosis: Pitta-Jwara.\nPrescription: Sanshamani Vati 500mg BD after food.\nPathya: Light warm soup, avoid oily/spicy foods."
        )

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("💾 Save Prescription to EMR", type="primary"):
                update_doctor_notes(record["record_id"], doctor_notes_input, status="Completed")
                st.toast("Prescription saved successfully!", icon="✅")
                st.rerun()

        opd_slip_text = f"""
===================================================================
                  samvadaAI INTEGRATIVE OPD CLINIC
                      CLINICAL PRESCRIPTION SLIP
===================================================================
Date/Time : {record['timestamp']}
Record ID : #{record['record_id']}

PATIENT DEMOGRAPHICS
--------------------
Name   : {record['patient_name']}
Age/Sex: {record['age']} yrs / {record['sex']}
Phone  : {record['phone_number']}
Metrics: Height: {record['height_cm']} cm | Weight: {record['weight_kg']} kg | BMI: {bmi}

CLINICAL SUMMARY (SOCRATES)
---------------------------
Chief Complaint:
{record['chief_complaint']}

SOCRATES Notes:
{record['socrates_notes']}

AYUSH Assessment Focus:
{record['suggested_ayush_focus']}

PHYSICIAN DIAGNOSIS & PRESCRIPTION
----------------------------------
Attending Doctor: {doctor['name']} ({doctor['department']})

Notes & Treatment Plan:
{doctor_notes_input if doctor_notes_input else 'No doctor notes entered yet.'}

===================================================================
This slip is generated via samvadaAI EMR system for physician review.
===================================================================
"""
        with col_act2:
            st.download_button(
                label="📄 Export Printable OPD Slip",
                data=opd_slip_text,
                file_name=f"OPD_Slip_Patient_{record['patient_id']}.txt",
                mime="text/plain"
            )