# Trigger deploy: 2024-03-26
import streamlit as st
import opik
import os
from streamlit_mic_recorder import mic_recorder
import io
from openai import OpenAI
import yaml
import streamlit_authenticator as stauth
from database import save_chat, get_user_chats, save_tournament_result, get_user_tournament_results, get_user_stats, get_user_by_username

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

# Load authentication config
with open('config.yaml') as file:
    config = yaml.load(file, Loader=yaml.SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    auto_hash=False
)

# Initialize session state for authentication if not already done
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

# Initialize login
try:
    authenticator.login(location='main')
    
    if st.session_state['authentication_status']:
        authenticator.logout('Logout', location='sidebar')
        st.sidebar.title(f'Welcome {st.session_state["username"]}')
        
        # Display user stats in sidebar if available
        user_stats = get_user_stats(st.session_state["username"])
        if user_stats:
            st.sidebar.subheader("Your Tournament Stats")
            st.sidebar.metric("Total Tournaments", user_stats["total_tournaments"])
            st.sidebar.metric("ROI", f"{user_stats['roi']:.1f}%")
            st.sidebar.metric("ITM %", f"{user_stats['itm_percentage']:.1f}%")
            st.sidebar.metric("Total Profit", f"${user_stats['total_profit']:,.2f}")
    elif st.session_state['authentication_status'] == False:
        st.error('Username/password is incorrect')
    elif st.session_state['authentication_status'] == None:
        st.warning('Please enter your username and password')

    # Only show the rest of the UI if authenticated
    if st.session_state['authentication_status']:
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
                    # Get user's tournament history for context
                    user_tournaments = get_user_tournament_results(st.session_state.user_uuid)
                    tournament_context = ""
                    if user_tournaments:
                        total_tournaments = len(user_tournaments)
                        recent_results = user_tournaments[:3]  # Last 3 tournaments
                        tournament_context = f"Context: The user has played {total_tournaments} tracked tournaments. "
                        tournament_context += "Recent results: " + ", ".join([
                            f"${t['prize_won']} won (${t['total_investment']} invested)" for t in recent_results
                        ])
                    
                    # Get relevant chat history
                    past_chats = get_user_chats(st.session_state.user_uuid)
                    chat_context = ""
                    if past_chats:
                        # Filter chats by current mode
                        mode_chats = [chat for chat in past_chats if chat['mode'] == st.session_state.coaching_mode]
                        if mode_chats:
                            # Get the last 3 relevant conversations
                            recent_chats = mode_chats[:3]
                            chat_context = "\n\nPrevious relevant conversations:\n"
                            for chat in recent_chats:
                                # Extract key exchanges from each chat
                                messages = chat['messages']
                                # Skip system message and get user-assistant pairs
                                for i in range(1, len(messages)-1, 2):
                                    chat_context += f"User: {messages[i]['content']}\n"
                                    chat_context += f"Coach: {messages[i+1]['content']}\n"
                
                    system_prompt = GENERAL_COACHING_PROMPT if st.session_state.coaching_mode == "General Coaching Chat" else TOURNAMENT_STRATEGY_PROMPT
                    
                    # Add context to system prompt
                    if tournament_context:
                        system_prompt += f"\n\n{tournament_context}"
                    if chat_context:
                        system_prompt += f"\n{chat_context}\n\nUse the above conversation history to maintain consistency in your advice and build upon previous discussions. If you see patterns in the user's questions or areas they frequently ask about, address those topics more thoroughly."
                    
                    st.session_state.chat = [{
                        "role": "system",
                        "content": system_prompt
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
                
                # Save chat to database
                save_chat(
                    st.session_state.user_uuid,
                    st.session_state.coaching_mode,
                    st.session_state.chat
                )
                
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
        try:
            mode = st.radio(
                "Select Coaching Mode:",
                ["General Coaching Chat", "Tournament Strategy", "Enter Tournament Result"],
                key="coaching_mode",
                on_change=on_mode_change
            )

            if mode == "Enter Tournament Result":
                with st.form("tournament_result"):
                    st.subheader("Enter Tournament Result")
                    try:
                        venue = st.text_input("Venue (Casino/Online Site)")
                        format_type = st.selectbox("Format", ["Live", "Online"])
                        buy_in = st.number_input("Buy-in ($)", min_value=0.0, step=1.0)
                        rebuys = st.number_input("Number of Rebuys", min_value=0, step=1)
                        add_ons = st.number_input("Number of Add-ons", min_value=0, step=1)
                        total_entries = st.number_input("Total Entries", min_value=1, step=1)
                        position = st.number_input("Position Finished", min_value=1, step=1)
                        prize = st.number_input("Prize Won ($)", min_value=0.0, step=1.0)
                        duration = st.number_input("Duration (hours)", min_value=0.0, step=0.5)
                        notes = st.text_area("Tournament Notes")
                        
                        submitted = st.form_submit_button("Save Result")
                        if submitted:
                            if not venue:
                                st.error("Please enter a venue name")
                            else:
                                total_investment = buy_in * (1 + rebuys) + (add_ons * buy_in)
                                tournament_data = {
                                    "venue": venue,
                                    "format": format_type,
                                    "buy_in": buy_in,
                                    "rebuys": rebuys,
                                    "add_ons": add_ons,
                                    "total_investment": total_investment,
                                    "total_entries": total_entries,
                                    "position_finished": position,
                                    "prize_won": prize,
                                    "duration_hours": duration,
                                    "notes": notes
                                }
                                try:
                                    save_tournament_result(st.session_state.user_uuid, tournament_data)
                                    st.success("Tournament result saved successfully!")
                                    st.experimental_rerun()  # Rerun to update stats
                                except Exception as e:
                                    st.error(f"Error saving tournament result: {str(e)}")
                    except Exception as e:
                        st.error(f"Error displaying tournament form: {str(e)}")
            else:
                # Display mode-specific instructions
                if mode == "Tournament Strategy":
                    st.info("I'll help you develop a personalized tournament strategy. Tell me about your tournament experience, preferred formats, and goals!")

                # Input section with text and voice options
                try:
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
                except Exception as e:
                    st.error(f"Error in chat interface: {str(e)}")

        except Exception as e:
            st.error(f"Application error: {str(e)}")
            st.error("Please refresh the page or contact support if the error persists.")

        # Show chat history
        for message in st.session_state.chat[1:]:  # Skip system prompt
            if message["role"] == "user":
                st.markdown(f'<div class="user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
            elif message["role"] == "assistant":
                st.markdown(f'<div class="coach-message"><strong>Poker Coach:</strong> {message["content"]}</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Application error: {str(e)}")
    st.error("Please refresh the page or contact support if the error persists.") 