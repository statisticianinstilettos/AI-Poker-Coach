"""
Tournament display module for Poker Coach application.
Handles tournament results viewing, editing, and deletion.
"""

import streamlit as st
import pandas as pd
from src.utils.calculations import calculate_profit_loss, calculate_roi
from src.forms.tournament_forms import create_tournament_entry_form
from database import (
    get_user_tournament_results, delete_single_tournament_result, 
    delete_user_tournament_results
)


def display_tournament_results(username):
    """
    Display tournament results table with edit/delete functionality and add new option.
    
    Args:
        username (str): Current username
    """
    st.subheader("📊 Your Tournament Results")
    
    # Add New Tournament button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("➕ Add New Tournament", type="primary"):
            st.session_state.show_add_form = True
    
    # Show add tournament form if requested
    if st.session_state.get('show_add_form', False):
        st.divider()
        st.subheader("➕ Add New Tournament Result")
        
        # Create the form and check if it was submitted successfully
        form_submitted = create_tournament_entry_form()
        
        if form_submitted:
            # Clear the form state and rerun to show updated results
            st.session_state.show_add_form = False
            st.rerun()
        
        # Cancel button
        if st.button("❌ Cancel", key="cancel_add_form"):
            st.session_state.show_add_form = False
            st.rerun()
        
        st.divider()
    
    try:
        tournament_results = get_user_tournament_results(username)
        
        if tournament_results:
            # Table header - simplified 6 columns
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
            
            # Display each tournament as a row
            for i, result in enumerate(tournament_results):
                delete_confirm_key = f"delete_confirm_{i}"
                
                if st.session_state.get(delete_confirm_key, False):
                    # Show delete confirmation
                    confirm_cols = st.columns([1.5, 7])
                    with confirm_cols[0]:
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("✅", key=f"confirm_delete_{i}", help="Confirm delete"):
                                try:
                                    deleted_count = delete_single_tournament_result(str(result['_id']), username)
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
                    # Normal row display
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
                
                # Add separator between rows
                st.markdown("<hr style='margin: 10px 0; border: 0.5px solid #333;'>", unsafe_allow_html=True)
            
            # CSV export functionality
            st.divider()
            export_data = create_export_data(tournament_results)
            export_df = pd.DataFrame(export_data)
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name=f"tournament_results_{username}.csv",
                mime="text/csv"
            )
            
            # Data management section
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
                                deleted_count = delete_user_tournament_results(username)
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
            st.info("📝 No tournament results found. Click 'Add New Tournament' above to add your first tournament.")
            
    except Exception as e:
        st.error(f"Error loading tournament results: {str(e)}")
        st.info("💡 If you're seeing this error, the database connection might not be working. Tournament results will be available once the database is connected.")


def create_export_data(tournament_results):
    """
    Create export data for CSV download.
    
    Args:
        tournament_results (list): List of tournament results
        
    Returns:
        list: Formatted data for export
    """
    export_data = []
    for result in tournament_results:
        profit_loss = calculate_profit_loss(result['prize_won'], result['total_investment'])
        roi = calculate_roi(profit_loss, result['total_investment'])
        
        export_data.append({
            'Date': result['tournament_date'],
            'Venue': result['venue'],
            'Format': result['format'],
            'Buy-in': result['buy_in'],
            'Rebuys': result.get('rebuys', 0),
            'Add-on Cost': result.get('add_on_cost', 0),
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
    
    return export_data 