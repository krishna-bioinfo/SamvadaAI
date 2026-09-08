# db.py
"""
Database Management Module using SQLite.
Handles user authentication (Patients & Doctors), demographic storage,
and persistent clinical intake records.
"""

import sqlite3
import hashlib
import json
from datetime import datetime

DB_FILE = "ayush_clinic.db"


def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def seed_mock_data():
    """Guarantees default mock patients and intake records are always present in SQLite."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Mock Patient A (Red Flag Chest Pain Case)
    cursor.execute("SELECT id FROM patients WHERE phone_number = '9876543210'")
    p1 = cursor.fetchone()
    if not p1:
        cursor.execute("""
            INSERT INTO patients (phone_number, password_hash, name, age, sex, height_cm, weight_kg)
            VALUES ('9876543210', ?, 'Rajesh Kumar', 52, 'Male', 172, 84)
        """, (hash_password("patient123"),))
        p1_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO intake_records 
            (patient_id, chief_complaint, socrates_notes, red_flags, suggested_ayush_focus, chat_transcript, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending Review')
        """, (
            p1_id,
            "Severe crushing chest pain radiating to left arm for 45 minutes",
            "Site: Substernal chest\nOnset: 45 min ago while climbing stairs\nCharacter: Heavy pressure/crushing\nRadiation: Left shoulder & jaw\nAssociations: Diaphoresis & mild shortness of breath",
            json.dumps(["🚨 EMERGENCY WARNING: 'Chest Pain' detected. Immediate ER triage required."]),
            "IMMEDIATE EMERGENCY REFERRAL REQUIRED. Suspected Acute Coronary Syndrome. Hold AYUSH interventions.",
            json.dumps([
                {"role": "user", "content": "I have severe crushing pain in my chest that goes down my left arm."},
                {"role": "assistant", "content": "🚨 EMERGENCY WARNING: 'Chest Pain' detected. Please seek emergency medical care immediately."}
            ])
        ))

    # 2. Mock Patient B (Pitta-Jwara Fever Case)
    cursor.execute("SELECT id FROM patients WHERE phone_number = '9876543211'")
    p2 = cursor.fetchone()
    if not p2:
        cursor.execute("""
            INSERT INTO patients (phone_number, password_hash, name, age, sex, height_cm, weight_kg)
            VALUES ('9876543211', ?, 'Ananya Rao', 28, 'Female', 162, 58)
        """, (hash_password("patient123"),))
        p2_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO intake_records 
            (patient_id, chief_complaint, socrates_notes, red_flags, suggested_ayush_focus, chat_transcript, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending Review')
        """, (
            p2_id,
            "Continuous burning fever for 4 days with excessive thirst and sweating",
            "Site: Systemic body heat\nOnset: 4 days ago\nCharacter: High burning sensation\nAssociations: Marked thirst (Pipasa), profuse sweating (Sveda), mild appetite drop\nCourse: Constant without chills",
            json.dumps([]),
            "Assessment for Pitta-Jwara (Pitta-dominant fever). Evaluate Agni status, check for Ama presence, and consider Ama-pachana measures.",
            json.dumps([
                {"role": "user", "content": "I've had a burning fever for 4 days and feel constantly thirsty."},
                {"role": "assistant", "content": "I understand. Is the fever constant or spiking, and have you noticed any changes in appetite or body pain?"}
            ])
        ))

    conn.commit()
    conn.close()

def init_db():
    """Initializes database tables if they do not exist and inserts default doctor account."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Patients Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        sex TEXT NOT NULL,
        height_cm REAL NOT NULL,
        weight_kg REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Doctors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        department TEXT DEFAULT 'AYUSH / Integrative OPD'
    )
    """)

    # 3. Intake Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS intake_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        chief_complaint TEXT,
        socrates_notes TEXT,
        red_flags TEXT,
        suggested_ayush_focus TEXT,
        chat_transcript TEXT,
        status TEXT DEFAULT 'Pending Review',
        doctor_notes TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients (id)
    )
    """)

    conn.commit()

    # Insert default Doctor account for testing
    default_doc_pass = hash_password("password123")
    try:
        cursor.execute(
            "INSERT INTO doctors (username, password_hash, name) VALUES (?, ?, ?)",
            ("doctor1", default_doc_pass, "Dr. A. Sharma (BAMS, MD)")
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Doctor already exists

    # Close connection ONLY after all queries are finished
    conn.close()

    # Seed mock data after initial tables are created
    seed_mock_data()


def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


# --- PATIENT AUTHENTICATION ---

def register_patient(phone_number, password, name, age, sex, height_cm, weight_kg):
    """Registers a new patient with physical metrics."""
    conn = get_connection()
    cursor = conn.cursor()
    hashed_pwd = hash_password(password)

    try:
        cursor.execute("""
            INSERT INTO patients (phone_number, password_hash, name, age, sex, height_cm, weight_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (phone_number, hashed_pwd, name, age, sex, height_cm, weight_kg))
        conn.commit()
        patient_id = cursor.lastrowid
        conn.close()
        return True, patient_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Phone number already registered."


def authenticate_patient(phone_number, password):
    """Verifies patient credentials and returns patient dict."""
    conn = get_connection()
    cursor = conn.cursor()
    hashed_pwd = hash_password(password)

    cursor.execute(
        "SELECT * FROM patients WHERE phone_number = ? AND password_hash = ?",
        (phone_number, hashed_pwd)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


# --- DOCTOR AUTHENTICATION ---

def authenticate_doctor(username, password):
    """Verifies doctor credentials and returns doctor dict."""
    conn = get_connection()
    cursor = conn.cursor()
    hashed_pwd = hash_password(password)

    cursor.execute(
        "SELECT * FROM doctors WHERE username = ? AND password_hash = ?",
        (username, hashed_pwd)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


# --- INTAKE RECORDS CRUD ---

def save_intake_record(patient_id, summary_dict, chat_history):
    """Saves a completed voice intake summary into the database."""
    conn = get_connection()
    cursor = conn.cursor()

    chief_complaint = summary_dict.get("chief_complaint", "")
    socrates_notes = summary_dict.get("socrates_notes", "")
    red_flags = json.dumps(summary_dict.get("red_flags", []))
    ayush_focus = summary_dict.get("suggested_ayush_focus", "")
    transcript = json.dumps(chat_history)

    cursor.execute("""
        INSERT INTO intake_records 
        (patient_id, chief_complaint, socrates_notes, red_flags, suggested_ayush_focus, chat_transcript)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (patient_id, chief_complaint, socrates_notes, red_flags, ayush_focus, transcript))

    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id


def get_all_intakes_for_doctor():
    """Fetches all intake records joined with patient demographics for the doctor queue."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            i.id AS record_id,
            i.timestamp,
            i.chief_complaint,
            i.socrates_notes,
            i.red_flags,
            i.suggested_ayush_focus,
            i.chat_transcript,
            i.status,
            i.doctor_notes,
            p.id AS patient_id,
            p.name AS patient_name,
            p.phone_number,
            p.age,
            p.sex,
            p.height_cm,
            p.weight_kg
        FROM intake_records i
        JOIN patients p ON i.patient_id = p.id
        ORDER BY i.timestamp DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    records = []
    for r in rows:
        item = dict(r)
        item["red_flags"] = json.loads(item["red_flags"]) if item["red_flags"] else []
        item["chat_transcript"] = json.loads(item["chat_transcript"]) if item["chat_transcript"] else []
        records.append(item)

    return records


def update_doctor_notes(record_id, doctor_notes, status="Completed"):
    """Updates doctor consultation notes and status for a record."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE intake_records
        SET doctor_notes = ?, status = ?
        WHERE id = ?
    """, (doctor_notes, status, record_id))

    conn.commit()
    conn.close()

def get_patient_history(patient_id):
    """Fetches all past intake records for a specific patient ordered by date."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM intake_records
        WHERE patient_id = ?
        ORDER BY timestamp DESC
    """, (patient_id,))

    rows = cursor.fetchall()
    conn.close()

    history = []
    for r in rows:
        item = dict(r)
        item["red_flags"] = json.loads(item["red_flags"]) if item["red_flags"] else []
        item["chat_transcript"] = json.loads(item["chat_transcript"]) if item["chat_transcript"] else []
        history.append(item)

    return history


# Automatically initialize tables when module is imported
init_db()