from typing import Any, Dict, List, Optional
import pandas as pd
import requests
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv
import json
import os
import google.generativeai as genai
import time
import random
import altair as alt
from datetime import datetime
from io import BytesIO
import xlsxwriter
import streamlit.components.v1 as components
import html
from datetime import datetime
from anthropic import Anthropic
import openai
import csv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic.chat_models import ChatAnthropic
from langchain_xai import ChatXAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores.azuresearch import AzureSearch as AzureSearchStore
from langchain.chains import RetrievalQA    

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai.api_key = os.getenv("OPENAI_API_KEY")
# Load environment variables
load_dotenv()

# Constants
DATABASE = st.secrets["database"]
SCHEMA = st.secrets["schema"]
STAGE = st.secrets["stage"]
FILE = st.secrets["yaml_name"]
WAREHOUSE = st.secrets["warehouse"]
HOST = st.secrets["host"]
ACCOUNT = st.secrets["account"]
USER = st.secrets["user_name"]
PASSWORD = st.secrets["password"]
ROLE = st.secrets["role"]
GOOGLE_API_KEY = st.secrets["GEMINI_API_KEY"]
ANTHROPIC_API_KEY=st.secrets["CLAUDE_API_KEY"]
chat_mode = "Select Chat Mode"

@st.cache_resource
def get_snowflake_connection():
    try:
        conn = snowflake.connector.connect(
            user=USER,
            password=PASSWORD,
            account=ACCOUNT,
            host=HOST,
            port=443,
            warehouse=WAREHOUSE,
            role=ROLE,
        )
        return conn
    except Exception as e:
        st.error(f"Failed to establish Snowflake connection: {str(e)}")
        return None

def execute_query(query: str):
    conn = get_snowflake_connection()
    if conn is None:
        st.error("No valid Snowflake connection available.")
        return pd.DataFrame()
    
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return pd.DataFrame(result, columns=[col[0] for col in cursor.description])
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        return pd.DataFrame()
    finally:
        cursor.close()




    

# Theme colors
PRIMARY_COLOR = "#282828"
SECONDARY_COLOR = "#868686" 
BACKGROUND_COLOR = "#F5F7F8"
TEXT_COLOR = "#333333"
USER_BUBBLE_COLOR = "#E3F4F4"
ANALYST_BUBBLE_COLOR = "#D2E0FB"
ACCENT_COLOR = "#4B56D2"
ACCENT_HOVER_COLOR = "#3A45C1"

# Streamlit page config
st.set_page_config(
    page_title="Cortex Analyst", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:support@example.com',
        'Report a bug': 'mailto:bugs@example.com',
        'About': 'Cortex Analyst is your AI-powered data assistant.'
    }
)

# Enhanced Custom CSS with all suggested improvements
st.markdown("""
<style>
    /* Overall app styling */
    .stApp {
        background-color: #F5F7F8;
    }
    
    /* Card styling */
    .dashboard-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .dashboard-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* Improved buttons */
    .custom-button {
        background-color: #4B56D2;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 8px 16px;
        font-size: 0.9em;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .custom-button:hover {
        background-color: #3A45C1;
        transform: translateY(-1px);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #F5F7F8;
    }
    
    /* Chat input area */
    .stChatInput {
        border-radius: 20px;
        background-color: white;
        border: 1px solid #E0E0E0;
        transition: border 0.3s ease, box-shadow 0.3s ease;
    }
    
    .stChatInput:focus-within {
        border-color: #4B56D2;
        box-shadow: 0 0 0 2px rgba(75, 86, 210, 0.2);
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 15px;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        font-weight: 500;
    }
    
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Primary button styling */
    .stButton>button[kind="primary"] {
        background-color: #4B56D2;
        color: white;
    }
    
    .stButton>button[kind="primary"]:hover {
        background-color: #3A45C1;
    }
    
    /* Suggestion button styling */
    .suggestion-btn {
        background-color: #D2E0FB;
        border: none;
        border-radius: 18px;
        padding: 8px 12px;
        margin: 5px;
        font-size: 0.9em;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .suggestion-btn:hover {
        background-color: #4B56D2;
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Improved tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 0;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4B56D2;
        color: white;
    }
    
    /* Welcome animation */
    @keyframes fadeIn {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    
    .welcome-banner {
        animation: fadeIn 1.5s;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        padding: 8px 12px;
    }
    
    .typing-indicator span {
        height: 8px;
        width: 8px;
        background-color: #4B56D2;
        border-radius: 50%;
        margin: 0 2px;
        display: inline-block;
        animation: bounce 1.5s infinite ease-in-out;
    }
    
    .typing-indicator span:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-indicator span:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes bounce {
        0%, 60%, 100% {
            transform: translateY(0);
        }
        30% {
            transform: translateY(-5px);
        }
    }
    
    /* Chat message animations */
    @keyframes slideIn {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    .slide-in {
        animation: slideIn 0.3s ease-out forwards;
    }
    
    /* Loading states */
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    
    .loading-pulse {
        animation: pulse 1.5s infinite ease-in-out;
    }
    
    /* Chart container */
    .chart-container {
        transition: all 0.5s ease;
    }
    
    /* Tutorial styles */
    .tutorial-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0,0,0,0.7);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.5s;
    }
    
    .tutorial-card {
        background-color: white;
        border-radius: 15px;
        padding: 30px;
        max-width: 500px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    .tutorial-step {
        margin-bottom: 20px;
    }
    
    .tutorial-button {
        background-color: #4B56D2;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 10px 20px;
        cursor: pointer;
        font-size: 1em;
        transition: all 0.3s ease;
    }
    
    .tutorial-button:hover {
        background-color: #3A45C1;
    }
    
    .spotlight {
        position: absolute;
        border-radius: 50%;
        box-shadow: 0 0 0 9999px rgba(0,0,0,0.7);
        pointer-events: none;
    }
    
    /* Keyboard shortcuts */
    .keyboard-shortcuts {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(245, 247, 248, 0.9);
        padding: 8px 20px;
        font-size: 0.8em;
        text-align: center;
        border-top: 1px solid #eee;
        display: flex;
        justify-content: center;
        gap: 20px;
        backdrop-filter: blur(5px);
        z-index: 1000;
    }
    
    .shortcut-key {
        display: inline-flex;
        align-items: center;
    }
    
    kbd {
        background-color: #f7f7f7;
        border: 1px solid #ccc;
        border-radius: 3px;
        box-shadow: 0 1px 0 rgba(0,0,0,0.2);
        color: #333;
        display: inline-block;
        font-size: 0.85em;
        font-weight: 700;
        line-height: 1;
        padding: 2px 4px;
        margin-right: 5px;
        white-space: nowrap;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        /* Adjust sidebar */
        .css-1d391kg {
            width: 100% !important;
        }
        
        /* Make bubbles take more width */
        [style*="max-width: 80%"] {
            max-width: 95% !important;
        }
        
        /* Stack controls on mobile */
        .stColumns [data-testid="column"] {
            width: 100% !important;
            margin-bottom: 1rem;
        }
        
        /* Adjust buttons */
        .stButton>button {
            width: 100%;
        }
        
        /* Adjust keyboard shortcuts */
        .keyboard-shortcuts {
            flex-direction: column;
            gap: 5px;
            padding: 5px;
        }
    }
    
    /* Dark mode support */
    body.dark-theme {
        background-color: #1E1E1E !important;
        color: #E0E0E0 !important;
    }
    
    body.dark-theme .stApp {
        background-color: #1E1E1E !important;
    }
    
    body.dark-theme .dashboard-card {
        background-color: #2D2D2D !important;
        color: #E0E0E0 !important;
    }
    
    body.dark-theme .stTextInput>div>div>input {
        background-color: #3D3D3D !important;
        color: #E0E0E0 !important;
    }
    
    body.dark-theme .stButton>button {
        background-color: #4B56D2 !important;
        color: white !important;
    }
    
</style>

<script>
function toggleTheme() {
    const body = document.body;
    const isDark = body.classList.contains('dark-theme');
    
    if (isDark) {
        body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
    }
}

// Check user preference on load
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || 
        (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.body.classList.add('dark-theme');
    }
    
    // Add smooth scrolling to new messages
    const chatContainer = document.querySelector('.stChatMessageContent');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});

function handleResize() {
    // Add responsive adjustments
    const width = window.innerWidth;
    const isMobile = width < 768;
    
    // Adjust layout for mobile
    if (isMobile) {
        document.body.classList.add('mobile-view');
    } else {
        document.body.classList.remove('mobile-view');
    }
}

window.addEventListener('resize', handleResize);
handleResize();
</script>
""", unsafe_allow_html=True)

# App header with modern design
if st.session_state.get("chat_mode", "Structured Data Search") == "Unstructured Chat":
    st.markdown(f"""
<div class="welcome-banner dashboard-card" style="background: linear-gradient(135deg, {PRIMARY_COLOR}, {SECONDARY_COLOR});
padding:20px; border-radius:15px; margin-bottom:30px; color:white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <h1 style="margin:0; display:flex; align-items:center;">
        <span style="font-size:2rem; margin-right:10px;">💻</span>
        UnStructBot
    </h1>
    <p style="opacity:0.8; margin-top:10px;">Your Smart AI assistant. Talk your data.</p>
</div>
""", unsafe_allow_html=True)
else: 
    st.markdown(f"""
<div class="welcome-banner dashboard-card" style="background: linear-gradient(135deg, {PRIMARY_COLOR}, {SECONDARY_COLOR});
padding:20px; border-radius:15px; margin-bottom:30px; color:white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <h1 style="margin:0; display:flex; align-items:center;">
        <span style="font-size:2rem; margin-right:10px;">💻</span>
        StructBot
    </h1>
    <p style="opacity:0.8; margin-top:10px;">Your Smart AI assistant. Talk your data.</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "active_suggestion" not in st.session_state:
    st.session_state.active_suggestion = None
    
if "first_visit" not in st.session_state:
    st.session_state.first_visit = True
    
if "typing" not in st.session_state:
    st.session_state.typing = False
    
if "tutorial_step" not in st.session_state:
    st.session_state.tutorial_step = 0
    
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Check URL parameters for tutorial advancement
query_params = st.query_params
if "tutorial_step" in query_params:
    try:
        st.session_state.tutorial_step = int(query_params["tutorial_step"][0])
    except ValueError:
        pass

if "tutorial_complete" in query_params:
    st.session_state.first_visit = False


st.markdown("""
    <style>
        /* Shrink all sidebar text */
        [data-testid="stSidebar"] * {
            font-size: 13px !important;
        }

        /* Tighten padding around elements */
        [data-testid="stSidebar"] .css-1v3fvcr,  
        [data-testid="stSidebar"] .css-1d391kg {
            padding: 5px 10px !important;
            margin: 0 !important;
        }

        /* Compact headers */
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3 {
            font-size: 16px !important;
        }

        /* Compact buttons, sliders */
        [data-testid="stSidebar"] button, 
        [data-testid="stSidebar"] .stSlider,
        [data-testid="stSidebar"] .stDownloadButton {
            font-size: 12px !important;
            padding: 4px 8px !important;
        }

        /* Optional: reduce sidebar image size */
        [data-testid="stSidebar"] img {
            max-width: 120px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)


# if "chat_mode" not in st.session_state:
#     st.session_state.chat_mode = "Structured Data Search"


# Enhanced sidebar with modern styling
with st.sidebar:
    # initialize default only once
    if "chat_mode" not in st.session_state:
        st.session_state.chat_mode = "Structured Data Search"

    # single selectbox, tied to session_state via its key
    chat_mode = st.selectbox(
        "💬 Select Chat Mode",
        ["Structured Data Search", "Unstructured Chat"],
        index=["Structured Data Search", "Unstructured Chat"]
              .index(st.session_state.chat_mode),
        key="chat_mode",
    )

    if chat_mode != st.session_state.chat_mode:
        st.session_state.chat_mode = chat_mode
        st.rerun()

    st.image("logo.jpg", use_container_width=True)

    cols = st.columns(3)  # Create 3 columns in one row

# Add content to each tile (J1, J2, J3, etc.)
    # Define colors
    PRIMARY_COLOR = "#4CAF50"  # You can replace this with your desired color
    TEXT_COLOR = "#333333"  # You can replace this with your desired text color
    # tile_queries = [
    #     "select count(*) from bridgehorn_sandbox.cortex_analyst.PPP_CDM_COMPANY c join bridgehorn_sandbox.cortex_analyst.PPP_CDM_OPPORTUNITIES o on o.company_id=c.company_id join bridgehorn_sandbox.cortex_analyst.PPP_CDM_OPPORTUNITY_PHASE op on o.opportunity_id=op.related_opportunity_id where o.opportunity_stage='Active';",  # Query for Tile 1
    #     "select count(*) from bridgehorn_sandbox.cortex_analyst.ppp_cdm_opportunities where opportunity_status='Open';",  # Query for Tile 2
    #     "select count(KP.PROJECT_ID,KP.PROJECT_TITLE, AC.NAME) From BRIDGEHORN_SANDBOX.CDM.PPP_CDM_KANTATA_PROJECTS as KP left join Kantata.MODELED.WORKSPACES as WP on WP.ID = KP.PROJECT_ID left join KANTATA.MODELED.ACCOUNT_COLORS as AC on AC.ID=WP.ACCOUNT_COLOR_ID Where PROJECT_STATUS in ('Completed','Active') and AC.Name <> 'DE'",  # Query for Tile 3
    #     "select count(distinct EMPLOYEE_NUMBER) from zenefits.cleansed.people ;",  # Query for Tile 4
    # ]
    # tile_data = [execute_query(query) for query in tile_queries]
    # tile_val=["Companies", "Opportunities", "Projects", "Employees"]
    # # Create 2 tiles in the first row (3 columns layout)
    # cols = st.columns(2)  # Create 2 columns in one row

    # # Add content to each tile (Tile 0, Tile 1, etc.)
    # for i in range(2):
    #     with cols[i]:
    #         data = tile_data[i].iloc[0, 0] if not tile_data[i].empty else "No Data"
    #         st.markdown(f"""
    #         <div style="text-align:center; background-color:#f9f9fb; margin:5px; padding:10x; border-radius:10px; box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);">
    #             <h3 style="color:{TEXT_COLOR};font-size:24px;">{data}</h3>
    #             <p style="font-size:0.8em; color:{TEXT_COLOR}; margin-top:4px;">{tile_val[i]}</p>
    #         </div>
    #         """, unsafe_allow_html=True)


    # # Create second row for the tiles (3 columns layout)
    # cols2 = st.columns(2)  # Create 2 columns in the second row

    # # Add content to each tile (Tile 2, Tile 3)
    # for i in range(2, 4):
    #     with cols2[i-2]:  # Adjust the column index for the second row
    #         data = tile_data[i].iloc[0, 0] if not tile_data[i].empty else "No Data"
    #         st.markdown(f"""
    #             <div style="text-align:center; background-color:#f9f9fb; margin:5px; padding:10x; border-radius:10px; box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);">
    #                 <h3 style="color:{TEXT_COLOR};font-size:24px;">{data}</h3>
    #                 <p style="font-size:0.8em; color:{TEXT_COLOR}; margin-top:4px;">{tile_val[i]}</p>
    #             </div>
    #             """, unsafe_allow_html=True)



        
    # Session management with improved buttons
    st.markdown(f"### Session Controls")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat"):
            st.session_state.messages = []
            st.session_state.active_suggestion = None
            st.toast("Chat history cleared!", icon="🧹")
            st.rerun()
            
    with col2:
        if st.button("📥 Export Chat", use_container_width=True, key="export_chat"):
            # Create a comprehensive export of the chat
            chat_export = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                "messages": []
            }
            
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    chat_export["messages"].append({"role": "user", "text": msg["content"][0]["text"]})
                else:
                    # Extract just the text content for simplicity
                    text_content = [item["text"] for item in msg["content"] if item["type"] == "text"]
                    chat_export["messages"].append({"role": "analyst", "text": " ".join(text_content)})
            
            st.download_button(
                label="Download JSON",
                data=json.dumps(chat_export, indent=2),
                file_name=f"cortex_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key="download_chat"
            )
    
    # Sample questions with improved styling
    st.markdown("### Sample Questions")
    if st.session_state.get("chat_mode", "Structured Data Search") == "Unstructured Chat":

        sample_questions1=[
            'What is the update on Concur Integraration?',
            "How is Bynder-Matillion integration going on?",
            "What is the status of CDM view consolidation"
        ]
        for idx, question in enumerate(sample_questions1):
            if st.button(f"🔍 {question}", key=f"sample_question_{idx}", use_container_width=True):
                st.session_state.active_suggestion = question
                st.rerun()
    else:
        sample_questions2 = [
            "What are the top 5 companies by deal count?",
            "Show me asset distribution by region",
            "Compare deal values year over year",
            "Which sectors have the highest growth rate?"
        ]
        for idx, question in enumerate(sample_questions2):
            if st.button(f"🔍 {question}", key=f"sample_question_{idx}", use_container_width=True):
                st.session_state.active_suggestion = question
                st.rerun()
    
    # Enhanced Help & Resources section
    with st.expander("ℹ️ Help & Resources", expanded=False):
        st.markdown("""
        <div class="dashboard-card" style="padding:10px;">
            <h4>Quick Tips</h4>
            <ul>
                <li>Be specific with your questions</li>
                <li>You can ask for specific visualizations</li>
                <li>Export results for further analysis</li>
                <li>Use sample questions to get started</li>
            </ul>
        </div>
        
        <div class="dashboard-card" style="padding:10px; margin-top:10px;">
            <h4>Documentation</h4>
            <p>For detailed documentation and guides, visit our <a href="#" target="_blank">help center</a>.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced User Preferences
    with st.expander("⚙️ Preferences", expanded=False):
        st.slider("Chart Animation Speed", 0.1, 2.0, 1.0, 0.1, key="animation_speed", 
                 help="Control the speed of chart animations")
        st.toggle("Auto-expand SQL queries", value=False, key="auto_expand_sql",
                 help="Automatically show SQL queries for each response")
        theme = st.selectbox("UI Theme", ["Light", "Dark"], index=0, key="ui_theme",
                            help="Change the appearance of the interface")
        
        if theme == "Dark" and not st.session_state.get("theme_changed", False):
            st.session_state.theme_changed = True
            st.markdown("""
            <script>
                document.body.classList.add('dark-theme');
                localStorage.setItem('theme', 'dark');
            </script>
            """, unsafe_allow_html=True)
        elif theme == "Light" and st.session_state.get("theme_changed", False):
            st.session_state.theme_changed = False
            st.markdown("""
            <script>
                document.body.classList.remove('dark-theme');
                localStorage.setItem('theme', 'light');
            </script>
            """, unsafe_allow_html=True)
            
        st.info("Some settings may require a page refresh to apply fully")

# Initialize connection

# Ensure connection is available
if "CONN" not in st.session_state or st.session_state.CONN is None:
    try:
        st.session_state.CONN = get_snowflake_connection()
        if st.session_state.CONN is None:
            st.stop()
    except Exception as e:
        st.error(f"Failed to connect to Snowflake: {str(e)}")
        st.stop()

def show_tutorial():
    """Show interactive tutorial for first-time users"""
    tutorial_steps = [
        {
            "title": "Welcome to Cortex Analyst!",
            "text": "Your smart AI assistant for data analysis. Let me show you around. Click 'Next' to continue.",
            "target": None
        },
        {
            "title": "Ask Questions",
            "text": "Type your data questions here and press Enter to send. Try asking about companies, deals, assets, and more.",
            "target": "chat_input"
        },
        {
            "title": "Sample Questions",
            "text": "Not sure what to ask? Try one of these sample questions from the sidebar.",
            "target": "sidebar"
        },
        {
            "title": "View Results",
            "text": "After running a query, you'll see the data in tables and visualizations that you can interact with.",
            "target": "results"
        },
        {
            "title": "Ready to Go!",
            "text": "You're all set! Start asking questions about your data and explore the insights.",
            "target": None
        }
    ]
    
    current_step = tutorial_steps[st.session_state.tutorial_step]
    button_text = 'Next' if st.session_state.tutorial_step < len(tutorial_steps) - 1 else 'Finish'
    target_json = json.dumps(current_step["target"])
    htmlcode=f"""
    <div class="tutorial-overlay" id="tutorial-overlay">
        <div class="tutorial-card">
            <h2>{current_step['title']}</h2>
            <p>{current_step['text']}</p>
            <div style="display: flex; justify-content: space-between; margin-top: 20px;">
                <button class="tutorial-button" onclick="hideTutorial()" style="background-color: #868686;">
                    Skip Tutorial
                </button>
                <button class="tutorial-button" onclick="nextTutorialStep()">
                    {'Next' if st.session_state.tutorial_step < len(tutorial_steps) - 1 else 'Finish'}
                </button>
            </div>
        </div>
    </div>
    <script>
        function hideTutorial() {{
            document.getElementById('tutorial-overlay').style.display = 'none';
            window.location.href = window.location.pathname + '?tutorial_complete=true';
        }}
        
        function nextTutorialStep() {{
            window.location.href = window.location.pathname + '?tutorial_step={st.session_state.tutorial_step + 1}';
        }}
        
        // Add spotlight effect if there's a target
        const target = '{current_step["target"]}';
        if (target && target !== 'None') {{
            const targetElem = document.querySelector(`[data-testid="${{target}}"]`) || 
                               document.getElementById(target);
            if (targetElem) {{
                const rect = targetElem.getBoundingClientRect();
                const spotlight = document.createElement('div');
                spotlight.className = 'spotlight';
                spotlight.style.top = `${{rect.top + rect.height/2}}px`;
                spotlight.style.left = `${{rect.left + rect.width/2}}px`;
                spotlight.style.width = `${{rect.width + 20}}px`;
                spotlight.style.height = `${{rect.height + 20}}px`;
                document.body.appendChild(spotlight);
            }}
        }}
    </script>"""
    components.html(htmlcode, height=600, unsafe_allow_html=True)


def render_chat_bubble(role: str, message: str, timestamp=None):
    """Enhanced chat bubble rendering with avatars, timestamps, and HTML support"""
    avatar = "👤" if role == "user" else "🤖"
    bg_color = USER_BUBBLE_COLOR if role == "user" else ANALYST_BUBBLE_COLOR
    text_align = "right" if role == "user" else "left"
    flex_direction = "row-reverse" if role == "user" else "row"
    shadow = "rgba(0,0,0,0.1)"

    # Escape the message content to prevent XSS
    escaped_message = html.escape(message).replace('\n', '<br>')

    # Create a clean HTML bubble with proper structure
    html_bubble = f"""
    <div class="slide-in" style="display: flex; flex-direction: {flex_direction}; margin: 10px 0; align-items: flex-start; gap: 10px;">
        <div style="background-color: {bg_color}; color: #333333; padding: 12px 18px; border-radius: 18px; 
                    max-width: 80%; box-shadow: 0 2px 5px {shadow}; word-wrap: break-word; text-align: {text_align}">
            {escaped_message}
            <div style="font-size: 0.7em; color: #777; margin-top: 5px;">
                {timestamp or datetime.now().strftime('%H:%M')}{' ✓✓' if role == 'user' else ''}
            </div>
        </div>
        <div style="width: 36px; height: 36px; border-radius: 50%; background-color: {bg_color}; 
                    display: flex; align-items: center; justify-content: center; font-size: 16px; 
                    box-shadow: 0 2px 5px {shadow}">
            {avatar}
        </div>
    </div>
    """

    # Render the HTML bubble
    st.markdown(html_bubble, unsafe_allow_html=True)

# def render_typing_indicator():
#     """Enhanced typing indicator with better animation"""
#     return """
#     <div class="slide-in" style="display: flex; flex-direction: row; margin: 10px 0; align-items: flex-start; gap: 10px;">
#         <div style="width: 36px; height: 36px; border-radius: 50%; background-color: #D2E0FB; 
#                    display: flex; align-items: center; justify-content: center; font-size: 16px;
#                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            
#         </div>
#         <div class="typing-indicator" style="background-color: #D2E0FB; border-radius: 18px; padding: 15px;">
#             <span></span>
#             <span></span>
#             <span></span>
#         </div>
#     </div>
#     """

def render_suggestion_button(label: str, key: str):
    """Render an improved suggestion button"""
    if st.button(label, key=key, help="Click to use this suggestion", 
                use_container_width=False, 
                type="primary" if random.choice([True, False]) else "secondary"):
        st.session_state.active_suggestion = label
        st.rerun()

def suggest_chart_type(df, x_col, y_col):
    """Intelligently suggest chart type based on data characteristics"""
    # Check if x is categorical/date and y is numeric
    x_is_numeric = pd.api.types.is_numeric_dtype(df[x_col])
    x_is_datetime = pd.api.types.is_datetime64_dtype(df[x_col])
    y_is_numeric = pd.api.types.is_numeric_dtype(df[y_col])
    unique_x = df[x_col].nunique()
    
    if unique_x <= 8 and y_is_numeric:
        return "Bar Chart 📊"  # Small number of categories
    elif (x_is_datetime or x_is_numeric) and y_is_numeric:
        return "Line Chart 📈"  # Time series or continuous x-axis
    elif x_is_numeric and y_is_numeric:
        return "Scatter Plot 📊"  # Two numeric variables
    elif unique_x <= 6 and y_is_numeric:
        return "Pie Chart 🥧"  # Very few categories
    else:
        return "Bar Chart 📊"  # Default

def send_message(prompt: str) -> Dict[str, Any]:
    request_body = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": get_better_prompt(prompt)}]}],
        "semantic_model_file": f"@{DATABASE}.{SCHEMA}.{STAGE}/{FILE}",
    }
    
    try:
        print(st.session_state.CONN.rest.token)
        with st.spinner("Talking to Cortex..."):
            resp = requests.post(
                url=f"https://{HOST}/api/v2/cortex/analyst/message",
                json=request_body,
                headers={
                    "Authorization": f'Snowflake Token="{st.session_state.CONN.rest.token}"',
                    "Content-Type": "application/json",
                },
                timeout=5000
            )
        
        request_id = resp.headers.get("X-Snowflake-Request-Id")
        
        if resp.status_code < 400:
            return {**resp.json(), "request_id": request_id}
        else:
            error_message = f"API Error ({resp.status_code}): {resp.text}"
            st.toast("Error communicating with Cortex", icon="🚨")
            return {
                "message": {"content": [{"type": "text", "text": error_message}]},
                "request_id": request_id,
            }
    except requests.Timeout:
        st.toast("Request timed out! The server may be busy.", icon="⏱️")
        return {
            "message": {"content": [{"type": "text", "text": "I'm sorry, but the request timed out. Please try again in a moment."}]},
            "request_id": "N/A",
        }
    except Exception as e:
        st.toast("Connection error occurred!", icon="🚨")
        return {
            "message": {"content": [{"type": "text", "text": f"Connection error: {str(e)}. Please check your network connection and try again."}]},
            "request_id": "N/A",
        }

def get_llm_summary(user_prompt: str, df: pd.DataFrame) -> str:
    if df.empty:
        return "No data available for summary."

    if not os.getenv("GEMINI_API_KEY"):
        return "Google API key not configured for summarization."

    # Prepare your prompt
    sample = df.to_markdown(index=False)
    prompt = (
        f"A customer asked: {user_prompt}\n\n"
        f"Based on the analysis, here is the output:\n{sample}\n\n"
        "Please provide a concise summary of the data in the sample above. "
        "Do not write an email or respond to the customer — just summarize the key insights from the data only."
    )

    try:
        client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
                model="o3-mini",  # Or "gpt-4" / "gpt-4-0125-preview"
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.7
            )
        return response.choices[0].message.content
    except Exception as e:
        st.warning(f"Failed to summarize: {str(e)}", icon="⚠️")
        return e



def get_better_prompt(prompt):
    if os.getenv("OPENAI_API_KEY") is None:
        return prompt
    
    try:
        with open("pppcdmai.yaml", "r") as f:
            yaml_content = f.read()
    except FileNotFoundError:
        st.warning("YAML file not found. Using original prompt.", icon="⚠️")
        return prompt
    


    context = f"""
You are a helpful assistant that rewrites user questions so they are better understood by Cortex Analyst, 
which generates SQL based on a semantic model.

Here is the semantic model (YAML format) defining the available tables, fields, and relationships:
{yaml_content}

Your job is to take the user's question and rephrase it into a clear, structured analytical request that:
- Uses fully-qualified field names (e.g. `TABLE.COLUMN`) wherever possible
- Hints at how tables should be joined using keys defined in the model
- Requests aggregations like counts, averages, or groupings where relevant
- Preserves all the original analytical intent

Use clear language and help Cortex Analyst build the most accurate query.
"""
    new_prompt = f"{context}\nUser Question: {prompt}\nRephrased Question:"

    try:
        client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="o3-mini",  # Or "gpt-4" / "gpt-4-0125-preview"
            messages=[{"role": "user", "content": new_prompt}],
            max_tokens=1024,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.warning(f"Prompt enhancement failed: {str(e)}. Using original prompt.", icon="⚠️")
        return prompt


def display_content(content: List[Dict[str, str]], request_id: Optional[str] = None, 
                   message_index: Optional[int] = None, prompt: Optional[str] = None):
    """Enhanced content display with improved visualizations and front-end integration"""
    message_index = message_index or len(st.session_state.messages)
    
    if st.session_state.get("show_debug", False):
        with st.expander("🔍 Request Details", expanded=False):
            st.code(f"Request ID: {request_id}", language="text")
    
    for item in content:
        if item["type"] == "text":
            st.markdown(f"<div class='dashboard-card'>", unsafe_allow_html=True)
            render_chat_bubble("analyst", item["text"])  # Already handles HTML
            st.markdown("</div>", unsafe_allow_html=True)
        elif item["type"] == "suggestions":
            st.markdown('<div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0;">', unsafe_allow_html=True)
            for suggestion_index, suggestion in enumerate(item["suggestions"]):
                button_key = f"suggestion_{message_index}_{suggestion_index}_{len(st.session_state.messages)}"
                if st.button(suggestion, key=button_key, help="Click to use this suggestion"):
                    st.session_state.active_suggestion = suggestion
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        elif item["type"] == "sql":
            sql = item["statement"]
            with st.expander("💾 SQL Query", expanded=st.session_state.get("auto_expand_sql", False)):
                st.code(sql, language="sql")
                if st.button("📋 Copy SQL", key=f"copy_sql_{message_index}"):
                    st.toast("SQL copied to clipboard!", icon="📋")
            try:
                with st.expander("📊 Results", expanded=True):
                    with st.spinner("⏳ Running query and processing results..."):
                        df = pd.read_sql(sql, st.session_state.CONN)
                        if df.empty:
                            st.info("Query returned no data.", icon="ℹ️")
                            return
                        df.to_csv("temp.csv", index=False)
                        tabs = st.tabs(["📄 Data Table", "📈 Visualization", "📝 Summary", "⚙️ Export"])
                        
                        with tabs[0]:
                            # Data table with enhanced options
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                st.dataframe(df, use_container_width=True)
                            with col2:
                                st.metric("Rows", f"{len(df):,}")
                            with col3:  
                                st.metric("Columns", f"{len(df.columns):,}")
                                
                        with tabs[1]:
                            if len(df.columns) >= 2:
                                st.markdown("### Data Visualization")
                                
                                col1, col2, col3 = st.columns([1, 1, 1])
                                
                                with col1:
                                    chart_type = st.selectbox(
                                        "Chart Type", 
                                        ["Bar Chart 📊", "Line Chart 📈", "Scatter Plot 📍", "Area Chart 🏔️", "Pie Chart 🥧"],
                                        key=f"chart_type_{message_index}"
                                    )
                                
                                with col2:
                                    x_options = [col for col in df.columns]
                                    x_col = st.selectbox("X-axis", x_options, key=f"x_{message_index}")
                                
                                with col3:
                                    y_options = [col for col in df.columns if col != x_col and pd.api.types.is_numeric_dtype(df[col])]
                                    if y_options:
                                        y_col = st.selectbox("Y-axis", y_options, key=f"y_{message_index}")
                                    else:
                                        st.warning("No numeric columns available for Y-axis. Please select a different X-axis or check your data.")
                                        y_col = None
                                
                                if y_col and x_col:
                                    # Additional chart options
                                    show_advanced = st.checkbox("Show Advanced Options", key=f"advanced_{message_index}")
                                    
                                    color_by = "None"
                                    sort_by = "None"
                                    if show_advanced:
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            color_by = st.selectbox(
                                                "Color by", 
                                                ["None"] + [col for col in df.columns if col != x_col and col != y_col],
                                                key=f"color_{message_index}"
                                            )
                                        
                                        with col2:
                                            if chart_type != "Pie Chart 🥧":
                                                sort_by = st.selectbox(
                                                    "Sort by", 
                                                    ["None", "X Ascending", "X Descending", "Y Ascending", "Y Descending"],
                                                    key=f"sort_{message_index}"
                                                )
                                    
                                    # Validate data before charting
                                    if df[x_col].isnull().all() or df[y_col].isnull().all():
                                        st.error("Selected columns contain only null values. Please choose different columns.")
                                        return
                                    
                                    # Prepare data
                                    chart_df = df.copy()
                                    
                                    # Sort if specified
                                    try:
                                        if sort_by != "None" and chart_type != "Pie Chart 🥧":
                                            if sort_by == "X Ascending":
                                                chart_df = chart_df.sort_values(by=x_col)
                                            elif sort_by == "X Descending":
                                                chart_df = chart_df.sort_values(by=x_col, ascending=False)
                                            elif sort_by == "Y Ascending":
                                                chart_df = chart_df.sort_values(by=y_col)
                                            elif sort_by == "Y Descending":
                                                chart_df = chart_df.sort_values(by=y_col, ascending=False)
                                        
                                        # Create the chart
                                        chart = None
                                        if chart_type == "Bar Chart 📊":
                                            chart = alt.Chart(chart_df).mark_bar().encode(
                                                x=alt.X(x_col, type="nominal" if not pd.api.types.is_numeric_dtype(df[x_col]) else "quantitative"),
                                                y=alt.Y(y_col, type="quantitative"),
                                                color=color_by if color_by != "None" else alt.value(ACCENT_COLOR),
                                                tooltip=[x_col, y_col] + ([color_by] if color_by != "None" else [])
                                            ).interactive()
                                        
                                        elif chart_type == "Line Chart 📈":
                                            chart = alt.Chart(chart_df).mark_line().encode(
                                                x=alt.X(x_col, type="temporal" if pd.api.types.is_datetime64_dtype(df[x_col]) else "quantitative"),
                                                y=alt.Y(y_col, type="quantitative"),
                                                color=color_by if color_by != "None" else alt.value(ACCENT_COLOR),
                                                tooltip=[x_col, y_col] + ([color_by] if color_by != "None" else [])
                                            ).interactive()
                                        
                                        elif chart_type == "Scatter Plot 📍":
                                            chart = alt.Chart(chart_df).mark_circle(size=60).encode(
                                                x=alt.X(x_col, type="quantitative"),
                                                y=alt.Y(y_col, type="quantitative"),
                                                color=color_by if color_by != "None" else alt.value(ACCENT_COLOR),
                                                tooltip=[x_col, y_col] + ([color_by] if color_by != "None" else [])
                                            ).interactive()
                                        
                                        elif chart_type == "Area Chart 🏔️":
                                            chart = alt.Chart(chart_df).mark_area(opacity=0.7).encode(
                                                x=alt.X(x_col, type="temporal" if pd.api.types.is_datetime64_dtype(df[x_col]) else "quantitative"),
                                                y=alt.Y(y_col, type="quantitative"),
                                                color=color_by if color_by != "None" else alt.value(ACCENT_COLOR),
                                                tooltip=[x_col, y_col] + ([color_by] if color_by != "None" else [])
                                            ).interactive()
                                        
                                        elif chart_type == "Pie Chart 🥧":
                                            pie_data = df.groupby(x_col)[y_col].sum().reset_index()
                                            chart = alt.Chart(pie_data).mark_arc().encode(
                                                theta=alt.Theta(field=y_col, type="quantitative"),
                                                color=alt.Color(field=x_col, type="nominal"),
                                                tooltip=[x_col, y_col]
                                            ).properties(
                                                width=400,
                                                height=400
                                            )
                                        
                                        if chart:
                                            st.altair_chart(chart, use_container_width=True)
                                        
                                    except Exception as chart_err:
                                        st.error(f"Failed to generate chart: {str(chart_err)}")
                                        st.markdown("""
                                        ### Chart Troubleshooting:
                                        - Ensure selected columns have valid data types
                                        - Check for missing or null values
                                        - Try a different chart type or column combination
                                        """)
                                else:
                                    st.warning("Need at least 2 valid columns to create a visualization.")
                        
                        with tabs[2]:
                            st.markdown("### Data Analysis Summary")
                            with st.spinner("Generating summary..."):
                                summary = get_llm_summary(prompt or "Analyze this data", df)
                                st.markdown(summary)
                        
                        with tabs[3]:
                            st.subheader("Export Options")
                            
                            export_col1, export_col2 = st.columns(2)
                            
                            with export_col1:
                                # Create export buttons
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label="Download CSV",
                                    data=csv,
                                    file_name=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv",
                                )
                            
                            with export_col2:
                                buffer = BytesIO()
                                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                                    df.to_excel(writer, sheet_name="Data", index=False)
                                excel_data = buffer.getvalue()
                                
                                st.download_button(
                                    label="Download Excel",
                                    data=excel_data,
                                    file_name=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                    mime="application/vnd.ms-excel",
                                )
                            
                            # Additional information - not inside an expander
                            st.subheader("Additional Information")
                            st.write("Need help with this data? Check the summary tab for insights.")
                            
                            # Troubleshooting help - not inside an expander
                            st.subheader("Troubleshooting Tips")
                            st.markdown("""
                            - If charts aren't rendering correctly, try a different chart type
                            - For large datasets, consider filtering or aggregating the data
                            - Check column types if visualization options are limited
                            """)
            except Exception as e:
                st.error(f"Error processing query results: {str(e)}")
                st.code(str(e), language="text")
                st.subheader("Troubleshooting Help")
                st.markdown("""
                ### Common Issues:
                - Check that all table references are valid
                - Verify column names and data types
                - Ensure your warehouse has access to the requested data
                - Check for syntax errors in the SQL query
                """)

def render_typing_indicator():
    return """
    <style>
    @keyframes blink {
        0% { opacity: 0.2; }
        20% { opacity: 1; }
        100% { opacity: 0.2; }
    }
    .typing-indicator span {
        background-color: #888;
        border-radius: 50%;
        width: 8px;
        height: 8px;
        margin: 0 3px;
        display: inline-block;
        animation: blink 1.4s infinite both;
    }
    .typing-indicator span:nth-child(2) {
        animation-delay: 0.2s;
    }
    .typing-indicator span:nth-child(3) {
        animation-delay: 0.4s;
    }
    </style>
    <div class="slide-in" style="display: flex; flex-direction: row; margin: 10px 0; align-items: flex-start; gap: 10px;">
        <div style="width: 36px; height: 36px; border-radius: 50%; background-color: #D2E0FB;"></div>
        <div class="typing-indicator" style="background-color: #D2E0FB; border-radius: 18px; padding: 15px;">
            <span></span><span></span><span></span>
        </div>
    </div>
    """
# Insert this anywhere in your new_UI_Vn.py file where you want the multimodel retriever to appear
# Recommended: place under a tab like "Multimodel Retriever"

def show_multimodel_interface(user_prompt):
    if not user_prompt:    # covers None or empty string
        return

    openai_api_key       = os.getenv("OPENAI_API_KEY")
    azure_search_service = os.getenv("AZURE_SEARCH_SERVICE")
    azure_search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
    claude_api_key       = os.getenv("CLAUDE_API_KEY")
    xai_api_key          = os.getenv("XAI_API_KEY")
    gemini_api_key       = os.getenv("GEMINI_API_KEY")

    # Index and embedding config
    INDEX_NAME = "file-index"
    VECTOR_FIELD = "content_vector"
    CONTENT_FIELD = "content"

    # Vector store
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_api_key)
    vector_store = AzureSearchStore(
        azure_search_endpoint=azure_search_service,
        azure_search_key=azure_search_api_key,
        index_name=INDEX_NAME,
        embedding_function=embeddings.embed_query,
        content_field=CONTENT_FIELD,
        vector_field=VECTOR_FIELD,
    )

    llms = {
        "ChatGPT": ChatOpenAI(model="o3-mini", openai_api_key=openai_api_key),
        "Claude": ChatAnthropic(model="claude-3-5-sonnet-20240620", anthropic_api_key=claude_api_key),
        "Gemini": ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=gemini_api_key),
        "Grok": ChatXAI(model="grok-3-latest", xai_api_key=xai_api_key),
    }

    # UI Header
    # st.title("🔍 Multi-Model AI Retriever with Source References")
    # st.caption("Ask a question and see how each model responds.")

    # Input
    # query = st.text_input("💬 Ask your question:", "e.g. What is our SharePoint AI roadmap?")
    # run_query = st.button("Run", type="primary")

    if  user_prompt.strip():
        retriever = vector_store.as_retriever(search_type="similarity", k=4)
        results_by_model = {}

        for model_name, llm in llms.items():
            with st.spinner(f"{model_name} is thinking..."):
                start = time.time()
                qa_chain = RetrievalQA.from_chain_type(
                    llm=llm,
                    retriever=retriever,
                    return_source_documents=True
                )
                result = qa_chain.invoke({"query": user_prompt})
                end = time.time()

                answer = result['result']
                sources = result["source_documents"]
                duration = round(end - start, 2)
                display_sources = [
                    f"{doc.metadata.get('filename')} (chunk {doc.metadata.get('chunk_index')}, page {doc.metadata.get('source_page')})"
                    for doc in sources
                ]

                # Fancy display with chat bubbles
                st.markdown(f"#### 🤖 {model_name}")
                render_chat_bubble("analyst", answer, timestamp=f"{duration}s")
                st.markdown("**📁 Please refer to the following sources for further information:**")
                for src in display_sources:
                    st.markdown(f"→ {src}")

                results_by_model[model_name] = {
                    "answer": answer,
                    "time": duration,
                    "sources": display_sources
                }

                # Save to session history
                st.session_state.messages.append({
                    "role": "analyst",
                    "content": [{"type": "text", "text": answer}],
                    "timestamp": datetime.now().isoformat(),
                    "model": model_name
                })

        # Optional CSV logging
        try:
            csv_path = "multimodel_answers_log.csv"
            if not os.path.exists(csv_path):
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Question"] + [item for model in llms for item in [f"{model} Answer", f"{model} Time", f"{model} Sources"]])
            with open(csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                row = [user_prompt] + [
                    val for model in llms for val in [
                        results_by_model[model]['answer'],
                        results_by_model[model]['time'],
                        "; ".join(results_by_model[model]['sources'])
                    ]
                ]
                writer.writerow(row)
        except Exception as e:
            st.warning(f"Failed to write to CSV: {e}")


def process_message(prompt: str):
    # Add user message to history and display
    st.session_state.messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})
    render_chat_bubble("user", prompt)
    
    # Show typing indicator
    
    typing_placeholder = st.empty()
    typing_placeholder.markdown(render_typing_indicator(), unsafe_allow_html=True)
    
    try:
            st.session_state.typing = True
            response = send_message(prompt=prompt)
            request_id = response.get("request_id")
            
            # Check if expected keys are present
            if "message" in response and "content" in response["message"]:
                content = response["message"]["content"]
            else:
                st.error(f"Unexpected API response format. Response: {response}")
                return  # Exit the function to prevent further processing
            
            # Process response content
            for item in content:
                if item["type"] == "text":
                    message_text = item["text"].strip()

                    # If the text looks like CSS or random HTML, skip it
                    suspicious_patterns = [
                        "background-color:", 
                        "border-radius:", 
                        "<style", 
                        "<script", 
                        "padding:", 
                        "font-size:", 
                        "{", 
                        "}"
                    ]

                    if any(pat in message_text.lower() for pat in suspicious_patterns):
                        print(f"[SKIPPED STYLING TEXT] 🔍 {message_text}")
                        continue  # Skip rendering this one

                    render_chat_bubble("analyst", message_text)
                elif item["type"] == "suggestions":
                    st.markdown('<div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 20px 46px;">', 
                            unsafe_allow_html=True)
                    
                    for idx, suggestion in enumerate(item["suggestions"]):
                        # Generate a truly unique key for each button
                        import hashlib
                        button_key = f"suggestion_{len(st.session_state.messages)}_{idx}_{time.time()}"
                        
                        # Store the suggestion in session state instead of immediate rerun
                        if st.button(suggestion, key=button_key):
                            st.session_state.pending_suggestion = suggestion  # Store the suggestion to process later
                            break  # Exit the loop to avoid multiple suggestions being processed
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                elif item["type"] == "sql":
                    display_content([item], request_id=request_id, prompt=prompt)
            
            # Save response to history
            st.session_state.messages.append({
                "role": "analyst", 
                "content": content, 
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            })
        
    finally:
        # Ensure typing indicator is always removed, even if an error occurs
        typing_placeholder.empty()
        st.session_state.typing = False
        # Save response to history

# Container for chat history
chat_container = st.container()

# Show chat history with better spacing and styling
with chat_container:
    for message_index, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            # For user messages, we just need the text content
            for item in message["content"]:
                if item["type"] == "text":
                    render_chat_bubble(message["role"], item["text"])
        else:
            # For analyst messages, process each content item
            for item in message["content"]:
                if item["type"] == "text":
                    render_chat_bubble(message["role"], item["text"])
                elif  item["type"] == "sql":
                    display_content([item], request_id=message.get("request_id"), message_index=message_index)

# Initial onboarding

    # process_message("What questions can I ask?")

# Chat input - moved to bottom for better UX
user_input = st.chat_input("Ask a question about your data...", key="chat_input")

if user_input:
    if st.session_state.chat_mode == "Structured Data Search":
        process_message(user_input)
    # else:  # must be Unstructured Chat
    #     render_chat_bubble("user", user_input)
    #     st.session_state.messages.append({
    #         "role": "user",
    #         "content": [{"type": "text", "text": user_input}],
    #         "timestamp": datetime.now().isoformat()
    #     })
    #     show_multimodel_interface(user_input)
    #     st.rerun()


# Process suggestion if clicked
if st.session_state.active_suggestion:
    process_message(st.session_state.active_suggestion)
    st.session_state.active_suggestion = None

# Keyboard shortcuts help - shown in a discreet footer
st.markdown("""
<div style="position: fixed; bottom: 0; left: 0; width: 100%; background-color: rgba(245, 247, 248, 0.8); 
padding: 5px 20px; font-size: 0.8em; text-align: center; border-top: 1px solid #eee;">
    Press <kbd>Enter</kbd> to send message • <kbd>Ctrl+L</kbd> to clear input • <kbd>Ctrl+K</kbd> to focus search
</div>
""", unsafe_allow_html=True)

# Handle resize for mobile responsiveness
st.markdown("""
<script>
function handleResize() {
    // Add responsive adjustments if needed
}
window.addEventListener('resize', handleResize);
handleResize();
</script>
""", unsafe_allow_html=True)
