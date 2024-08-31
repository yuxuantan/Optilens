from supabase import create_client, Client
import streamlit as st

# response = supabase.table("countries").select("*").execute()

def fetch_alerts():
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)

    try:
        response = supabase.table("alerts").select("*").execute()
        return response.data
    except Exception as e:
        st.error("Error fetching alerts:")
        st.error(str(e))
        
def create_user(email: str) -> str:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)

    try:
        response = supabase.table("users").insert({"email": email}).execute()
        st.write("User created successfully!")
        st.write(response)
        return response.data[0]["user_id"]  # Return the user_id
    except Exception as e:
        st.error("Error creating user:")
        st.error(str(e))


def update_telegram_chat_id(user_id: str, telegram_id: str) -> None:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)

    try:
        response = (
            supabase.table("users")
            .update({"telegram_user_chat_id": telegram_id})
            .eq("user_id", user_id)
            .execute()
        )
        st.write("User updated successfully!")
        st.write(response)
    except Exception as e:
        st.error("Error updating user:")
        st.error(str(e))


def fetch_user_data(user_id: str) -> dict:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)

    user = None
    alerts = None
    try:
        response = supabase.table("users").select("*").eq("user_id", user_id).execute()
        if response.data:
            user = response.data[0]
    except Exception as e:
        st.error("Error fetching user data:")
        st.error(str(e))

    try:
        response = (
            supabase.table("alerts")
            .select("*")
            .eq("creator_user_id", user_id)
            .execute()
        )
        if response.data:
            alerts = response.data
    except Exception as e:
        st.error("Error fetching user alerts:")
        st.error(str(e))

    return {"user": user, "alerts": alerts}


def update_user_alert(creator_user_id: str, alert_name: str, settings: dict) -> None:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)

    try:
        supabase.table("alerts").update({"settings": settings}).eq("alert_name", alert_name).eq("creator_user_id", creator_user_id).execute()
        st.write("Alert updated successfully!")
    except Exception as e:
        st.error("Error updating user alert:")
        st.error(str(e))


def create_user_alert(creator_user_id: str, alert_name: str, settings: dict) -> None:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)

    try:
        supabase.table("alerts").insert(
            {
                "creator_user_id": creator_user_id,
                "alert_name": alert_name,
                "settings": settings,
            }
        ).execute()

    except Exception as e:
        st.error("Error creating user alert:")
        st.error(str(e))


def delete_user_alert(
    creator_user_id: str,
    alert_name: str,
) -> None:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)

    try:
        supabase.table("alerts").delete().eq("creator_user_id", creator_user_id).eq(
            "alert_name", alert_name
        ).execute()

    except Exception as e:
        st.error("Error deleting user alert:")
        st.error(str(e))
