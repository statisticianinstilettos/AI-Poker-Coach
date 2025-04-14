# AI Poker Coach
AI poker coach powered by RL and LLMs 



🚀 To run it locally: (for MAC obviously)
1. Clone this repo.
2. Open your terminal and navigate to the project directory: cd path/to/your/project
3. Create a virtual environment: python -m venv venv
4. Activate the virtual environment: source venv/bin/activate
5. Install the Requirements in yourr virtual environment: pip install -r requirements.txt
6. Configure your OpenAI API key
   - Create a .streamlit directory: mkdir path/to/your/project/.streamlit
   - Inside that folder, create your secrets.toml: nano path/to/your/project/.streamlit/secrets.toml
   - Add your OpenAI API key to the file. Paste in: OPENAI_API_KEY = "sk-your-real-openai-key-here"
8. Run the app locally: streamlit run poker_chatbot.py
9. Open your browser to http://localhost:8501



🌐 To deploy it online:

You can use Streamlit Cloud (easy and free):
	1.	Push your code to a GitHub repo
	2.	Go to streamlit.io/cloud
	3.	Connect your GitHub and deploy the app
	4.	Add your OPENAI_API_KEY to Secrets in the Streamlit Cloud settings

Then open the URL on your iPhone and “Add to Home Screen” 📱✨


