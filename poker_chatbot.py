# Trigger deploy: 2024-03-26
import streamlit as st
import opik
import os
from streamlit_mic_recorder import mic_recorder
import io
from openai import OpenAI

# Use API keys from secrets
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["OPIK_API_KEY"] = st.secrets["OPIK_API_KEY"]
os.environ["OPIK_WORKSPACE"] = "statisticianinstilettos" 
os.environ["OPIK_PROJECT_NAME"] = "My-Poker-Coach" 

opik.configure(use_local=False)

from opik import track, opik_context
from opik.integrations.openai import track_openai

client = OpenAI() #Set up OpenAI
openai_client = track_openai(client) #set up the Opik tracer

# Initialize OpenAI client for Whisper
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI()

# Page configuration
st.set_page_config(page_title="♠️ Poker Coach GPT", page_icon="♠️", layout="centered")

# Custom CSS for dark theme, button glow, and text color styling
st.markdown("""
    <style>
        body {
            background-color: #121212;
            color: #E0E0E0;
        }
        .stButton > button {
            background-color: #1e1e1e;
            border: 1px solid #333;
            box-shadow: 0 0 10px #007BFF;
            color: #FFA500;
        }
        .stChatInput input {
            background-color: #1e1e1e;
            color: #87CEEB;
        }
        h1 {
            color: #FFA500;
        }
        .user-message {
            color: #87CEEB;
            background-color: #1e1e1e;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        .coach-message {
            color: #FFA500;
            background-color: #262626;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("♠️ AI Poker Coach")
st.markdown("Get strategy advice, hand reviews, and tournament tips from your expert AI coach.")

# Initialize session state variables
if "chat" not in st.session_state:
    st.session_state.chat = []

if "last_processed_input" not in st.session_state:
    st.session_state.last_processed_input = ""

# Function to handle mode change
def on_mode_change():
    st.session_state.chat = []
    st.session_state.last_processed_input = ""

# Function to handle message submission
def process_message():
    if st.session_state.user_message and st.session_state.user_message != st.session_state.last_processed_input:
        user_input = st.session_state.user_message
        st.session_state.last_processed_input = user_input
        
        # Initialize chat if empty
        if len(st.session_state.chat) == 0:
            st.session_state.chat = [{
                "role": "system",
                "content": GENERAL_COACHING_PROMPT if st.session_state.coaching_mode == "General Coaching Chat" else TOURNAMENT_STRATEGY_PROMPT
            }]
        
        # Add user message and get response
        st.session_state.chat.append({"role": "user", "content": user_input})
        
        # Call OpenAI
        response = client.chat.completions.create(
            model="o3-mini",
            reasoning_effort="medium",
            messages=st.session_state.chat
        )
        
        reply = response.choices[0].message.content
        st.session_state.chat.append({"role": "assistant", "content": reply})
        
        # Clear the input field
        st.session_state.user_message = ""

# System prompts for different modes
GENERAL_COACHING_PROMPT = """You are Poker Coach GPT — a sharp, friendly, and brutally effective AI coach for No-Limit Texas Hold'em.

You blend GTO precision with street-smart exploitative plays, adapting your advice to the player's skill level, style, and game type (live or online, cash or tournament). You explain why moves work using clear, fast math and straight talk — not fluff.

Coaching Style:
    •   Fun, fast, friendly. Speak like a seasoned pro who actually wants to help.
    •   Concise, direct, and confident. Don't hedge—give opinions.
    •   Explain hands with equity estimates, range logic, and core math (EV, odds, blockers).
    •   Use structured, scannable responses: bullets, formulas, quick math summaries.

What You Do:
    •   Recommend preflop and postflop plays with reasoning.
    •   Analyze hands across all streets.
    •   Calculate equity, EV, outs, pot odds, implied odds.
    •   Adjust between GTO and exploit based on opponent reads or leaks.
    •   Provide tailored advice for cash games or tournaments.
    •   Suggest sharp, simple improvements for the user's game.

If you don't know something precisely, approximate it. Always reason it out — use simple formulas and poker logic. Avoid rambling. Just teach, coach, and get the user better — one solid hand at a time."""

TOURNAMENT_STRATEGY_PROMPT = """You are an expert Tournament Poker Coach GPT, specializing in crafting personalized tournament strategies. Your expertise covers all aspects of tournament play, from early stage to final table dynamics.

Initial Assessment:
    •   Ask about their typical buy-in range and tournament types (live/online)
    •   Inquire about their current ROI and in-the-money percentage
    •   Understand their playing style and perceived strengths/weaknesses

Strategy Customization:
    •   Provide stack-size specific advice (big stack, medium, short stack play)
    •   Adjust strategies for different tournament stages
    •   ICM-aware recommendations for crucial decisions
    •   Bubble play and final table adjustments
    •   Specific advice for their preferred tournament types

Mathematical Approach:
    •   Calculate ICM implications for key decisions
    •   Provide clear push/fold ranges based on stack sizes
    •   Explain risk/reward ratios for tournament-specific spots
    •   Break down prize pool structures and their strategic implications

Your responses should be:
    •   Highly personalized to their specific tournament type and level
    •   Mathematical when needed, but always practical
    •   Focused on maximizing ROI and reducing variance
    •   Clear about adjustments needed as tournaments progress

Start by gathering key information about their tournament experience and goals, then provide targeted, actionable advice."""

# Mode selection
mode = st.radio(
    "Select Coaching Mode:",
    ["General Coaching Chat", "Get Personalized Tournament Strategy"],
    key="coaching_mode",
    on_change=on_mode_change
)

# Display mode-specific instructions
if mode == "Get PersonalizedTournament Strategy":
    st.info("I'll help you develop a personalized tournament strategy. Tell me about your tournament experience, preferred formats, and goals!")

# Input section with text and voice options
col1, col2 = st.columns([4, 1])
with col1:
    st.text_input(
        "Type or use voice input →",
        key="user_message",
        on_change=process_message
    )

with col2:
    st.markdown("""
        <style>
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Simple audio recording implementation
    audio = mic_recorder(
        start_prompt="🎤 Click to Start",
        stop_prompt="⏹️ Click to Stop",
        key="recorder"
    )

    if audio and isinstance(audio, dict) and 'bytes' in audio:
        with st.spinner("Transcribing..."):
            try:
                # Create audio file object for Whisper
                audio_file = io.BytesIO(audio['bytes'])
                audio_file.name = "audio.webm"
                
                # Transcribe with Whisper
                transcript = st.session_state.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                st.session_state.user_message = transcript.text
                process_message()
            except Exception as e:
                st.error(f"Error transcribing audio: {str(e)}")

# Show chat history
for message in st.session_state.chat[1:]:  # Skip system prompt
    if message["role"] == "user":
        st.markdown(f'<div class="user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
    elif message["role"] == "assistant":
        st.markdown(f'<div class="coach-message"><strong>Poker Coach:</strong> {message["content"]}</div>', unsafe_allow_html=True) 