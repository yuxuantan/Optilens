import streamlit as st
import utils.supabase as db
import time

def protect_page():
    st.title("Login")
    st.write("Please enter your User ID to proceed.")

    user_id_input = st.text_input("User ID")
    if st.button("Login"):
        if user_id_input:
            # Redirect to the main app with the user_id in query parameters
            st.query_params["user_id"]=user_id_input
            time.sleep(0.1) # add delay to ensure the query params is set before rerun
            st.rerun()
        else:
            st.warning("User ID cannot be empty.")

    st.divider()
    st.title("Sign Up")
    email = st.text_input("Email Address")
    if st.button("Sign Up"):
        # simulate sign up successful after payment. create new user and login
        user_id = db.create_user(email)
        if user_id:
            st.query_params.user_id=user_id
            time.sleep(0.1) # add delay to ensure the query params is set before rerun
            st.rerun()
            
