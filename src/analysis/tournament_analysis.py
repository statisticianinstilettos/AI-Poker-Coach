"""
Tournament analysis module for Poker Coach application.
Handles EV calculations and tournament analysis functionality.
"""

import streamlit as st
import sys
import os
import json
import pandas as pd
import numpy as np

# Add src/player_model to path
player_model_path = os.path.join(os.path.dirname(__file__), '../player_model')
if player_model_path not in sys.path:
    sys.path.append(player_model_path)

from src.ai.coaching import initialize_chat_session, process_chat_message, setup_openai
from src.utils.calculations import calculate_total_investment, calculate_roi
from database import get_user_tournament_results


def process_tournament_analysis(tournament_data, username):
    """
    Process tournament analysis with EV calculation and AI recommendations.
    
    Args:
        tournament_data (dict): Tournament parameters
        username (str): Current username
    """
    # Import EV calculation modules
    from ev import calculate_tournament_ev
    from tournament import tournament_structure
    from player import player_pdf
    
    # Get user's tournament history
    user_tournaments = get_user_tournament_results(username)
    
    # Extract tournament parameters
    buy_in = tournament_data['buy_in']
    field_size = tournament_data['field_size']
    format_type = tournament_data['format_type']
    num_rebuys = tournament_data['num_rebuys']
    addon_cost = tournament_data['addon_cost']
    rake_percent = tournament_data['rake_percent'] / 100
    paid_percent = tournament_data['paid_percent'] / 100
    
    # Calculate total investment
    total_investment = calculate_total_investment(buy_in, num_rebuys, addon_cost)
    
    # Determine buy-in range for filtering (±50% of current buy-in)
    buyin_range = (buy_in * 0.5, buy_in * 2.0) if user_tournaments else None
    
    # Calculate EV with personalized distribution if available
    if user_tournaments:
        ev_result = calculate_tournament_ev(
            num_players=int(field_size),
            buy_in=buy_in,
            num_rebuys=num_rebuys,
            rake_percent=rake_percent,
            paid_percent=paid_percent,
            tournament_history=user_tournaments,
            format_filter=format_type,
            buyin_range=buyin_range
        )
        
        # Handle return value
        if isinstance(ev_result, tuple):
            ev, personalized_metadata = ev_result
            distribution_info = f"**🎯 Personalized Analysis:** Based on {personalized_metadata['sample_size']} similar tournaments (Confidence: {personalized_metadata['confidence_level'].title()})"
        else:
            ev = ev_result
            personalized_metadata = None
            distribution_info = "**📊 Standard Analysis:** Using uniform probability distribution"
    else:
        # No tournament history, use uniform distribution
        ev = calculate_tournament_ev(
            num_players=int(field_size),
            buy_in=buy_in,
            num_rebuys=num_rebuys,
            rake_percent=rake_percent,
            paid_percent=paid_percent
        )
        personalized_metadata = None
        distribution_info = "**📊 Standard Analysis:** No tournament history available, using uniform probability distribution"
    
    # Get probabilities and paid positions for ITM calculation
    probabilities, num_paid = get_probabilities_for_analysis(
        field_size, buy_in, num_rebuys, addon_cost, rake_percent, paid_percent, 
        user_tournaments, format_type, buyin_range
    )
    
    # Display EV Analysis Results
    st.divider()
    st.subheader("📊 Mathematical EV Analysis")
    st.info(distribution_info)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Expected Value", f"${ev:.2f}")
    with col2:
        st.metric("Total Investment", f"${total_investment:.0f}")
    with col3:
        if probabilities is not None and num_paid is not None:
            itm_probability = sum(probabilities[:num_paid]) * 100
            st.metric("ITM Probability", f"{itm_probability:.1f}%")
        else:
            st.metric("ITM Probability", "N/A")
    with col4:
        roi_percent = calculate_roi(ev - total_investment, total_investment)
        st.metric("EV Assessment", 
                 "Positive" if roi_percent > 0 else "Negative" if roi_percent < -10 else "Marginal",
                 delta=f"{roi_percent:+.1f}%",
                 delta_color="normal")
    
    # Show personalized probability table
    create_probability_payout_table(
        field_size, buy_in, num_rebuys, addon_cost, rake_percent, paid_percent, 
        user_tournaments, format_type, buyin_range
    )
    
    # Generate AI analysis
    generate_ai_analysis(tournament_data, ev, total_investment, user_tournaments, username)


def get_probabilities_for_analysis(field_size, buy_in, num_rebuys, addon_cost, rake_percent, paid_percent, user_tournaments, format_type, buyin_range):
    """
    Get probabilities and number of paid positions for analysis calculations.
    
    Returns:
        tuple: (probabilities array, num_paid) or (None, None) if error
    """
    # Calculate number of paid positions
    num_paid = max(1, int(field_size * paid_percent))
    
    # Get user's personalized probability distribution using player_pdf
    from player import player_pdf
    probabilities, metadata = player_pdf(user_tournaments, field_size, format_type, buyin_range)
    
    return probabilities, num_paid


def create_probability_payout_table(field_size, buy_in, num_rebuys, addon_cost, rake_percent, paid_percent, user_tournaments, format_type, buyin_range):
    """
    Create a table showing payout positions, prizes, personal probabilities, and ROI.
    
    Args:
        field_size (int): Number of players
        buy_in (float): Buy-in amount
        num_rebuys (int): Number of rebuys
        addon_cost (float): Add-on cost
        rake_percent (float): Rake percentage
        paid_percent (float): Percentage of field paid
        user_tournaments (list): User's tournament history
        format_type (str): Tournament format
        buyin_range (tuple): Buy-in range for filtering
    """
    # Calculate total investment
    total_investment = calculate_total_investment(buy_in, num_rebuys, addon_cost)
    
    # Calculate number of paid positions  
    num_paid = max(1, int(field_size * paid_percent))
    
    # Basic validation
    if buy_in <= 0 or field_size <= 0 or rake_percent < 0 or rake_percent >= 1:
        st.error("Invalid tournament parameters")
        return
        
    # Get tournament structure (payout distribution) using centralized method
    from tournament import tournament_structure
    payout_table = tournament_structure(field_size, buy_in, rake_percent, paid_percent)
    prizes = payout_table['Payout ($)'].values
    
    # Get user's personalized probability distribution using player_pdf
    from player import player_pdf
    probabilities, metadata = player_pdf(user_tournaments, field_size, format_type, buyin_range)
    
    # Create payout table data
    table_data = []
    
    for position in range(1, min(num_paid + 1, len(prizes) + 1)):
        prize = prizes[position - 1] if position <= len(prizes) else 0
        probability = probabilities[position - 1] * 100  # Convert to percentage
        profit = prize - total_investment
        roi = calculate_roi(profit, total_investment)
        
        table_data.append({
            "Position": position,
            "Prize": f"${prize:,.0f}",
            "Your Probability": f"{probability:.2f}%",
            "ROI": f"{roi:+.1f}%"
        })
    
    if not table_data:
        st.error("No payout data could be generated")
        return
        
    # Display the table
    st.divider()
    st.subheader("🎯 Your Personalized Payout Probabilities")
    
    if metadata["sample_size"] > 0:
        st.info(f"Based on {metadata['sample_size']} similar tournaments from your history")
    else:
        st.info("Using uniform probability distribution (no tournament history available)")
    
    # Create DataFrame and display
    df = pd.DataFrame(table_data)
    
    # Style the dataframe for better presentation
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Position": st.column_config.NumberColumn(
                "Position",
                help="Tournament finishing position",
                format="%d"
            ),
            "Prize": st.column_config.TextColumn(
                "Prize",
                help="Prize money for this position"
            ),
            "Your Probability": st.column_config.TextColumn(
                "Your Probability",
                help="Your personal probability of finishing in this position"
            ),
            "ROI": st.column_config.TextColumn(
                "ROI",
                help="Return on Investment percentage"
            )
        }
    )


def generate_ai_analysis(tournament_data, ev, total_investment, user_tournaments, username):
    """
    Generate AI analysis for the tournament with clean UI formatting.
    
    Args:
        tournament_data (dict): Tournament parameters
        ev (float): Expected value (if calculated)
        total_investment (float): Total investment (if calculated)
        user_tournaments (list): User's tournament history
        username (str): Current username
    """
    # Create a focused query for AI analysis (without the messy data dump)
    if ev is not None and total_investment is not None:
        roi_percent = calculate_roi(ev - total_investment, total_investment)
        tournament_query = f"""Please analyze this tournament opportunity for me:

TOURNAMENT: {tournament_data['venue']} - ${tournament_data['buy_in']} {tournament_data['format_type']}
- Field Size: {tournament_data['field_size']} players
- Structure: {tournament_data['tournament_structure']}
- Total Investment: ${total_investment:.0f} (including {tournament_data['num_rebuys']} rebuys and ${tournament_data['addon_cost']} add-on)

MATHEMATICAL ANALYSIS:
- Expected Value: ${ev:.2f}
- Expected ROI: {roi_percent:+.1f}%

Based on my tournament history and this mathematical analysis, should I play this tournament? Please provide:
1. Your recommendation (Play/Don't Play) with confidence level
2. Key factors supporting your decision
3. Specific strategy adjustments for this tournament type
4. Risk assessment and bankroll considerations

Keep your response concise and actionable."""
    else:
        tournament_query = f"""Please analyze this tournament opportunity for me:

TOURNAMENT: {tournament_data['venue']} - ${tournament_data['buy_in']} {tournament_data['format_type']}
- Field Size: {tournament_data['field_size']} players
- Structure: {tournament_data['tournament_structure']}
- Rebuys: {tournament_data['rebuys_allowed']} (Expected: {tournament_data['num_rebuys']})
- Add-on: {tournament_data['addon_available']} (${tournament_data['addon_cost']})

Based on my tournament history, should I play this tournament? Please provide:
1. Your recommendation (Play/Don't Play) with confidence level
2. Key factors supporting your decision based on my historical performance
3. Specific strategy adjustments for this tournament type
4. Risk assessment and bankroll considerations

Keep your response concise and actionable."""
    
    # Initialize chat and get AI analysis
    chat_messages = initialize_chat_session(username, "Personalized Tournament Strategy Analysis", user_tournaments)
    chat_messages.append({"role": "user", "content": tournament_query})
    
    # Get AI response
    client, _ = setup_openai()
    reply = process_chat_message(client, chat_messages, username, "Personalized Tournament Strategy Analysis")
    
    if reply:
        # Display the analysis
        st.divider()
        st.subheader("🎯 AI Coach Recommendation")
        st.markdown(reply)
        
        # Option for follow-up questions
        st.divider()
        st.subheader("💬 Follow-up Questions")
        follow_up = st.text_input("Ask any follow-up questions about this analysis:", key="follow_up_question")
        if st.button("Ask Question") and follow_up:
            chat_messages.append({"role": "assistant", "content": reply})
            chat_messages.append({"role": "user", "content": follow_up})
            
            follow_reply = process_chat_message(client, chat_messages, username, "Personalized Tournament Strategy Analysis")
            
            if follow_reply:
                st.markdown("**Follow-up Answer:**")
                st.markdown(follow_reply)
                st.rerun() 