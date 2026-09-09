# app.py
import streamlit as st
from theme import apply_custom_theme
from db import init_db, authenticate_patient, register_patient, authenticate_doctor
from views.patient_view import render_patient_view
from views.doctor_view import render_doctor_view

st.set_page_config(
    page_title="samvadaAI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_theme()
init_db()

# Initialize Session Auth States
if "current_user_role" not in st.session_state:
    st.session_state.current_user_role = None  # Options: 'patient', 'doctor', None
if "patient_user" not in st.session_state:
    st.session_state.patient_user = None
if "doctor_user" not in st.session_state:
    st.session_state.doctor_user = None

# Header Banner
st.markdown("""
<div class="app-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1>🌿 samvadaAI</h1>
            <p>Multilingual Voice AI Triage & Integrative OPD Clinical Assistant</p>
        </div>
        <div>
            <span style="background: rgba(255,255,255,0.2); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
                SIH26047 • Healthcare & Ayush
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


def logout_user():
    """Clears all session states upon logout."""
    st.session_state.current_user_role = None
    st.session_state.patient_user = None
    st.session_state.doctor_user = None
    st.session_state.chat_history = []
    st.session_state.is_done = False
    st.rerun()


# --- ROUTE 1: UNAUTHENTICATED LANDING & LOGIN PAGE ---
if st.session_state.current_user_role is None:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        # Pill Toggle Switcher (Inspired by Mentee/Mentor toggle)
        selected_role = st.segmented_control(
            "Select Portal Access",
            options=["🧑 Patient Access", "👨‍⚕️ Doctor / Clinical EMR"],
            default="🧑 Patient Access",
            label_visibility="collapsed"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ---------------- PATIENT AUTHENTICATION ----------------
        if selected_role == "🧑 Patient Access":
            auth_tab1, auth_tab2 = st.tabs(["🔑 Patient Login", "📝 New Registration"])
            
            with auth_tab1:
                with st.form("patient_login_form"):
                    st.subheader("Login to Patient Account")
                    phone = st.text_input("Mobile Phone Number", value="9876543210")
                    pwd = st.text_input("Password", type="password", value="patient123")
                    submit = st.form_submit_button("Sign In & Proceed to Intake", use_container_width=True)

                    if submit:
                        user = authenticate_patient(phone, pwd)
                        if user:
                            st.session_state.patient_user = user
                            st.session_state.current_user_role = "patient"
                            st.success(f"Welcome back, {user['name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid phone number or password.")

            with auth_tab2:
                with st.form("patient_reg_form"):
                    st.subheader("Register Patient Profile")
                    name = st.text_input("Full Name", placeholder="e.g., Ananya Rao")
                    phone = st.text_input("Phone Number (10 digits)", placeholder="e.g., 9876543212")
                    pwd = st.text_input("Account Password", type="password")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        age = st.number_input("Age", min_value=1, max_value=110, value=28)
                    with c2:
                        sex = st.selectbox("Sex", ["Female", "Male", "Other"])
                    with c3:
                        height = st.number_input("Height (cm)", min_value=50.0, max_value=250.0, value=162.0)
                    weight = st.number_input("Weight (kg)", min_value=10.0, max_value=250.0, value=58.0)

                    reg_submit = st.form_submit_button("Create Account & Start Intake", use_container_width=True)
                    if reg_submit:
                        if not name or not phone or not pwd:
                            st.error("Please fill in all required fields.")
                        else:
                            new_user = create_patient(phone, pwd, name, age, sex, height, weight)
                            if new_user:
                                st.session_state.patient_user = new_user
                                st.session_state.current_user_role = "patient"
                                st.success("Registration successful!")
                                st.rerun()
                            else:
                                st.error("Phone number is already registered.")

        # ---------------- DOCTOR AUTHENTICATION ----------------
        else:
            with st.form("doctor_login_form"):
                st.subheader("👨‍⚕️ Physician EMR Login")
                doc_user = st.text_input("Physician Username", value="doctor1")
                doc_pass = st.text_input("Password", type="password", value="password123")
                doc_submit = st.form_submit_button("Authenticate & Open OPD Dashboard", use_container_width=True)

                if doc_submit:
                    user = authenticate_doctor(doc_user, doc_pass)
                    if user:
                        st.session_state.doctor_user = user
                        st.session_state.current_user_role = "doctor"
                        st.success(f"Authenticated: Dr. {user['name']}")
                        st.rerun()
                    else:
                        st.error("Invalid doctor credentials.")
            st.caption("💡 Test Credentials — Username: `doctor1` | Password: `password123`")

# --- ROUTE 2: PATIENT VIEW ---
elif st.session_state.current_user_role == "patient":
    st.sidebar.markdown(f"### 🧑 Logged in as:")
    st.sidebar.write(f"**{st.session_state.patient_user['name']}**")
    st.sidebar.caption(f"Phone: {st.session_state.patient_user['phone_number']}")
    if st.sidebar.button("🚪 Logout Patient", use_container_width=True):
        logout_user()

    render_patient_view()

# --- ROUTE 3: DOCTOR VIEW ---
elif st.session_state.current_user_role == "doctor":
    st.sidebar.markdown(f"### 👨‍⚕️ Logged in as:")
    st.sidebar.write(f"**Dr. {st.session_state.doctor_user['name']}**")
    st.sidebar.caption(f"Dept: {st.session_state.doctor_user['department']}")
    if st.sidebar.button("🚪 Logout Doctor", use_container_width=True):
        logout_user()

    render_doctor_view()