"""
AI Coaching module for Poker Coach application.
Handles chat sessions, AI responses, and tournament context generation.
"""
import opik
from openai import OpenAI
from opik import track, opik_context
from opik.integrations.openai import track_openai
from datetime import datetime, timedelta
from src.utils.calculations import calculate_overall_performance, calculate_performance_by_format
import streamlit as st

from src.config import OPENAI_MODEL, REASONING_EFFORT
from database import save_chat, get_user_chats, get_user_tournament_results

# Configure Opik and instantiate OpenAI client only once
opik.configure(use_local=False)
client = OpenAI()
tracked_client = track_openai(client)

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


@opik.track
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


@opik.track
def create_tournament_analysis_context(user_tournaments):
    """
    Create comprehensive tournament analysis context for strategy mode.
    
    Args:
        user_tournaments (list): User's tournament history
        
    Returns:
        str: Formatted tournament context
    """
    # Calculate overall performance using centralized function
    overall_stats = calculate_overall_performance(user_tournaments)
    
    # Calculate performance by format using centralized function  
    format_stats = calculate_performance_by_format(user_tournaments)
    
    # Performance by buy-in ranges
    low_buyin = [t for t in user_tournaments if t['buy_in'] <= 100]
    mid_buyin = [t for t in user_tournaments if 100 < t['buy_in'] <= 500]
    high_buyin = [t for t in user_tournaments if t['buy_in'] > 500]
    
    # Calculate venue performance (top 5 venues by frequency)
    venue_performance = {}
    for t in user_tournaments:
        venue = t.get('venue', 'Unknown')
        if venue not in venue_performance:
            venue_performance[venue] = {'count': 0, 'total_profit': 0, 'total_investment': 0}
        venue_performance[venue]['count'] += 1
        venue_performance[venue]['total_profit'] += t.get('prize_won', 0) - t.get('total_investment', 0)
        venue_performance[venue]['total_investment'] += t.get('total_investment', 0)
    
    # Sort venues by frequency and get top 5
    top_venues = sorted(venue_performance.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
    
    # Recent performance trend (last 10 tournaments)
    recent_tournaments = user_tournaments[:10]
    recent_profit = sum(t.get('prize_won', 0) - t.get('total_investment', 0) for t in recent_tournaments)
    recent_investment = sum(t.get('total_investment', 0) for t in recent_tournaments)
    recent_roi = (recent_profit / recent_investment * 100) if recent_investment > 0 else 0
    
    return f"""USER TOURNAMENT PERFORMANCE ANALYSIS:

OVERALL PERFORMANCE:
- Total Tournaments: {overall_stats['total_tournaments']}
- Overall ROI: {overall_stats['overall_roi']:.1f}%
- ITM Rate: {overall_stats['itm_rate']:.1f}%
- Total Profit/Loss: ${overall_stats['total_profit']:.0f}
- Total Investment: ${overall_stats['total_investment']:.0f}

FORMAT PERFORMANCE:
- Live: {format_stats['live']['total_tournaments']} tournaments, {format_stats['live']['overall_roi']:.1f}% ROI
- Online: {format_stats['online']['total_tournaments']} tournaments, {format_stats['online']['overall_roi']:.1f}% ROI

BUY-IN PERFORMANCE:
- Low Stakes ($1-$100): {len(low_buyin)} tournaments
- Mid Stakes ($101-$500): {len(mid_buyin)} tournaments  
- High Stakes ($500+): {len(high_buyin)} tournaments

TOP VENUES (by frequency):
{chr(10).join([f"- {venue}: {data['count']} tournaments, {(data['total_profit']/data['total_investment']*100 if data['total_investment'] > 0 else 0):.1f}% ROI" for venue, data in top_venues])}

RECENT TREND (Last 10 tournaments):
- Recent ROI: {recent_roi:.1f}%
- Recent Profit/Loss: ${recent_profit:.0f}

ANALYSIS INSTRUCTIONS:
Use this performance data to provide personalized recommendations. Focus on:
1. Format preferences (Live vs Online performance)
2. Optimal buy-in ranges based on historical ROI
3. Venue-specific performance patterns
4. Recent performance trends
5. Risk assessment based on bankroll and variance

Provide specific, actionable advice based on the user's actual results.""" 


@opik.track
def retrieve_user_tournaments(username, coaching_mode):
    return get_user_tournament_results(username)

@opik.track
def retrieve_chat_history(username, coaching_mode):
    past_chats = get_user_chats(username)
    chat_context = ""
    if past_chats:
        mode_chats = [chat for chat in past_chats if chat['mode'] == coaching_mode]
        if mode_chats:
            recent_chats = mode_chats[:3]
            chat_context = "\n\nPrevious relevant conversations:\n"
            for chat in recent_chats:
                messages = chat['messages']
                for i in range(1, len(messages)-1, 2):
                    chat_context += f"User: {messages[i]['content']}\n"
                    chat_context += f"Coach: {messages[i+1]['content']}\n"
    return chat_context

@opik.track(name="user_profile_analysis")
def user_profile_analysis(username, coaching_mode):
    user_tournaments = retrieve_user_tournaments(username, coaching_mode)
    chat_context = retrieve_chat_history(username, coaching_mode)
    messages = inject_prompt(username, coaching_mode, user_tournaments, chat_context)
    return messages

@opik.track
def inject_prompt(username, coaching_mode, user_tournaments, chat_context):
    tournament_context = ""
    if user_tournaments:
        if coaching_mode == "Personalized Tournament Strategy Analysis":
            tournament_context = create_tournament_analysis_context(user_tournaments)
        else:
            total_tournaments = len(user_tournaments)
            recent_results = user_tournaments[:3]
            tournament_context = f"Context: The user has played {total_tournaments} tracked tournaments. "
            tournament_context += "Recent results: " + ", ".join([
                f"${t['prize_won']} won (${t['total_investment']} invested)" for t in recent_results
            ])
    system_prompt = GENERAL_COACHING_PROMPT if coaching_mode == "General Coaching Chat" else TOURNAMENT_STRATEGY_PROMPT
    if tournament_context:
        system_prompt += f"\n\n{tournament_context}"
    if chat_context:
        system_prompt += f"\n{chat_context}\n\nUse the above conversation history to maintain consistency in your advice and build upon previous discussions. If you see patterns in the user's questions or areas they frequently ask about, address those topics more thoroughly."
    opik_context.update_current_trace(metadata={"system_prompt": system_prompt})
    return [{"role": "system", "content": system_prompt}]

@opik.track(name="llm_chat")
def chat_pipeline(user_input, username, coaching_mode):
    opik_context.update_current_trace(metadata={
        "coaching_mode": coaching_mode,
        "model": OPENAI_MODEL
    })
    messages = user_profile_analysis(username, coaching_mode)
    messages.append({"role": "user", "content": user_input})
    reply = generate_llm_response(tracked_client, messages, username, coaching_mode)
    save_chat(username, coaching_mode, messages + ([{"role": "assistant", "content": reply}] if reply else []))
    return reply

@opik.track
def generate_llm_response(tracked_client, messages, username, coaching_mode):
    try:
        response = tracked_client.chat.completions.create(
            model=OPENAI_MODEL,
            reasoning_effort=REASONING_EFFORT,
            messages=messages
        )
        reply = response.choices[0].message.content
        return reply
    except Exception as e:
        st.error(f"Error processing chat message: {str(e)}")
        return None