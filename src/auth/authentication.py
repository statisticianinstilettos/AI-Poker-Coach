"""
Authentication module for Poker Coach application.
Handles user login, logout, and session management.
"""

import streamlit as st
import streamlit_authenticator as stauth


def setup_authentication():
    """
    Initialize authentication configuration and authenticator.
    
    Returns:
        stauth.Authenticate: Configured authenticator instance
    """
    config = {
        'cookie': {
            'expiry_days': 30,
            'key': st.secrets["cookie_key"],
            'name': 'poker_coach_cookie'
        },
        'credentials': {
            'usernames': st.secrets["credentials"]["usernames"]
        }
    }
    
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        auto_hash=False
    )
    
    return authenticator


def initialize_session_state():
    """Initialize authentication session state variables."""
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = None
    if 'username' not in st.session_state:
        st.session_state['username'] = None


def handle_authentication():
    """
    Handle the complete authentication flow.
    
    Returns:
        bool: True if user is authenticated, False otherwise
    """
    authenticator = setup_authentication()
    initialize_session_state()
    
    try:
        authenticator.login(location='main')
        
        if st.session_state['authentication_status']:
            authenticator.logout('Logout', location='sidebar')
            return True
        elif st.session_state['authentication_status'] == False:
            st.error('Username/password is incorrect')
        elif st.session_state['authentication_status'] == None:
            st.warning('Please enter your username and password')
        
        return False
        
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False


def get_current_username():
    """
    Get the current authenticated username.
    
    Returns:
        str: Current username or None if not authenticated
    """
    return st.session_state.get('username')


def is_authenticated():
    """
    Check if user is currently authenticated.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    return st.session_state.get('authentication_status') == True 