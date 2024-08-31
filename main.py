import streamlit as st
from stock_screener_page import stock_screener_page
import controllers.supabase_controller as db
# Get the user_id from URL query parameters

user_id = st.query_params["user_id"] if "user_id" in st.query_params else None

# If user_id is not provided in the URL, show the login page
if not user_id:
    st.title("Login")
    st.write("Please enter your User ID to proceed.")
    
    user_id_input = st.text_input("User ID")
    if st.button("Login"):
        if user_id_input:
            # Redirect to the main app with the user_id in query parameters
            st.query_params.user_id=user_id_input
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
            st.rerun()
         
else:
    # Check if user exists on DB. if not, show login page
    user_id = st.query_params.user_id
    user_data = db.fetch_user_data(user_id)
    if user_data.get('user') is None:
        st.warning("User not found. Please login again.")
        print("User not found. Please login again")
        st.query_params.clear()
        st.rerun()

    stock_screener_page(user_data)
