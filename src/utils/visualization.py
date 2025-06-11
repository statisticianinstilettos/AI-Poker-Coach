"""
Visualization utilities for Poker Coach application.
Handles chart generation and plotting functionality.
"""

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import sys
import os

# Add src/player_model to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../player_model'))

from src.config import PLOT_FIELD_SIZE, PLOT_FIGSIZE, PLOT_COLORS


def create_player_pdf_plot(tournament_results, username):
    """
    Create a matplotlib plot of the user's personalized probability distribution.
    
    Args:
        tournament_results (list): User's tournament history
        username (str): Username for plot title
        
    Returns:
        tuple: (matplotlib.figure.Figure, dict) or (None, None) if error
    """
    if not tournament_results or len(tournament_results) < 3:
        return None, None
    
    from player import player_pdf
    
    # Get personalized distribution
    probabilities, metadata = player_pdf(tournament_results, PLOT_FIELD_SIZE)
    
    # Create the plot
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=PLOT_FIGSIZE)
    
    # Create positions as percentiles for better readability
    positions = np.arange(1, PLOT_FIELD_SIZE + 1)
    percentiles = positions / PLOT_FIELD_SIZE * 100
    
    # Plot the distribution
    ax.plot(percentiles, probabilities * 100, 
           color=PLOT_COLORS['primary'], linewidth=2, alpha=0.8)
    ax.fill_between(percentiles, probabilities * 100, 
                   alpha=0.3, color=PLOT_COLORS['primary'])
    
    # Customize the plot
    ax.set_xlabel('Finish Percentile (%)', color='white', fontsize=10)
    ax.set_ylabel('Probability (%)', color='white', fontsize=10)
    ax.set_title(f'{username}\'s Performance Distribution\n({metadata["sample_size"]} tournaments)', 
                color=PLOT_COLORS['primary'], fontsize=12, fontweight='bold')
    
    # Add grid
    ax.grid(True, alpha=0.3, color='white')
    
    # Set background color
    fig.patch.set_facecolor(PLOT_COLORS['background'])
    ax.set_facecolor(PLOT_COLORS['background'])
    
    # Color the axes
    ax.tick_params(colors='white', labelsize=8)
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Add expected finish line
    expected_percentile = metadata['expected_finish_position'] / PLOT_FIELD_SIZE * 100
    ax.axvline(expected_percentile, color=PLOT_COLORS['secondary'], 
              linestyle='--', alpha=0.8, linewidth=1)
    ax.text(expected_percentile + 2, max(probabilities * 100) * 0.8, 
           f'Expected: {expected_percentile:.0f}%', 
           color=PLOT_COLORS['secondary'], fontsize=8, rotation=90)
    
    # Tight layout
    plt.tight_layout()
    
    return fig, metadata


def display_user_performance_plot(user_tournament_data, username):
    """
    Display the user's performance distribution plot in the sidebar.
    
    Args:
        user_tournament_data (list): User's tournament history
        username (str): Username for display
    """
    if user_tournament_data and len(user_tournament_data) >= 3:
        fig, metadata = create_player_pdf_plot(user_tournament_data, username)
        if fig and metadata:
            st.sidebar.subheader("📊 Your Performance Distribution")
            st.sidebar.pyplot(fig, use_container_width=True)
            plt.close(fig)  # Clean up to prevent memory issues
            
            # Add small explanation
            st.sidebar.caption(
                f"Based on {metadata['sample_size']} tournaments • "
                f"{metadata['confidence_level'].title()} confidence"
            ) 