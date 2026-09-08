# theme.py
import streamlit as st

def apply_custom_theme():
    """Injects high-contrast, modern clinical CSS for hackathon-grade UI."""
    st.markdown("""
        <style>
        /* Modern Clinical Background */
        .stApp {
            background-color: #F4F7F6 !important;
            color: #1E293B !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Force high contrast text on standard markdown & labels */
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, div, span {
            color: #0F172A !important;
        }

        /* Card Container Styling */
        .patient-card {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 1.2rem 1.5rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        
        .patient-badge {
            background-color: #DCFCE7 !important;
            color: #166534 !important;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.85rem;
            border: 1px solid #BBF7D0;
        }

        /* App Banner Header */
        .app-header {
            background: linear-gradient(135deg, #064E3B 0%, #047857 100%);
            padding: 1.2rem 2rem;
            border-radius: 16px;
            color: white !important;
            margin-bottom: 1.8rem;
            box-shadow: 0 10px 20px rgba(6, 78, 59, 0.15);
        }
        .app-header h1, .app-header p {
            color: #FFFFFF !important;
        }

        /* Metric Box Styling */
        .metric-box {
            background: #FFFFFF !important;
            border-radius: 12px;
            padding: 1.2rem;
            border-left: 6px solid #047857;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
            border-top: 1px solid #E2E8F0;
            border-right: 1px solid #E2E8F0;
            border-bottom: 1px solid #E2E8F0;
        }

        /* Triage Alert Cards */
        .alert-card-red {
            background-color: #FEF2F2 !important;
            border-left: 6px solid #EF4444 !important;
            border-radius: 12px;
            padding: 1.2rem;
            color: #991B1B !important;
            margin-bottom: 1rem;
            border: 1px solid #FCA5A5;
        }
        .alert-card-red h4, .alert-card-red p, .alert-card-red li {
            color: #991B1B !important;
        }

        .alert-card-green {
            background-color: #F0FDF4 !important;
            border-left: 6px solid #22C55E !important;
            border-radius: 12px;
            padding: 1.2rem;
            color: #166534 !important;
            margin-bottom: 1rem;
            border: 1px solid #86EFAC;
        }
        .alert-card-green h4, .alert-card-green p, .alert-card-green li {
            color: #166534 !important;
        }

        /* Styled Input Box Backgrounds */
        .stTextArea textarea, .stTextInput input {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1.5px solid #CBD5E1 !important;
            border-radius: 10px !important;
            font-size: 0.95rem;
        }
        .stTextArea textarea:focus, .stTextInput input:focus {
            border-color: #047857 !important;
            box-shadow: 0 0 0 3px rgba(4, 120, 87, 0.2) !important;
        }

        /* Tab Bar Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #E2E8F0;
            padding: 6px;
            border-radius: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 42px;
            background-color: transparent;
            border-radius: 8px;
            padding: 0 16px;
            font-weight: 600;
            color: #475569 !important;
            border: none !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            color: #047857 !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        }

        /* Streamlit Buttons */
        .stButton button {
            border-radius: 10px !important;
            font-weight: 600 !important;
        }
        </style>
    """, unsafe_allow_html=True)