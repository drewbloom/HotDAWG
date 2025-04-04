import streamlit as st
import streamlit_authenticator as stauth
import yaml

class Authentication:
    """
    Handles user authentication, login, and registration processes.
    """

    def __init__(self, config_file='testlogin.yaml'):
        
        # MUST REFACTOR THIS TO USE STREAMLIT'S SECRETS HANDLING

        """
        Initialize authentication with configuration from the provided YAML file.

        Args:
            config_file (str): Path to the configuration YAML file.
        """
        # Use the following for a yaml file
        #with open(config_file) as file:
        #    self.config = yaml.load(file, Loader=SafeLoader)

        # Handle secrets acc. streamlit's Cloud secrets
        raw_yaml = st.secrets["authenticator"]["credentials"]
        self.config = yaml.safe_load(raw_yaml)
        
        self.authenticator = stauth.Authenticate(
            credentials=self.config
        )

        self.initialize_session_state()


    def initialize_session_state(self):
        """Initialize necessary session states to manage user interaction states."""
        st.session_state.authentication_status = st.session_state.get('authentication_status', None)
        st.session_state.show_success_message = st.session_state.get('show_success_message', False)
        st.session_state.device_flow_message = st.session_state.get('device_flow_message', False)

    def setup_login(self):
        """Create login interface and handle login events."""
        self.authenticator.login(
            location='sidebar', 
            max_login_attempts=5, 
            fields={
                'Form name': 'Log In', 
                'Username': 'Username', 
                'Password': 'Password', 
                'Login': 'Submit', 
                'Captcha': 'Captcha'
            }
        )

    def display_auth_messages(self):
        """Display messages based on the authentication status."""
        if st.session_state['authentication_status'] is False:
            st.error('Username/password is incorrect')
        elif st.session_state['authentication_status'] is None:
            st.write("# Welcome! Log in on the left to start!")
            st.sidebar.warning('Enter your username and password')
        elif st.session_state.authentication_status is True:
            st.success(f"Welcome back, {st.session_state.name}!")


    def main(self):
        """Manage authentication status and related UI elements."""

        self.setup_login()
        self.display_auth_messages()

