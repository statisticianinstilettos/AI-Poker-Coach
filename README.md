# AI Poker Coach
AI poker coach powered by RL and LLMs.

Your AI Poker Coach comes with:
✅ Comprehensive tournament result tracking. 
✅ Personalized Mathematical models for expected value calculations to guide Tourmament selectionand Strategy 
✅ AI chat for personalized coaching


<p align="center">
<img src="images/blonde-poker-coach.png" width=200>
</p>

🚀 To run it locally: (for MAC obviously)
1. Clone this repo.
2. Open your terminal and navigate to the project directory: cd path/to/your/project
3. Create a virtual environment: python -m venv venv
4. Activate the virtual environment: source venv/bin/activate
5. Install the Requirements in your virtual environment: pip install -r requirements.txt
6. Configure your OpenAI API key
   - Create a .streamlit directory: mkdir path/to/your/project/.streamlit
   - Inside that folder, create your secrets.toml: nano path/to/your/project/.streamlit/secrets.toml
   - Add your OpenAI API key to the file. Paste in: OPENAI_API_KEY = "sk-your-real-openai-key-here" and your OPIK_API_KEY = "your-real-opik-key-here"
8. Run the app locally: streamlit run poker_chatbot.py
9. Open your browser to http://localhost:8501



⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻
🎯 Test Questions for AI Poker Coach

1. Preflop Ranges

“I’m in the cutoff with A♠️9♦️ in a 6-max cash game. Everyone folded to me. Should I open? What are the risks?”

🧪 Tests: GTO opening ranges, position-based advice, clarity on risk/reward

⸻

2. Equity + Math Mode

“I have 10♠️J♠️ on a flop of Q♠️9♦️2♣️. My opponent bets pot. How much equity do I need to call, and do I have it?”

🧮 Tests: Pot odds, equity math, outs, structured response with numbers

⸻

3. Exploitative Strategy

“Villain is super tight postflop. I have A♦️K♦️ and flop is 4♠️8♣️K♣️. Should I slowplay?”

🎭 Tests: Adjusting strategy based on opponent profile (exploitative logic)

⸻

4. Hand History Review

“I raised preflop with Q♣️Q♦️, got called by big blind. Flop is K♠️7♣️3♠️. BB checks, I c-bet small, BB raises big. What now?”

🧐 Tests: Reading ranges, explaining pressure spots, conciseness, tone

⸻

5. Tournament ICM Pressure

“I’m on the bubble of a $100 MTT. 12bb in the big blind. Button shoves 20bb. I have A♥️9♥️. Everyone else folded. What’s the play?”

🧠 Tests: Tournament dynamics, ICM pressure, push/fold logic
