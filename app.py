import sys
import os

# Add the root directory (AffinityAssist) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from auth import Authentication  # Import the Authentication class
from hotdawg import HotDawg

### NEXT STEPS:
# Add modular agents in addition to Graph API Agent: Teamwork API, NetDocuments API
# Capture refresh tokens to use for future auth in stable state beyond sessions (yaml field?)

# Load environment variables
# load_dotenv()
# OPENAI_API_KEY = os.getenv('AFFINITY_OPENAI_API_KEY')

# Use streamlit secrets implementation
OPENAI_API_KEY = st.secrets["openai"]["api_key"]

def main():
    # Initialize the Authentication class
    auth = Authentication()

    # Handle Streamlit login and registration
    auth.main()

    # If user is authenticated, proceed with application logic
    if st.session_state.get('authentication_status') == True:
        

        client = OpenAI(api_key=OPENAI_API_KEY)
        HotDawgClient = HotDawg(client)
        
        # Here we assume AffinityAssist has methods to manage UI and functionality
        HotDawgClient.main()

if __name__ == "__main__":
    main()