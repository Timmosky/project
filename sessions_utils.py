import instaloader
import os
import streamlit as st

def load_instaloader_session(username, session_path):
    L = instaloader.Instaloader()

    try:
        # Try loading saved session file
        L.load_session_from_file(username, filename=session_path)

        # Attempt to validate the session with a lightweight request
        instaloader.Profile.from_username(L.context, username)

        st.success("✅ Instagram session loaded and valid.")
        return L

    except Exception as e:
        st.error("❌ Your Instagram session is expired or invalid.")
        st.info("🔁 Please re-export your cookies and rerun the conversion script.")
        st.stop()
        return None
