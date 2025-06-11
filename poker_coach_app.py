"""
Poker Coach GPT - Main Application
A clean, modular poker coaching application with tournament analysis capabilities.
"""

import streamlit as st
import io
from streamlit_mic_recorder import mic_recorder

# Import our custom modules
from src.config import PAGE_TITLE, PAGE_ICON, DARK_THEME_CSS
from src.auth.authentication import handle_authentication, get_current_username
from src.ui.sidebar import setup_sidebar
from src.ai.coaching import setup_openai, initialize_chat_session, process_chat_message
from src.forms.tournament_forms import (
    create_tournament_entry_form, 
    create_tournament_edit_form, 
    create_tournament_analysis_form
)
from src.ui.tournament_display import display_tournament_results
from database import get_user_tournament_results


def initialize_session_state():
    """Initialize application session state variables."""
    if "chat" not in st.session_state:
        st.session_state.chat = []
    if "last_processed_input" not in st.session_state:
        st.session_state.last_processed_input = ""


def handle_mode_change():
    """Handle coaching mode changes by clearing chat."""
    st.session_state.chat = []
    st.session_state.last_processed_input = ""


def process_text_message():
    """Process text input message."""
    if st.session_state.user_message and st.session_state.user_message != st.session_state.last_processed_input:
        user_input = st.session_state.user_message
        st.session_state.last_processed_input = user_input
        
        username = get_current_username()
        coaching_mode = st.session_state.coaching_mode
        
        # Initialize chat if empty
        if len(st.session_state.chat) == 0:
            user_tournaments = get_user_tournament_results(username)
            st.session_state.chat = initialize_chat_session(username, coaching_mode, user_tournaments)
        
        # Add user message and get response
        st.session_state.chat.append({"role": "user", "content": user_input})
        
        # Get AI response
        client, _ = setup_openai()
        reply = process_chat_message(client, st.session_state.chat, username, coaching_mode)
        
        if reply:
            st.session_state.chat.append({"role": "assistant", "content": reply})
        
        # Clear the input field
        st.session_state.user_message = ""


def process_voice_input(transcript_text):
    """Process voice input message."""
    if transcript_text and transcript_text != st.session_state.last_processed_input:
        user_input = transcript_text
        st.session_state.last_processed_input = user_input
        
        username = get_current_username()
        coaching_mode = st.session_state.coaching_mode
        
        # Initialize chat if empty
        if len(st.session_state.chat) == 0:
            user_tournaments = get_user_tournament_results(username)
            st.session_state.chat = initialize_chat_session(username, coaching_mode, user_tournaments)
        
        # Add user message and get response
        st.session_state.chat.append({"role": "user", "content": user_input})
        
        # Get AI response
        client, _ = setup_openai()
        reply = process_chat_message(client, st.session_state.chat, username, coaching_mode)
        
        if reply:
            st.session_state.chat.append({"role": "assistant", "content": reply})
        
        # Trigger rerun to show new conversation
        st.rerun()


def render_chat_interface():
    """Render the chat interface with text and voice input."""
    # Text input
    st.text_input(
        "Type your message below or use voice input:",
        key="user_message",
        on_change=process_text_message
    )
    
    # Voice input button (centered)
    col_left, col_center, col_right = st.columns([1, 1, 1])
    with col_center:
        audio = mic_recorder(
            start_prompt="🎤 Click to Chat",
            stop_prompt="⏹️",
            key="recorder"
        )

    # Process voice input
    if audio and isinstance(audio, dict) and 'bytes' in audio:
        with st.spinner("Transcribing..."):
            try:
                # Create audio file for Whisper
                audio_file = io.BytesIO(audio['bytes'])
                audio_file.name = "audio.webm"
                
                # Transcribe with Whisper
                transcript = st.session_state.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                
                process_voice_input(transcript.text)
                
            except Exception as e:
                st.error(f"Error transcribing audio: {str(e)}")


def render_chat_history():
    """Render chat message history."""
    for message in st.session_state.chat[1:]:  # Skip system prompt
        if message["role"] == "user":
            st.markdown(f'<div class="user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        elif message["role"] == "assistant":
            st.markdown(f'<div class="coach-message"><strong>Poker Coach:</strong> {message["content"]}</div>', unsafe_allow_html=True)


def main():
    """Main application function."""
    # Page configuration
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")
    
    # Handle authentication
    if not handle_authentication():
        return
    
    # Apply custom CSS
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Setup sidebar
    username = get_current_username()
    setup_sidebar(username)
    
    # Header
    st.title("♠️ AI Poker Coach")
    st.markdown("Get strategy advice, hand reviews, and tournament tips from your expert AI coach.")
    
    # Mode selection
    mode = st.radio(
        "Select Coaching Mode:",
        [
            "General Coaching Chat", 
            "Personalized Tournament Strategy Analysis", 
            "Enter Tournament Result", 
            "View Tournament Results"
        ],
        key="coaching_mode",
        on_change=handle_mode_change
    )
    
    # Handle different modes
    if mode == "Enter Tournament Result":
        create_tournament_entry_form()
    
    elif mode == "View Tournament Results":
        # Check for edit mode
        if 'edit_tournament_id' in st.session_state:
            tournament_id = st.session_state.edit_tournament_id
            create_tournament_edit_form(tournament_id, username)
        else:
            display_tournament_results(username)
    
    elif mode == "Personalized Tournament Strategy Analysis":
        st.subheader("🎯 Tournament Strategy Analysis")
        st.info("Fill out the details of the tournament you're considering, and I'll analyze your historical data to provide personalized recommendations.")
        
        # Tournament analysis form
        tournament_data = create_tournament_analysis_form()
        
        if tournament_data:
            # Process tournament analysis
            from src.analysis.tournament_analysis import process_tournament_analysis
            process_tournament_analysis(tournament_data, username)
    
    else:  # General Coaching Chat
        # Display mode-specific instructions
        if mode == "Personalized Tournament Strategy Analysis":
            st.info("I'll analyze your tournament history data to recommend optimal tournament selection and strategies for maximizing your ROI. Let me review your past results and provide data-driven recommendations!")
        
        # Chat interface
        render_chat_interface()
        
        # Show chat history
        render_chat_history()


if __name__ == "__main__":
    main() 