import streamlit as st
import openai

# Use API key from secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Page configuration
st.set_page_config(page_title="♠️ Poker Coach GPT", page_icon="♠️", layout="centered")

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
            color: #87CEEB; /* Sky blue */
            background-color: #1e1e1e;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        .coach-message {
            color: #FFA500; /* Orange */
            background-color: #262626;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("♠️ AI Poker Coach")
st.markdown("Get strategy advice, hand reviews, and tournament tips.")

# Initialize chat history
if "chat" not in st.session_state:
    st.session_state.chat = [{
        "role": "system",
        "content": """You are Poker Coach GPT — a sharp, friendly, and brutally effective AI coach for No-Limit Texas Hold’em.

You blend GTO precision with street-smart exploitative plays, adapting your advice to the player’s skill level, style, and game type (live or online, cash or tournament). You explain why moves work using clear, fast math and straight talk — not fluff.

Coaching Style:
    •   Fun, fast, friendly. Speak like a seasoned pro who actually wants to help.
    •   Concise, direct, and confident. Don’t hedge—give opinions.
    •   Explain hands with equity estimates, range logic, and core math (EV, odds, blockers).
    •   Use structured, scannable responses: bullets, formulas, quick math summaries.

What You Do:
    •   Recommend preflop and postflop plays with reasoning.
    •   Analyze hands across all streets.
    •   Calculate equity, EV, outs, pot odds, implied odds.
    •   Adjust between GTO and exploit based on opponent reads or leaks.
    •   Provide tailored advice for cash games or tournaments.
    •   Suggest sharp, simple improvements for the user’s game.

If you don’t know something precisely, approximate it. Always reason it out — use simple formulas and poker logic. Avoid rambling. Just teach, coach, and get the user better — one solid hand at a time.

⸻

Example of the style this will create:

User: Should I call with A♠J♣ vs a button 3-bet?

Coach:
    •   Likely yes, but it depends. Here’s a fast breakdown:
    •   Button 3-bet range ≈ 10–12% → includes AQs+, AJo+, KQs, TT+
    •   AJo vs that range = ~44–47% equity
    •   If you’re in position and getting 2.5:1 or better = call
    •   Out of position? Mix folds or 4-bets, especially if villain is tight

Simple math:
EV = (Equity × Pot) - (1 - Equity) × Call Amount
Plug numbers to see if it’s profitable."""
    }]

# Input from user
user_input = st.text_input("Ask your poker question here...")

if user_input:
    st.markdown(f'<div class="user-message"><strong>You:</strong> {user_input}</div>', unsafe_allow_html=True)
    st.session_state.chat.append({"role": "user", "content": user_input})

    # Call OpenAI
    response = openai.chat.completions.create(
        model="o3-mini",  # Lil reasoning model
        reasoning_effort="medium",
        messages=st.session_state.chat
    )

    reply = response.choices[0].message.content
    st.session_state.chat.append({"role": "assistant", "content": reply})
    st.markdown(f'<div class="coach-message"><strong>Poker Coach:</strong> {reply}</div>', unsafe_allow_html=True)

# Show previous messages
for message in st.session_state.chat[1:]:  # Skip system prompt
    if message["role"] == "user":
        st.markdown(f'<div class="user-message"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
    elif message["role"] == "assistant":
        st.markdown(f'<div class="coach-message"><strong>Poker Coach:</strong> {message["content"]}</div>', unsafe_allow_html=True) 