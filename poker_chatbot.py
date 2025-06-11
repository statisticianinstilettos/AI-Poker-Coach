# Trigger deploy: 2024-03-26
import streamlit as st
import opik
import os
from streamlit_mic_recorder import mic_recorder
import io
from openai import OpenAI
import yaml
import streamlit_authenticator as stauth
from database import save_chat, get_user_chats, save_tournament_result, get_user_tournament_results, get_user_stats, get_user_by_username, delete_user_tournament_results, delete_single_tournament_result, update_tournament_result, get_single_tournament_result
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

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

def create_player_pdf_plot(tournament_results, username):
    """
    Create a matplotlib plot of the user's personalized probability distribution
    """
    if not tournament_results or len(tournament_results) < 3:
        return None, None
    
    try:
        # Import the player_pdf function
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'player_model'))
        from player import player_pdf
        
        # Use a standard field size for visualization (100 players)
        field_size = 100
        
        # Get personalized distribution
        probabilities, metadata = player_pdf(tournament_results, field_size)
        
        # Create the plot
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # Create positions as percentiles for better readability
        positions = np.arange(1, field_size + 1)
        percentiles = positions / field_size * 100
        
        # Plot the distribution
        ax.plot(percentiles, probabilities * 100, color='#FFA500', linewidth=2, alpha=0.8)
        ax.fill_between(percentiles, probabilities * 100, alpha=0.3, color='#FFA500')
        
        # Customize the plot
        ax.set_xlabel('Finish Percentile (%)', color='white', fontsize=10)
        ax.set_ylabel('Probability (%)', color='white', fontsize=10)
        ax.set_title(f'{username}\'s Performance Distribution\n({metadata["sample_size"]} tournaments)', 
                    color='#FFA500', fontsize=12, fontweight='bold')
        
        # Add grid
        ax.grid(True, alpha=0.3, color='white')
        
        # Set background color
        fig.patch.set_facecolor('#0E1117')
        ax.set_facecolor('#0E1117')
        
        # Color the axes
        ax.tick_params(colors='white', labelsize=8)
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Add expected finish line
        expected_percentile = metadata['expected_finish_position'] / field_size * 100
        ax.axvline(expected_percentile, color='#87CEEB', linestyle='--', alpha=0.8, linewidth=1)
        ax.text(expected_percentile + 2, max(probabilities * 100) * 0.8, 
               f'Expected: {expected_percentile:.0f}%', 
               color='#87CEEB', fontsize=8, rotation=90)
        
        # Tight layout
        plt.tight_layout()
        
        return fig, metadata
        
    except Exception as e:
        st.error(f"Error creating PDF plot: {str(e)}")
        return None, None

# Page configuration
st.set_page_config(page_title="♠️ Poker Coach GPT", page_icon="♠️", layout="centered")

# Authentication configuration using Streamlit secrets
config = {
    'cookie': {
        'expiry_days': 30,
        'key': st.secrets["cookie_key"],
        'name': 'poker_coach_cookie'
    },
    'credentials': {
        'usernames': st.secrets["credentials"]["usernames"]
    }
}

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
            
            # Create and display player PDF plot
            user_tournament_data = get_user_tournament_results(st.session_state["username"])
            if user_tournament_data and len(user_tournament_data) >= 3:
                fig, metadata = create_player_pdf_plot(user_tournament_data, st.session_state["username"])
                if fig and metadata:
                    st.sidebar.subheader("📊 Your Performance Distribution")
                    st.sidebar.pyplot(fig, use_container_width=True)
                    plt.close(fig)  # Clean up to prevent memory issues
                    
                    # Add small explanation
                    st.sidebar.caption(f"Based on {metadata['sample_size']} tournaments • {metadata['confidence_level'].title()} confidence")
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
                    user_tournaments = get_user_tournament_results(st.session_state["username"])
                    tournament_context = ""
                    
                    if user_tournaments:
                        # For Tournament Strategy Analysis mode, provide comprehensive data
                        if st.session_state.coaching_mode == "Personalized Tournament Strategy Analysis":
                            # Comprehensive tournament analysis for strategy mode
                            total_tournaments = len(user_tournaments)
                            total_profit = sum(t['prize_won'] - t['total_investment'] for t in user_tournaments)
                            total_investment = sum(t['total_investment'] for t in user_tournaments)
                            overall_roi = (total_profit / total_investment * 100) if total_investment > 0 else 0
                            itm_count = sum(1 for t in user_tournaments if t['prize_won'] > 0)
                            itm_rate = (itm_count / total_tournaments * 100) if total_tournaments > 0 else 0
                            
                            # Performance by format
                            live_tournaments = [t for t in user_tournaments if t.get('format') == 'Live']
                            online_tournaments = [t for t in user_tournaments if t.get('format') == 'Online']
                            
                            live_roi = 0
                            online_roi = 0
                            if live_tournaments:
                                live_profit = sum(t['prize_won'] - t['total_investment'] for t in live_tournaments)
                                live_investment = sum(t['total_investment'] for t in live_tournaments)
                                live_roi = (live_profit / live_investment * 100) if live_investment > 0 else 0
                            
                            if online_tournaments:
                                online_profit = sum(t['prize_won'] - t['total_investment'] for t in online_tournaments)
                                online_investment = sum(t['total_investment'] for t in online_tournaments)
                                online_roi = (online_profit / online_investment * 100) if online_investment > 0 else 0
                            
                            # Performance by buy-in ranges
                            low_buyin = [t for t in user_tournaments if t['buy_in'] <= 100]
                            mid_buyin = [t for t in user_tournaments if 100 < t['buy_in'] <= 500]
                            high_buyin = [t for t in user_tournaments if t['buy_in'] > 500]
                            
                            # Get last 10 tournaments and convert to clean JSON for analysis
                            import json
                            last_10_tournaments = user_tournaments[:10]
                            tournament_json_data = []
                            
                            for t in last_10_tournaments:
                                # Clean tournament data for JSON - remove MongoDB ObjectId and add calculated fields
                                clean_tournament = {
                                    "tournament_date": t.get('tournament_date'),
                                    "venue": t.get('venue'),
                                    "format": t.get('format'),
                                    "buy_in": t.get('buy_in'),
                                    "rebuys": t.get('rebuys', 0),
                                    "add_ons": t.get('add_ons', 0),
                                    "total_investment": t.get('total_investment'),
                                    "total_entries": t.get('total_entries'),
                                    "position_finished": t.get('position_finished'),
                                    "prize_won": t.get('prize_won'),
                                    "duration_hours": t.get('duration_hours', 0),
                                    "starting_stack": t.get('starting_stack'),
                                    "ante_structure": t.get('ante_structure'),
                                    "level_time_minutes": t.get('level_time_minutes'),
                                    "notes": t.get('notes', ''),
                                    "profit_loss": t.get('prize_won', 0) - t.get('total_investment', 0),
                                    "roi_percent": ((t.get('prize_won', 0) - t.get('total_investment', 0)) / t.get('total_investment', 1) * 100)
                                }
                                tournament_json_data.append(clean_tournament)
                            
                            tournament_context = f"""
USER TOURNAMENT PERFORMANCE DATA FOR ANALYSIS:

Overall Performance Summary:
- Total Tournaments: {total_tournaments}
- Overall ROI: {overall_roi:.1f}%
- ITM Rate: {itm_rate:.1f}%
- Total Profit/Loss: ${total_profit:,.0f}
- Total Investment: ${total_investment:,.0f}

Format Performance:
- Live Tournaments: {len(live_tournaments)} played, ROI: {live_roi:.1f}%
- Online Tournaments: {len(online_tournaments)} played, ROI: {online_roi:.1f}%

Buy-in Distribution:
- Low Stakes ($1-$100): {len(low_buyin)} tournaments
- Mid Stakes ($101-$500): {len(mid_buyin)} tournaments  
- High Stakes ($500+): {len(high_buyin)} tournaments

TOURNAMENT DATA (JSON FORMAT - Last 10 Tournaments):
{json.dumps(tournament_json_data, indent=2)}

INSTRUCTIONS: Analyze this tournament data to identify patterns and provide specific recommendations for optimal tournament selection and ROI maximization. Focus on format preferences, buy-in optimization, venue performance, and strategic adjustments based on the actual results shown above."""
                        
                        else:
                            # Basic context for other modes
                            total_tournaments = len(user_tournaments)
                            recent_results = user_tournaments[:3]  # Last 3 tournaments
                            tournament_context = f"Context: The user has played {total_tournaments} tracked tournaments. "
                            tournament_context += "Recent results: " + ", ".join([
                                f"${t['prize_won']} won (${t['total_investment']} invested)" for t in recent_results
                            ])
                    
                    # Get relevant chat history
                    past_chats = get_user_chats(st.session_state["username"])
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
                    st.session_state["username"],
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

        TOURNAMENT_STRATEGY_PROMPT = """You are an expert Tournament Selection & ROI Optimization Coach GPT. Your specialty is analyzing a player's historical tournament performance to provide data-driven recommendations for specific tournaments they're considering.

        Your Primary Function:
            •   First, ask the user for details about the specific tournament they're considering playing
            •   Analyze their historical data in context of this specific tournament opportunity
            •   Provide tailored recommendations for that exact tournament based on their past performance patterns
            •   Give specific strategic advice for maximizing ROI in that particular tournament

        Step 1 - Gather Tournament Details:
        Ask the user to provide details about the tournament they're considering:
            •   Venue/Location (casino name, online site, etc.)
            •   Buy-in amount and structure (rebuys, add-ons allowed?)
            •   Format (Live or Online)
            •   Expected field size or typical field size
            •   Tournament structure (deep stack, turbo, etc.)
            •   Any other relevant details about the event

        Step 2 - Data Analysis & Recommendations:
        Based on their tournament history data, analyze:
            •   Their performance at similar venues
            •   ROI trends at similar buy-in levels
            •   Success rates in similar formats (Live vs Online)
            •   Performance in similar field sizes
            •   Optimal strategy adjustments for this specific tournament type

        Step 3 - Specific Recommendations:
        Provide actionable advice:
            •   Whether they should play this tournament (yes/no with reasoning)
            •   Expected ROI range based on their historical performance
            •   Optimal strategy approach for this specific tournament
            •   Bankroll considerations and risk assessment
            •   Specific adjustments to make based on venue/format/field size

        Your Approach:
            •   Start every conversation by asking for the specific tournament details
            •   Reference their actual performance data when making recommendations
            •   Compare this tournament to similar ones in their history
            •   Provide confidence levels for your recommendations based on sample size
            •   Give specific, actionable advice rather than generic tournament strategy

        Remember: You have access to their complete tournament history in JSON format. Use this data to provide personalized, evidence-based recommendations for the specific tournament they're asking about. Always tie your advice back to their actual results in similar situations."""

        # Mode selection
        try:
            mode = st.radio(
                "Select Coaching Mode:",
                ["General Coaching Chat", "Personalized Tournament Strategy Analysis", "Enter Tournament Result", "View Tournament Results"],
                key="coaching_mode",
                on_change=on_mode_change
            )

            if mode == "Enter Tournament Result":
                with st.form("tournament_result"):
                    st.subheader("Enter Tournament Result")
                    try:
                        col1, col2 = st.columns(2)
                        with col1:
                            venue = st.text_input("Venue (Casino/Online Site)")
                            format_type = st.selectbox("Format", ["Live", "Online"])
                            tournament_date = st.date_input("Tournament Date")
                            buy_in = st.number_input("Buy-in ($)", min_value=0.0, step=1.0)
                            rebuys = st.number_input("Number of Rebuys", min_value=0, step=1)
                            add_ons = st.number_input("Number of Add-ons", min_value=0, step=1)
                            total_entries = st.number_input("Total Entries", min_value=1, step=1)
                        
                        with col2:
                            position = st.number_input("Position Finished", min_value=1, step=1)
                            prize = st.number_input("Prize Won ($)", min_value=0.0, step=1.0)
                            duration = st.number_input("Duration (hours)", min_value=0.0, step=0.5)
                            
                            # Tournament Structure
                            st.subheader("Tournament Structure")
                            tournament_structure = st.selectbox("Tournament Structure", [
                                "Multi-Table Tournament (MTT)",
                                "Deep Stack",
                                "Turbo",
                                "Hyper Turbo",
                                "Bounty/Progressive Knockout",
                                "Freezeout",
                                "Rebuy",
                                "Satellite",
                                "Sit & Go",
                                "Single Table Tournament",
                                "Other"
                            ])
                            starting_stack = st.number_input("Starting Chip Stack", min_value=1000, step=1000, value=20000, help="Starting chips (e.g., 20,000)")
                            ante_structure = st.selectbox("Ante Structure", ["No Ante", "Ante Later Levels", "Ante All Levels"])
                            level_time = st.number_input("Level Time (minutes)", min_value=5, step=5, value=20, help="Length of each blind level in minutes")
                        
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
                                    "tournament_date": tournament_date.strftime("%Y-%m-%d"),
                                    "buy_in": buy_in,
                                    "rebuys": rebuys,
                                    "add_ons": add_ons,
                                    "total_investment": total_investment,
                                    "total_entries": total_entries,
                                    "position_finished": position,
                                    "prize_won": prize,
                                    "duration_hours": duration,
                                    "tournament_structure": tournament_structure,
                                    "starting_stack": starting_stack,
                                    "ante_structure": ante_structure,
                                    "level_time_minutes": level_time,
                                    "notes": notes
                                }
                                try:
                                    save_tournament_result(st.session_state["username"], tournament_data)
                                    st.success("Tournament result saved successfully!")
                                    st.rerun()  # Updated from experimental_rerun to rerun
                                except Exception as e:
                                    st.error(f"Error saving tournament result: {str(e)}")
                    except Exception as e:
                        st.error(f"Error displaying tournament form: {str(e)}")
            
            elif mode == "View Tournament Results":
                st.subheader("📊 Your Tournament Results")
                
                try:
                    # Get tournament results from database
                    tournament_results = get_user_tournament_results(st.session_state["username"])
                    
                    if tournament_results:
                        # Handle edit mode
                        if 'edit_tournament_id' in st.session_state:
                            tournament_to_edit = get_single_tournament_result(st.session_state.edit_tournament_id, st.session_state["username"])
                            if tournament_to_edit:
                                st.subheader("✏️ Edit Tournament Result")
                                
                                with st.form("edit_tournament_result"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        venue = st.text_input("Venue (Casino/Online Site)", value=tournament_to_edit.get('venue', ''))
                                        format_type = st.selectbox("Format", ["Live", "Online"], 
                                                                  index=0 if tournament_to_edit.get('format') == 'Live' else 1)
                                        tournament_date = st.date_input("Tournament Date", 
                                                                       value=pd.to_datetime(tournament_to_edit.get('tournament_date')).date() if tournament_to_edit.get('tournament_date') else None)
                                        buy_in = st.number_input("Buy-in ($)", min_value=0.0, step=1.0, value=float(tournament_to_edit.get('buy_in', 0)))
                                        rebuys = st.number_input("Number of Rebuys", min_value=0, step=1, value=int(tournament_to_edit.get('rebuys', 0)))
                                        add_ons = st.number_input("Number of Add-ons", min_value=0, step=1, value=int(tournament_to_edit.get('add_ons', 0)))
                                        total_entries = st.number_input("Total Entries", min_value=1, step=1, value=int(tournament_to_edit.get('total_entries', 1)))
                                    
                                    with col2:
                                        position = st.number_input("Position Finished", min_value=1, step=1, value=int(tournament_to_edit.get('position_finished', 1)))
                                        prize = st.number_input("Prize Won ($)", min_value=0.0, step=1.0, value=float(tournament_to_edit.get('prize_won', 0)))
                                        duration = st.number_input("Duration (hours)", min_value=0.0, step=0.5, value=float(tournament_to_edit.get('duration_hours', 0)))
                                        
                                        # Tournament Structure
                                        st.subheader("Tournament Structure")
                                        tournament_structure_options = [
                                            "Multi-Table Tournament (MTT)",
                                            "Deep Stack",
                                            "Turbo",
                                            "Hyper Turbo",
                                            "Bounty/Progressive Knockout",
                                            "Freezeout",
                                            "Rebuy",
                                            "Satellite",
                                            "Sit & Go",
                                            "Single Table Tournament",
                                            "Other"
                                        ]
                                        current_structure = tournament_to_edit.get('tournament_structure', 'Multi-Table Tournament (MTT)')
                                        structure_index = tournament_structure_options.index(current_structure) if current_structure in tournament_structure_options else 0
                                        tournament_structure = st.selectbox("Tournament Structure", tournament_structure_options, index=structure_index)
                                        starting_stack = st.number_input("Starting Chip Stack", min_value=1000, step=1000, 
                                                                        value=int(tournament_to_edit.get('starting_stack', 20000)))
                                        ante_structure_options = ["No Ante", "Ante Later Levels", "Ante All Levels"]
                                        current_ante = tournament_to_edit.get('ante_structure', 'No Ante')
                                        ante_index = ante_structure_options.index(current_ante) if current_ante in ante_structure_options else 0
                                        ante_structure = st.selectbox("Ante Structure", ante_structure_options, index=ante_index)
                                        level_time = st.number_input("Level Time (minutes)", min_value=5, step=5, 
                                                                    value=int(tournament_to_edit.get('level_time_minutes', 20)))
                                    
                                    notes = st.text_area("Tournament Notes", value=tournament_to_edit.get('notes', ''))
                                    
                                    col_save, col_cancel = st.columns(2)
                                    with col_save:
                                        if st.form_submit_button("💾 Save Changes", type="primary"):
                                            if not venue:
                                                st.error("Please enter a venue name")
                                            else:
                                                total_investment = buy_in * (1 + rebuys) + (add_ons * buy_in)
                                                updated_tournament_data = {
                                                    "venue": venue,
                                                    "format": format_type,
                                                    "tournament_date": tournament_date.strftime("%Y-%m-%d"),
                                                    "buy_in": buy_in,
                                                    "rebuys": rebuys,
                                                    "add_ons": add_ons,
                                                    "total_investment": total_investment,
                                                    "total_entries": total_entries,
                                                    "position_finished": position,
                                                    "prize_won": prize,
                                                    "duration_hours": duration,
                                                    "tournament_structure": tournament_structure,
                                                    "starting_stack": starting_stack,
                                                    "ante_structure": ante_structure,
                                                    "level_time_minutes": level_time,
                                                    "notes": notes
                                                }
                                                try:
                                                    update_tournament_result(st.session_state.edit_tournament_id, st.session_state["username"], updated_tournament_data)
                                                    st.success("Tournament result updated successfully!")
                                                    del st.session_state.edit_tournament_id
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Error updating tournament result: {str(e)}")
                                    
                                    with col_cancel:
                                        if st.form_submit_button("❌ Cancel"):
                                            del st.session_state.edit_tournament_id
                                            st.rerun()
                            else:
                                st.error("Tournament not found")
                                del st.session_state.edit_tournament_id
                                st.rerun()
                        
                        else:
                            # Display custom table with action buttons
                            st.subheader("Tournament Records")
                            
                            # Simplified table header - only 6 columns now
                            header_cols = st.columns([1.5, 2.5, 1.5, 1.2, 1.2, 1.5])
                            with header_cols[0]:
                                st.markdown("**Actions**")
                            with header_cols[1]:
                                st.markdown("**Venue**")
                            with header_cols[2]:
                                st.markdown("**Tournament Date**")
                            with header_cols[3]:
                                st.markdown("**Position**")
                            with header_cols[4]:
                                st.markdown("**Field Size**")
                            with header_cols[5]:
                                st.markdown("**Prize Won**")
                            
                            st.divider()
                            
                            # Display each tournament as a row with action buttons
                            for i, result in enumerate(tournament_results):
                                # Handle delete confirmation for this specific row
                                delete_confirm_key = f"delete_confirm_{i}"
                                
                                if st.session_state.get(delete_confirm_key, False):
                                    # Show delete confirmation
                                    confirm_cols = st.columns([1.5, 7])
                                    with confirm_cols[0]:
                                        col_yes, col_no = st.columns(2)
                                        with col_yes:
                                            if st.button("✅", key=f"confirm_delete_{i}", help="Confirm delete"):
                                                try:
                                                    deleted_count = delete_single_tournament_result(str(result['_id']), st.session_state["username"])
                                                    if deleted_count > 0:
                                                        st.success("✅ Tournament deleted!")
                                                        st.session_state[delete_confirm_key] = False
                                                        st.rerun()
                                                    else:
                                                        st.error("❌ Could not delete tournament")
                                                except Exception as e:
                                                    st.error(f"Error: {str(e)}")
                                        with col_no:
                                            if st.button("❌", key=f"cancel_delete_{i}", help="Cancel delete"):
                                                st.session_state[delete_confirm_key] = False
                                                st.rerun()
                                    with confirm_cols[1]:
                                        st.warning(f"⚠️ Delete: {result['venue']} - {result['tournament_date']} - ${result['buy_in']:.0f}?")
                                else:
                                    # Simplified row display
                                    row_cols = st.columns([1.5, 2.5, 1.5, 1.2, 1.2, 1.5])
                                    
                                    with row_cols[0]:
                                        # Action buttons
                                        btn_col1, btn_col2 = st.columns(2)
                                        with btn_col1:
                                            if st.button("✏️", key=f"edit_{i}", help="Edit tournament"):
                                                st.session_state.edit_tournament_id = str(result['_id'])
                                                st.rerun()
                                        with btn_col2:
                                            if st.button("🗑️", key=f"delete_{i}", help="Delete tournament"):
                                                st.session_state[delete_confirm_key] = True
                                                st.rerun()
                                    
                                    with row_cols[1]:
                                        st.text(result['venue'])
                                    
                                    with row_cols[2]:
                                        st.text(result['tournament_date'])
                                    
                                    with row_cols[3]:
                                        st.text(str(result['position_finished']))
                                    
                                    with row_cols[4]:
                                        st.text(str(result['total_entries']))
                                    
                                    with row_cols[5]:
                                        st.text(f"${result['prize_won']:.0f}")
                                
                                # Add a subtle separator between rows
                                st.markdown("<hr style='margin: 10px 0; border: 0.5px solid #333;'>", unsafe_allow_html=True)
                            
                            # Add download option - create DataFrame for CSV export
                            st.divider()
                            export_data = []
                            for result in tournament_results:
                                profit_loss = result['prize_won'] - result['total_investment']
                                roi = (profit_loss / result['total_investment'] * 100) if result['total_investment'] > 0 else 0
                                
                                export_data.append({
                                    'Date': result['tournament_date'],
                                    'Venue': result['venue'],
                                    'Format': result['format'],
                                    'Buy-in': result['buy_in'],
                                    'Rebuys': result.get('rebuys', 0),
                                    'Add-ons': result.get('add_ons', 0),
                                    'Total Investment': result['total_investment'],
                                    'Total Entries': result['total_entries'],
                                    'Position Finished': result['position_finished'],
                                    'Prize Won': result['prize_won'],
                                    'Profit/Loss': profit_loss,
                                    'ROI (%)': roi,
                                    'Duration (hours)': result.get('duration_hours', 0),
                                    'Tournament Structure': result.get('tournament_structure', 'N/A'),
                                    'Starting Stack': result.get('starting_stack', 'N/A'),
                                    'Ante Structure': result.get('ante_structure', 'N/A'),
                                    'Level Time (min)': result.get('level_time_minutes', 'N/A'),
                                    'Notes': result.get('notes', '')
                                })
                            
                            export_df = pd.DataFrame(export_data)
                            csv = export_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Results as CSV",
                                data=csv,
                                file_name=f"tournament_results_{st.session_state['username']}.csv",
                                mime="text/csv"
                            )
                            
                            # Add clear all data option
                            st.divider()
                            st.subheader("🗑️ Data Management")
                            
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                if st.button("🗑️ Clear All Data", type="secondary"):
                                    st.session_state.show_clear_confirm = True
                            
                            with col2:
                                if st.session_state.get('show_clear_confirm', False):
                                    st.warning("⚠️ This will permanently delete ALL your tournament results!")
                                    col_yes, col_no = st.columns(2)
                                    with col_yes:
                                        if st.button("✅ Yes, Delete All", type="primary"):
                                            try:
                                                deleted_count = delete_user_tournament_results(st.session_state["username"])
                                                st.success(f"✅ Successfully deleted {deleted_count} tournament records!")
                                                st.session_state.show_clear_confirm = False
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error deleting data: {str(e)}")
                                    with col_no:
                                        if st.button("❌ Cancel"):
                                            st.session_state.show_clear_confirm = False
                                            st.rerun()
                    else:
                        st.info("📝 No tournament results found. Start by entering your tournament results!")
                        st.markdown("Use the **'Enter Tournament Result'** mode to add your first tournament.")
                        
                except Exception as e:
                    st.error(f"Error loading tournament results: {str(e)}")
                    st.info("💡 If you're seeing this error, the database connection might not be working. Tournament results will be available once the database is connected.")

            elif mode == "Personalized Tournament Strategy Analysis":
                st.subheader("🎯 Tournament Strategy Analysis")
                st.info("Fill out the details of the tournament you're considering, and I'll analyze your historical data to provide personalized recommendations.")
                
                with st.form("tournament_analysis"):
                    st.subheader("Tournament Details")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        venue = st.text_input("Venue/Location*", placeholder="e.g., Bellagio, PokerStars, Borgata")
                        buy_in = st.number_input("Buy-in Amount ($)*", min_value=0.0, step=1.0, value=100.0)
                        format_type = st.selectbox("Format*", ["Live", "Online"])
                        field_size = st.number_input("Expected Field Size*", min_value=1, step=1, value=100, help="Expected number of players")
                        
                        # EV Calculation Parameters
                        st.subheader("Tournament Structure & EV Analysis")
                        rake_percent = st.number_input("Rake Percentage (%)", min_value=0.0, max_value=50.0, step=0.5, value=10.0, help="Tournament rake percentage (typically 10-15%)")
                        paid_percent = st.number_input("Players Paid (%)", min_value=1.0, max_value=100.0, step=1.0, value=15.0, help="Percentage of field that gets paid (typically 10-20%)")
                    
                    with col2:
                        structure = st.selectbox("Tournament Structure", 
                                                ["Multi-Table Tournament (MTT)",
                                                 "Deep Stack",
                                                 "Turbo",
                                                 "Hyper Turbo",
                                                 "Bounty/Progressive Knockout",
                                                 "Freezeout",
                                                 "Rebuy",
                                                 "Satellite",
                                                 "Sit & Go",
                                                 "Single Table Tournament",
                                                 "Other"])
                        rebuys_allowed = st.selectbox("Rebuys Allowed?", ["No", "Yes - Limited", "Yes - Unlimited"])
                        
                        # Conditional rebuy details
                        num_rebuys = 0
                        if rebuys_allowed != "No":
                            num_rebuys = st.number_input("Expected Number of Rebuys", min_value=0, step=1, value=1, help="How many rebuys do you typically use?")
                        
                        addon_available = st.selectbox("Add-on Available?", ["No", "Yes"])
                        addon_cost = 0
                        if addon_available == "Yes":
                            addon_cost = st.number_input("Add-on Cost ($)", min_value=0.0, step=1.0, value=buy_in, help="Cost of the add-on (often same as buy-in)")
                        
                        # Tournament Structure
                        st.subheader("Tournament Structure")
                        tournament_structure = st.selectbox("Tournament Structure", [
                            "Multi-Table Tournament (MTT)",
                            "Deep Stack",
                            "Turbo",
                            "Hyper Turbo",
                            "Bounty/Progressive Knockout",
                            "Freezeout",
                            "Rebuy",
                            "Satellite",
                            "Sit & Go",
                            "Single Table Tournament",
                            "Other"
                        ])
                        starting_stack = st.number_input("Starting Chip Stack", min_value=1000, step=1000, value=20000, help="Starting chips (e.g., 20,000)")
                        ante_structure = st.selectbox("Ante Structure", ["No Ante", "Ante Later Levels", "Ante All Levels"])
                        level_time = st.number_input("Level Time (minutes)", min_value=5, step=5, value=20, help="Length of each blind level in minutes")
                        
                        other_details = st.text_area("Other Details", 
                                                   placeholder="Any other relevant info: special format, etc.")
                    
                    st.markdown("*Required fields")
                    
                    submitted = st.form_submit_button("🎯 Get My Tournament Analysis & EV Calculation", type="primary")
                    
                    if submitted:
                        if not venue or buy_in <= 0 or field_size <= 0:
                            st.error("Please fill in the required fields: Venue, Buy-in Amount, and Field Size")
                        else:
                            # Import EV calculation function
                            try:
                                import sys
                                import os
                                sys.path.append(os.path.join(os.path.dirname(__file__), 'player_model'))
                                from ev import calculate_tournament_ev
                                from tournament import tournament_structure
                                from player import player_pdf
                                
                                # Get user's tournament history for personalized distribution
                                user_tournaments = get_user_tournament_results(st.session_state["username"])
                                
                                # Determine buy-in range for filtering (±50% of current buy-in)
                                buyin_range = (buy_in * 0.5, buy_in * 2.0) if user_tournaments else None
                                
                                # Calculate EV with personalized distribution
                                total_investment = buy_in * (1 + num_rebuys) + addon_cost
                                
                                if user_tournaments:
                                    # Use personalized distribution
                                    ev_result = calculate_tournament_ev(
                                        num_players=int(field_size),
                                        buy_in=buy_in,
                                        num_rebuys=num_rebuys,
                                        rake_percent=rake_percent/100,  # Convert percentage to decimal
                                        paid_percent=paid_percent/100,   # Convert percentage to decimal
                                        tournament_history=user_tournaments,
                                        format_filter=format_type,
                                        buyin_range=buyin_range
                                    )
                                    
                                    # Handle return value (could be tuple with metadata or just float)
                                    if isinstance(ev_result, tuple):
                                        ev, personalized_metadata = ev_result
                                        distribution_info = f"**🎯 Personalized Analysis:** Based on {personalized_metadata['sample_size']} similar tournaments (Confidence: {personalized_metadata['confidence_level'].title()})"
                                        
                                        # Get the personalized distribution for the table
                                        personalized_distribution, _ = player_pdf(
                                            user_tournaments, int(field_size), format_type, buyin_range
                                        )
                                    else:
                                        ev = ev_result
                                        personalized_metadata = None
                                        distribution_info = "**📊 Standard Analysis:** Using uniform probability distribution"
                                        personalized_distribution = None
                                else:
                                    # No tournament history, use uniform distribution
                                    ev = calculate_tournament_ev(
                                        num_players=int(field_size),
                                        buy_in=buy_in,
                                        num_rebuys=num_rebuys,
                                        rake_percent=rake_percent/100,
                                        paid_percent=paid_percent/100
                                    )
                                    personalized_metadata = None
                                    distribution_info = "**📊 Standard Analysis:** No tournament history available, using uniform probability distribution"
                                    personalized_distribution = None
                                
                                # Get payout structure
                                payout_structure = tournament_structure(
                                    int(field_size),
                                    buy_in,
                                    rake_percent=rake_percent/100,
                                    paid_percent=paid_percent/100
                                )
                                
                                # Display EV Analysis Results
                                st.divider()
                                st.subheader("📊 Mathematical EV Analysis")
                                
                                # Show distribution type being used
                                st.info(distribution_info)
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Expected Value", f"${ev:.2f}")
                                with col2:
                                    roi_percent = (ev / total_investment * 100) if total_investment > 0 else 0
                                    st.metric("Expected ROI", f"{roi_percent:.1f}%")
                                with col3:
                                    st.metric("Total Investment", f"${total_investment:.0f}")
                                with col4:
                                    breakeven_percent = (total_investment / (payout_structure['Payout ($)'].sum() / field_size)) * 100 if field_size > 0 else 0
                                    st.metric("Break-even Rate", f"{breakeven_percent:.1f}%")
                                
                                # Show personalized performance insights if available
                                if personalized_metadata and personalized_metadata['sample_size'] > 0:
                                    with st.expander("🎯 Your Historical Performance Insights"):
                                        col_a, col_b, col_c = st.columns(3)
                                        with col_a:
                                            expected_pos = personalized_metadata['expected_finish_position']
                                            st.metric("Expected Finish Position", f"{expected_pos}/{field_size}")
                                        with col_b:
                                            avg_percentile = personalized_metadata['avg_finish_percentile'] * 100
                                            st.metric("Average Finish Percentile", f"{avg_percentile:.1f}%")
                                        with col_c:
                                            best_percentile = personalized_metadata['best_finish_percentile'] * 100
                                            st.metric("Best Finish Percentile", f"{best_percentile:.1f}%")
                                        
                                        st.markdown(f"""
                                        **Analysis Method:** {personalized_metadata['method'].replace('_', ' ').title()}
                                        
                                        **Data Used:** {personalized_metadata['sample_size']} tournaments matching your criteria
                                        
                                        **Filters Applied:**
                                        - Format: {personalized_metadata['filters_applied']['format'] or 'All'}
                                        - Buy-in Range: ${buyin_range[0]:.0f} - ${buyin_range[1]:.0f}
                                        """)
                                
                                # Show enhanced payout analysis with personalized probabilities
                                with st.expander("💰 View Position Analysis: Payout, Probability & ROI"):
                                    # Create enhanced analysis table
                                    import pandas as pd
                                    
                                    # Use personalized distribution if available, otherwise uniform
                                    if personalized_distribution is not None:
                                        probability_source = "📊 **Personalized Probabilities** (Based on Your Tournament History)"
                                    else:
                                        probability_source = "📊 **Uniform Probabilities** (Equal chance for each position)"
                                        personalized_distribution = np.ones(field_size) / field_size
                                    
                                    st.markdown(probability_source)
                                    
                                    # Create analysis data
                                    analysis_data = []
                                    
                                    # Add paying positions
                                    for i, (position, payout) in enumerate(zip(payout_structure['Position'], payout_structure['Payout ($)'])):
                                        position_idx = int(position) - 1  # Convert to 0-based index
                                        
                                        if position_idx < len(personalized_distribution):
                                            position_probability = personalized_distribution[position_idx]
                                        else:
                                            position_probability = 0
                                            
                                        roi = ((payout - total_investment) / total_investment * 100) if total_investment > 0 else 0
                                        analysis_data.append({
                                            'Position': f"{position}",
                                            'Payout': f"${payout:,.0f}",
                                            'Probability': f"{position_probability:.6f} ({position_probability*100:.3f}%)",
                                            'ROI': f"{roi:+.1f}%"
                                        })
                                    
                                    # Add non-paying positions summary
                                    non_paying_positions = field_size - len(payout_structure)
                                    if non_paying_positions > 0:
                                        # Sum probabilities for all non-paying positions
                                        non_paying_prob = sum(personalized_distribution[len(payout_structure):])
                                        loss_roi = -100.0  # Complete loss
                                        analysis_data.append({
                                            'Position': f"{len(payout_structure)+1}-{field_size}",
                                            'Payout': "$0",
                                            'Probability': f"{non_paying_prob:.6f} ({non_paying_prob*100:.2f}%)",
                                            'ROI': f"{loss_roi:.1f}%"
                                        })
                                    
                                    # Create and display DataFrame
                                    analysis_df = pd.DataFrame(analysis_data)
                                    st.dataframe(analysis_df, use_container_width=True, hide_index=True)
                                    
                                    # Add summary statistics
                                    st.markdown("**📈 Key Insights:**")
                                    itm_prob = sum(personalized_distribution[:len(payout_structure)]) * 100
                                    min_cash = payout_structure['Payout ($)'].iloc[-1] if len(payout_structure) > 0 else 0
                                    min_cash_roi = ((min_cash - total_investment) / total_investment * 100) if total_investment > 0 and min_cash > 0 else -100
                                    
                                    col_a, col_b, col_c = st.columns(3)
                                    with col_a:
                                        st.metric("ITM Probability", f"{itm_prob:.2f}%")
                                    with col_b:
                                        st.metric("Min Cash ROI", f"{min_cash_roi:+.1f}%")
                                    with col_c:
                                        bubble_position = len(payout_structure) + 1 if len(payout_structure) < field_size else field_size
                                        st.metric("Bubble Position", f"{bubble_position}")
                                
                            except ImportError as e:
                                st.warning(f"⚠️ EV calculation module not available: {str(e)}")
                                st.info("Proceeding with coaching analysis only...")
                                ev = None
                                total_investment = buy_in * (1 + num_rebuys) + addon_cost
                            except Exception as e:
                                st.error(f"Error calculating EV: {str(e)}")
                                st.info("Falling back to standard analysis...")
                                ev = None
                                total_investment = buy_in * (1 + num_rebuys) + addon_cost
                            
                            # Create enhanced tournament analysis query with EV data
                            ev_context = ""
                            if ev is not None:
                                roi_percent = (ev / total_investment * 100) if total_investment > 0 else 0
                                ev_context = f"""
MATHEMATICAL EV ANALYSIS:
- Expected Value: ${ev:.2f}
- Expected ROI: {roi_percent:.1f}%
- Total Investment: ${total_investment:.0f}
- Break-even Performance Required: Top {paid_percent:.0f}% of field

"""
                            
                            tournament_query = f"""
I'm considering playing a tournament with these details:
- Venue: {venue}
- Buy-in: ${buy_in}
- Format: {format_type}
- Expected Field Size: {field_size} players
- Structure: {structure}
- Rebuys: {rebuys_allowed} (Expected: {num_rebuys})
- Add-on: {addon_available} (Cost: ${addon_cost})
- Rake: {rake_percent}%
- Players Paid: {paid_percent}%
- Starting Stack: {starting_stack:,} chips
- Ante Structure: {ante_structure}
- Level Time: {level_time} minutes
- Additional Details: {other_details if other_details else 'None provided'}

{ev_context}Based on my tournament history data AND the mathematical EV analysis above, please analyze whether I should play this tournament. Provide specific recommendations for maximizing my ROI, compare the mathematical expectation with my historical performance, and give your confidence level in the recommendation. 

Consider how the tournament structure (starting stack, level time, ante structure) affects my typical playing style and historical performance patterns."""
                            
                            # Initialize chat with tournament data and analysis
                            user_tournaments = get_user_tournament_results(st.session_state["username"])
                            tournament_context = ""
                            
                            if user_tournaments:
                                # Get comprehensive tournament data for analysis
                                total_tournaments = len(user_tournaments)
                                total_profit = sum(t['prize_won'] - t['total_investment'] for t in user_tournaments)
                                total_investment = sum(t['total_investment'] for t in user_tournaments)
                                overall_roi = (total_profit / total_investment * 100) if total_investment > 0 else 0
                                itm_count = sum(1 for t in user_tournaments if t['prize_won'] > 0)
                                itm_rate = (itm_count / total_tournaments * 100) if total_tournaments > 0 else 0
                                
                                # Performance by format
                                live_tournaments = [t for t in user_tournaments if t.get('format') == 'Live']
                                online_tournaments = [t for t in user_tournaments if t.get('format') == 'Online']
                                
                                live_roi = 0
                                online_roi = 0
                                if live_tournaments:
                                    live_profit = sum(t['prize_won'] - t['total_investment'] for t in live_tournaments)
                                    live_investment = sum(t['total_investment'] for t in live_tournaments)
                                    live_roi = (live_profit / live_investment * 100) if live_investment > 0 else 0
                                
                                if online_tournaments:
                                    online_profit = sum(t['prize_won'] - t['total_investment'] for t in online_tournaments)
                                    online_investment = sum(t['total_investment'] for t in online_tournaments)
                                    online_roi = (online_profit / online_investment * 100) if online_investment > 0 else 0
                                
                                # Get all tournament data in JSON format
                                import json
                                tournament_json_data = []
                                
                                for t in user_tournaments:
                                    clean_tournament = {
                                        "tournament_date": t.get('tournament_date'),
                                        "venue": t.get('venue'),
                                        "format": t.get('format'),
                                        "buy_in": t.get('buy_in'),
                                        "rebuys": t.get('rebuys', 0),
                                        "add_ons": t.get('add_ons', 0),
                                        "total_investment": t.get('total_investment'),
                                        "total_entries": t.get('total_entries'),
                                        "position_finished": t.get('position_finished'),
                                        "prize_won": t.get('prize_won'),
                                        "duration_hours": t.get('duration_hours', 0),
                                        "starting_stack": t.get('starting_stack'),
                                        "ante_structure": t.get('ante_structure'),
                                        "level_time_minutes": t.get('level_time_minutes'),
                                        "notes": t.get('notes', ''),
                                        "profit_loss": t.get('prize_won', 0) - t.get('total_investment', 0),
                                        "roi_percent": ((t.get('prize_won', 0) - t.get('total_investment', 0)) / t.get('total_investment', 1) * 100)
                                    }
                                    tournament_json_data.append(clean_tournament)
                                
                                tournament_context = f"""
USER TOURNAMENT PERFORMANCE DATA FOR ANALYSIS:

Overall Performance Summary:
- Total Tournaments: {total_tournaments}
- Overall ROI: {overall_roi:.1f}%
- ITM Rate: {itm_rate:.1f}%
- Total Profit/Loss: ${total_profit:,.0f}
- Total Investment: ${total_investment:,.0f}

Format Performance:
- Live Tournaments: {len(live_tournaments)} played, ROI: {live_roi:.1f}%
- Online Tournaments: {len(online_tournaments)} played, ROI: {online_roi:.1f}%

COMPLETE TOURNAMENT HISTORY (JSON FORMAT):
{json.dumps(tournament_json_data, indent=2)}

INSTRUCTIONS: Analyze this tournament data in context of the specific tournament the user is asking about. Compare venue performance, buy-in range success, format preferences, and field size patterns to provide a data-driven recommendation."""
                            
                            system_prompt = TOURNAMENT_STRATEGY_PROMPT
                            if tournament_context:
                                system_prompt += f"\n\n{tournament_context}"
                            
                            st.session_state.chat = [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": tournament_query}
                            ]
                            
                            # Get AI analysis
                            try:
                                response = client.chat.completions.create(
                                    model="o3-mini",
                                    reasoning_effort="medium",
                                    messages=st.session_state.chat
                                )
                                
                                reply = response.choices[0].message.content
                                st.session_state.chat.append({"role": "assistant", "content": reply})
                                
                                # Save analysis to database
                                save_chat(
                                    st.session_state["username"],
                                    st.session_state.coaching_mode,
                                    st.session_state.chat
                                )
                                
                                # Display the analysis
                                st.divider()
                                st.subheader("📊 Your Personalized Tournament Analysis")
                                st.markdown(reply)
                                
                                # Option for follow-up questions
                                st.divider()
                                st.subheader("💬 Follow-up Questions")
                                follow_up = st.text_input("Ask any follow-up questions about this analysis:", key="follow_up_question")
                                if st.button("Ask Question") and follow_up:
                                    st.session_state.chat.append({"role": "user", "content": follow_up})
                                    
                                    follow_response = client.chat.completions.create(
                                        model="o3-mini",
                                        reasoning_effort="medium",
                                        messages=st.session_state.chat
                                    )
                                    
                                    follow_reply = follow_response.choices[0].message.content
                                    st.session_state.chat.append({"role": "assistant", "content": follow_reply})
                                    
                                    save_chat(
                                        st.session_state["username"],
                                        st.session_state.coaching_mode,
                                        st.session_state.chat
                                    )
                                    
                                    st.markdown("**Follow-up Answer:**")
                                    st.markdown(follow_reply)
                                    st.rerun()
                                    
                            except Exception as e:
                                st.error(f"Error getting analysis: {str(e)}")

            else:
                # Display mode-specific instructions
                if mode == "Personalized Tournament Strategy Analysis":
                    st.info("I'll analyze your tournament history data to recommend optimal tournament selection and strategies for maximizing your ROI. Let me review your past results and provide data-driven recommendations!")

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