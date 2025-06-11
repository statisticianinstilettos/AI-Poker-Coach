"""
Sidebar UI components for Poker Coach application.
Handles user stats display and performance visualization.
"""

import streamlit as st
from database import get_user_stats, get_user_tournament_results
from src.utils.visualization import display_user_performance_plot


def display_welcome_header(username):
    """
    Display welcome header in sidebar.
    
    Args:
        username (str): Current username
    """
    st.sidebar.title(f'Welcome {username}')


def display_user_stats(username):
    """
    Display user statistics in sidebar.
    
    Args:
        username (str): Current username
    """
    user_stats = get_user_stats(username)
    if user_stats:
        st.sidebar.subheader("Your Tournament Stats")
        st.sidebar.metric("Total Tournaments", user_stats["total_tournaments"])
        st.sidebar.metric("ROI", f"{user_stats['roi']:.1f}%")
        st.sidebar.metric("ITM %", f"{user_stats['itm_percentage']:.1f}%")
        st.sidebar.metric("Total Profit", f"${user_stats['total_profit']:,.2f}")


def display_performance_visualization(username):
    """
    Display performance distribution chart in sidebar.
    
    Args:
        username (str): Current username
    """
    user_tournament_data = get_user_tournament_results(username)
    display_user_performance_plot(user_tournament_data, username)


def setup_sidebar(username):
    """
    Set up complete sidebar with welcome, stats, and visualization.
    
    Args:
        username (str): Current username
    """
    display_welcome_header(username)
    display_user_stats(username)
    display_performance_visualization(username) 