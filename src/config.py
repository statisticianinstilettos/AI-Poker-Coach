"""
Configuration constants for the Poker Coach application.
"""

# UI Constants
PAGE_TITLE = "♠️ Poker Coach GPT"
PAGE_ICON = "♠️"

# Tournament Structure Options
TOURNAMENT_STRUCTURES = [
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

# Ante Structure Options
ANTE_STRUCTURES = [
    "No Ante",
    "Ante Later Levels", 
    "Ante All Levels"
]

# Format Options
FORMATS = ["Live", "Online"]

# Rebuy Options
REBUY_OPTIONS = ["No", "Yes - Limited", "Yes - Unlimited"]

# Add-on Options
ADDON_OPTIONS = ["No", "Yes"]

# Default Values
DEFAULT_BUY_IN = 100.0
DEFAULT_FIELD_SIZE = 100
DEFAULT_STARTING_STACK = 20000
DEFAULT_LEVEL_TIME = 20
DEFAULT_RAKE_PERCENT = 10.0
DEFAULT_PAID_PERCENT = 15.0

# Visualization Constants
PLOT_FIELD_SIZE = 100
PLOT_FIGSIZE = (6, 4)
PLOT_COLORS = {
    'primary': '#FFA500',
    'secondary': '#87CEEB',
    'background': '#0E1117'
}

# OpenAI Model Configuration
OPENAI_MODEL = "o3-mini"
REASONING_EFFORT = "medium"

# CSS Styling
DARK_THEME_CSS = """
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
""" 