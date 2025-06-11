"""
AI Coaching module for Poker Coach application.
Handles chat sessions, AI responses, and tournament context generation.
"""

import streamlit as st
import os
import opik
from openai import OpenAI
from opik import track, opik_context
from opik.integrations.openai import track_openai
from datetime import datetime, timedelta
from src.utils.calculations import calculate_overall_performance, calculate_performance_by_format

from src.config import OPENAI_MODEL, REASONING_EFFORT
from database import save_chat, get_user_chats


# Initialize OpenAI clients
def setup_openai():
    """Initialize OpenAI clients and Opik tracking."""
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    os.environ["OPIK_API_KEY"] = st.secrets["OPIK_API_KEY"]
    os.environ["OPIK_WORKSPACE"] = "statisticianinstilettos" 
    os.environ["OPIK_PROJECT_NAME"] = "My-Poker-Coach"
    
    opik.configure(use_local=False)
    
    client = OpenAI()
    tracked_client = track_openai(client)
    
    # Initialize OpenAI client for Whisper
    if 'openai_client' not in st.session_state:
        st.session_state.openai_client = OpenAI()
    
    return client, tracked_client


# System prompts
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


def initialize_chat_session(username, coaching_mode, user_tournaments=None):
    """
    Initialize chat session with appropriate context and system prompt.
    
    Args:
        username (str): Current username
        coaching_mode (str): Selected coaching mode
        user_tournaments (list): User's tournament history
        
    Returns:
        list: Initialized chat messages
    """
    tournament_context = ""
    
    if user_tournaments:
        if coaching_mode == "Personalized Tournament Strategy Analysis":
            # Comprehensive tournament analysis for strategy mode
            tournament_context = create_tournament_analysis_context(user_tournaments)
        else:
            # Basic context for other modes
            total_tournaments = len(user_tournaments)
            recent_results = user_tournaments[:3]  # Last 3 tournaments
            tournament_context = f"Context: The user has played {total_tournaments} tracked tournaments. "
            tournament_context += "Recent results: " + ", ".join([
                f"${t['prize_won']} won (${t['total_investment']} invested)" for t in recent_results
            ])
    
    # Get relevant chat history
    past_chats = get_user_chats(username)
    chat_context = ""
    if past_chats:
        # Filter chats by current mode
        mode_chats = [chat for chat in past_chats if chat['mode'] == coaching_mode]
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
    
    system_prompt = GENERAL_COACHING_PROMPT if coaching_mode == "General Coaching Chat" else TOURNAMENT_STRATEGY_PROMPT
    
    # Add context to system prompt
    if tournament_context:
        system_prompt += f"\n\n{tournament_context}"
    if chat_context:
        system_prompt += f"\n{chat_context}\n\nUse the above conversation history to maintain consistency in your advice and build upon previous discussions. If you see patterns in the user's questions or areas they frequently ask about, address those topics more thoroughly."
    
    return [{"role": "system", "content": system_prompt}]


def create_tournament_analysis_context(user_tournaments):
    """
    Create comprehensive tournament analysis context for strategy mode.
    
    Args:
        user_tournaments (list): User's tournament history
        
    Returns:
        str: Formatted tournament context
    """
    import json
    
    # Calculate overall performance using centralized function
    overall_stats = calculate_overall_performance(user_tournaments)
    
    # Calculate performance by format using centralized function  
    format_stats = calculate_performance_by_format(user_tournaments)
    
    # Performance by buy-in ranges
    low_buyin = [t for t in user_tournaments if t['buy_in'] <= 100]
    mid_buyin = [t for t in user_tournaments if 100 < t['buy_in'] <= 500]
    high_buyin = [t for t in user_tournaments if t['buy_in'] > 500]
    
    # Get last 10 tournaments and convert to clean JSON for analysis
    last_10_tournaments = user_tournaments[:10]
    tournament_json_data = []
    
    for t in last_10_tournaments:
        clean_tournament = {
            "tournament_date": t.get('tournament_date'),
            "venue": t.get('venue'),
            "format": t.get('format'),
            "buy_in": t.get('buy_in'),
            "rebuys": t.get('rebuys', 0),
            "add_on_cost": t.get('add_on_cost', 0),
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
    
    return f"""
USER TOURNAMENT PERFORMANCE DATA FOR ANALYSIS:

Overall Performance Summary:
- Total Tournaments: {overall_stats['total_tournaments']}
- Overall ROI: {overall_stats['overall_roi']:.1f}%
- ITM Rate: {overall_stats['itm_rate']:.1f}%
- Total Profit/Loss: ${overall_stats['total_profit']:.0f}
- Total Investment: ${overall_stats['total_investment']:.0f}

Format Performance:
- Live Tournaments: {format_stats['live']['total_tournaments']} played, ROI: {format_stats['live']['overall_roi']:.1f}%
- Online Tournaments: {format_stats['online']['total_tournaments']} played, ROI: {format_stats['online']['overall_roi']:.1f}%

Buy-in Distribution:
- Low Stakes ($1-$100): {len(low_buyin)} tournaments
- Mid Stakes ($101-$500): {len(mid_buyin)} tournaments  
- High Stakes ($500+): {len(high_buyin)} tournaments

TOURNAMENT DATA (JSON FORMAT - Last 10 Tournaments):
{json.dumps(tournament_json_data, indent=2)}

INSTRUCTIONS: Analyze this tournament data to identify patterns and provide specific recommendations for optimal tournament selection and ROI maximization. Focus on format preferences, buy-in optimization, venue performance, and strategic adjustments based on the actual results shown above."""


def process_chat_message(client, messages, username, coaching_mode):
    """
    Process chat message with OpenAI and save to database.
    
    Args:
        client: OpenAI client
        messages (list): Chat messages
        username (str): Current username
        coaching_mode (str): Selected coaching mode
        
    Returns:
        str: AI response
    """
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            reasoning_effort=REASONING_EFFORT,
            messages=messages
        )
        
        reply = response.choices[0].message.content
        
        # Save chat to database
        save_chat(username, coaching_mode, messages + [{"role": "assistant", "content": reply}])
        
        return reply
        
    except Exception as e:
        st.error(f"Error processing chat message: {str(e)}")
        return None 