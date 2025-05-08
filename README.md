AI poker coach powered by GenAI

🚀 To run it locally: (for MAC obviously)

Clone this repo.
Open your terminal and navigate to the project directory: cd path/to/your/project
Create a virtual environment: python -m venv venv
Activate the virtual environment: source venv/bin/activate
Install the Requirements in yourr virtual environment: pip install -r requirements.txt
Configure your OpenAI API key
Create a .streamlit directory: mkdir path/to/your/project/.streamlit
Inside that folder, create your secrets.toml: nano path/to/your/project/.streamlit/secrets.toml
Add your OpenAI API key to the file. Paste in: OPENAI_API_KEY = "sk-your-real-openai-key-here"
Run the app locally: streamlit run poker_chatbot.py
Open your browser to http://localhost:8501
🌐 To deploy it online:

You can use Streamlit Cloud (easy and free): 1. Push your code to a GitHub repo 2. Go to streamlit.io/cloud 3. Connect your GitHub and deploy the app 4. Add your OPENAI_API_KEY to Secrets in the Streamlit Cloud settings

Then open the URL on your iPhone and “Add to Home Screen” 📱✨
