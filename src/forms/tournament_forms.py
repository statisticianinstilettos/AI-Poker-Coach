"""
Tournament forms module for Poker Coach application.
Handles tournament entry, editing, and analysis forms.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from src.config import (
    TOURNAMENT_STRUCTURES, ANTE_STRUCTURES, FORMATS, 
    REBUY_OPTIONS, ADDON_OPTIONS, DEFAULT_BUY_IN, 
    DEFAULT_FIELD_SIZE, DEFAULT_STARTING_STACK, 
    DEFAULT_LEVEL_TIME, DEFAULT_RAKE_PERCENT, DEFAULT_PAID_PERCENT
)
from src.utils.calculations import calculate_total_investment
from database import (
    save_tournament_result, update_tournament_result, 
    get_single_tournament_result
)


def create_tournament_entry_form():
    """
    Create tournament entry form for saving results.
    
    Returns:
        bool: True if form was submitted successfully, False otherwise
    """
    with st.form("tournament_result"):
        st.subheader("Enter Tournament Result")
        
        col1, col2 = st.columns(2)
        with col1:
            venue = st.text_input("Venue/Location", placeholder="e.g., Bellagio, PokerStars, Borgata")
            format_type = st.selectbox("Format", FORMATS)
            tournament_date = st.date_input("Tournament Date")
            buy_in = st.number_input("Buy-in Amount ($)", min_value=0.0, step=1.0)
            rebuys = st.number_input("Number of Rebuys", min_value=0, step=1)
            add_on_cost = st.number_input("Add-on ($)", min_value=0.0, step=1.0, help="Total amount spent on add-ons")
            total_entries = st.number_input("Total Entries", min_value=1, step=1, help="Total number of players in the tournament")
        
        with col2:
            position = st.number_input("Position Finished", min_value=1, step=1)
            prize = st.number_input("Prize Won ($)", min_value=0.0, step=1.0)
            duration = st.number_input("Duration (hours)", min_value=0.0, step=0.5)
            
            # Tournament Structure
            st.subheader("Tournament Structure")
            tournament_structure = st.selectbox("Tournament Structure", TOURNAMENT_STRUCTURES)
            starting_stack = st.number_input("Starting Chip Stack", min_value=1000, step=1000, value=DEFAULT_STARTING_STACK, help="Starting chips (e.g., 20,000)")
            ante_structure = st.selectbox("Ante Structure", ANTE_STRUCTURES)
            level_time = st.number_input("Level Time (minutes)", min_value=5, step=5, value=DEFAULT_LEVEL_TIME, help="Length of each blind level in minutes")
        
        notes = st.text_area("Tournament Notes", placeholder="Any additional notes about this tournament")
        
        submitted = st.form_submit_button("Save Tournament Result")
        
        if submitted:
            if not venue:
                st.error("Please enter a venue name")
                return False
            
            total_investment = calculate_total_investment(buy_in, rebuys, add_on_cost)
            tournament_data = {
                "venue": venue,
                "format": format_type,
                "tournament_date": tournament_date.strftime("%Y-%m-%d"),
                "buy_in": buy_in,
                "rebuys": rebuys,
                "add_on_cost": add_on_cost,
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
                return True
            except Exception as e:
                st.error(f"Error saving tournament result: {str(e)}")
                return False
    
    return False


def create_tournament_edit_form(tournament_id, username):
    """
    Create tournament edit form for modifying existing tournaments.
    
    Args:
        tournament_id (str): ID of tournament to edit
        username (str): Current username
        
    Returns:
        bool: True if form was submitted successfully, False otherwise
    """
    tournament_to_edit = get_single_tournament_result(tournament_id, username)
    if not tournament_to_edit:
        st.error("Tournament not found")
        return False
    
    st.subheader("✏️ Edit Tournament Result")
    
    with st.form("edit_tournament_result"):
        col1, col2 = st.columns(2)
        with col1:
            venue = st.text_input("Venue/Location", value=tournament_to_edit.get('venue', ''), placeholder="e.g., Bellagio, PokerStars, Borgata")
            format_type = st.selectbox("Format", FORMATS, index=0 if tournament_to_edit.get('format') == 'Live' else 1)
            tournament_date = st.date_input("Tournament Date", value=pd.to_datetime(tournament_to_edit.get('tournament_date')).date() if tournament_to_edit.get('tournament_date') else None)
            buy_in = st.number_input("Buy-in Amount ($)", min_value=0.0, step=1.0, value=float(tournament_to_edit.get('buy_in', 0)))
            rebuys = st.number_input("Number of Rebuys", min_value=0, step=1, value=int(tournament_to_edit.get('rebuys', 0)))
            add_on_cost = st.number_input("Add-on ($)", min_value=0.0, step=1.0, value=float(tournament_to_edit.get('add_on_cost', 0)), help="Total amount spent on add-ons")
            total_entries = st.number_input("Total Entries", min_value=1, step=1, value=int(tournament_to_edit.get('total_entries', 1)), help="Total number of players in the tournament")
        
        with col2:
            position = st.number_input("Position Finished", min_value=1, step=1, value=int(tournament_to_edit.get('position_finished', 1)))
            prize = st.number_input("Prize Won ($)", min_value=0.0, step=1.0, value=float(tournament_to_edit.get('prize_won', 0)))
            duration = st.number_input("Duration (hours)", min_value=0.0, step=0.5, value=float(tournament_to_edit.get('duration_hours', 0)))
            
            # Tournament Structure
            st.subheader("Tournament Structure")
            current_structure = tournament_to_edit.get('tournament_structure', 'Multi-Table Tournament (MTT)')
            structure_index = TOURNAMENT_STRUCTURES.index(current_structure) if current_structure in TOURNAMENT_STRUCTURES else 0
            tournament_structure = st.selectbox("Tournament Structure", TOURNAMENT_STRUCTURES, index=structure_index)
            
            starting_stack = st.number_input("Starting Chip Stack", min_value=1000, step=1000, value=int(tournament_to_edit.get('starting_stack', DEFAULT_STARTING_STACK)), help="Starting chips (e.g., 20,000)")
            
            current_ante = tournament_to_edit.get('ante_structure', 'No Ante')
            ante_index = ANTE_STRUCTURES.index(current_ante) if current_ante in ANTE_STRUCTURES else 0
            ante_structure = st.selectbox("Ante Structure", ANTE_STRUCTURES, index=ante_index)
            
            level_time = st.number_input("Level Time (minutes)", min_value=5, step=5, value=int(tournament_to_edit.get('level_time_minutes', DEFAULT_LEVEL_TIME)), help="Length of each blind level in minutes")
        
        notes = st.text_area("Tournament Notes", value=tournament_to_edit.get('notes', ''), placeholder="Any additional notes about this tournament")
        
        col_save, col_cancel = st.columns(2)
        with col_save:
            save_clicked = st.form_submit_button("💾 Save Changes", type="primary")
        with col_cancel:
            cancel_clicked = st.form_submit_button("❌ Cancel")
        
        if cancel_clicked:
            if 'edit_tournament_id' in st.session_state:
                del st.session_state.edit_tournament_id
            st.rerun()
            return False
        
        if save_clicked:
            if not venue:
                st.error("Please enter a venue name")
                return False
            
            total_investment = calculate_total_investment(buy_in, rebuys, add_on_cost)
            updated_tournament_data = {
                "venue": venue,
                "format": format_type,
                "tournament_date": tournament_date.strftime("%Y-%m-%d"),
                "buy_in": buy_in,
                "rebuys": rebuys,
                "add_on_cost": add_on_cost,
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
                update_tournament_result(tournament_id, username, updated_tournament_data)
                st.success("Tournament result updated successfully!")
                if 'edit_tournament_id' in st.session_state:
                    del st.session_state.edit_tournament_id
                st.rerun()
                return True
            except Exception as e:
                st.error(f"Error updating tournament result: {str(e)}")
                return False
    
    return False


def create_tournament_analysis_form():
    """
    Create tournament analysis form for analyzing potential tournaments.
    
    Returns:
        dict or None: Tournament data if form submitted, None otherwise
    """
    with st.form("tournament_analysis"):
        st.subheader("Tournament Structure")
        
        col1, col2 = st.columns(2)
        with col1:
            venue = st.text_input("Venue/Location*", placeholder="e.g., Bellagio, PokerStars, Borgata")
            buy_in = st.number_input("Buy-in Amount ($)*", min_value=0.0, step=1.0, value=DEFAULT_BUY_IN)
            format_type = st.selectbox("Format*", FORMATS)
            field_size = st.number_input("Total Entries*", min_value=1, step=1, value=DEFAULT_FIELD_SIZE, help="Expected number of players in the tournament")
        
        with col2:
            tournament_structure = st.selectbox("Tournament Structure", TOURNAMENT_STRUCTURES)
            starting_stack = st.number_input("Starting Chip Stack", min_value=1000, step=1000, value=DEFAULT_STARTING_STACK, help="Starting chips (e.g., 20,000)")
            ante_structure = st.selectbox("Ante Structure", ANTE_STRUCTURES)
            level_time = st.number_input("Level Time (minutes)", min_value=5, step=5, value=DEFAULT_LEVEL_TIME, help="Length of each blind level in minutes")
            rake_percent = st.number_input("Rake Percentage (%)", min_value=0.0, max_value=50.0, step=0.5, value=DEFAULT_RAKE_PERCENT, help="Tournament rake percentage (typically 10-15%)")
            paid_percent = st.number_input("Players Paid (%)", min_value=1.0, max_value=100.0, step=1.0, value=DEFAULT_PAID_PERCENT, help="Percentage of field that gets paid (typically 10-20%)")
            
            # Rebuy/Add-on Details
            rebuys_allowed = st.selectbox("Rebuys Allowed?", REBUY_OPTIONS)
            
            # Conditional rebuy details
            num_rebuys = 0
            if rebuys_allowed != "No":
                num_rebuys = st.number_input("Number of Rebuys", min_value=0, step=1, value=1, help="How many rebuys do you typically use?")
            
            addon_available = st.selectbox("Add-on Available?", ADDON_OPTIONS)
            addon_cost = 0
            if addon_available == "Yes":
                addon_cost = st.number_input("Add-on ($)", min_value=0.0, step=1.0, value=buy_in, help="Cost of the add-on (often same as buy-in)")
        
        other_details = st.text_area("Tournament Notes", placeholder="Any other relevant info about this tournament")
        
        st.markdown("*Required fields")
        
        submitted = st.form_submit_button("🎯 Get My Tournament Analysis & EV Calculation", type="primary")
        
        if submitted:
            if not venue or buy_in <= 0 or field_size <= 0:
                st.error("Please fill in the required fields: Venue, Buy-in Amount, and Field Size")
                return None
            
            return {
                'venue': venue,
                'buy_in': buy_in,
                'format_type': format_type,
                'field_size': field_size,
                'tournament_structure': tournament_structure,
                'starting_stack': starting_stack,
                'ante_structure': ante_structure,
                'level_time': level_time,
                'rake_percent': rake_percent,
                'paid_percent': paid_percent,
                'rebuys_allowed': rebuys_allowed,
                'num_rebuys': num_rebuys,
                'addon_available': addon_available,
                'addon_cost': addon_cost,
                'other_details': other_details
            }
    
    return None 