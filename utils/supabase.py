from supabase import create_client, Client
import streamlit as st

# response = supabase.table("countries").select("*").execute()


def fetch_configs():
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)

    try:
        response = supabase.table("saved_configs").select("*").execute()
        return response.data
    except Exception as e:
        st.error("Error fetching configs:")
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
    configs = None
    try:
        response = supabase.table("users").select("*").eq("user_id", user_id).execute()
        if response.data:
            user = response.data[0]
    except Exception as e:
        st.error("Error fetching user data:")
        st.error(str(e))

    try:
        response = (
            supabase.table("saved_configs")
            .select("*")
            .eq("creator_user_id", user_id)
            .execute()
        )
        if response.data:
            configs = response.data
    except Exception as e:
        st.error("Error fetching user saved configs:")
        st.error(str(e))

    return {"user": user, "configs": configs}


def update_user_config(creator_user_id: str, config_name: str, settings: dict) -> None:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)

    try:
        supabase.table("saved_configs").update({"settings": settings}).eq(
            "config_name", config_name
        ).eq("creator_user_id", creator_user_id).execute()
        st.success("Filter updated successfully!")
    except Exception as e:
        st.error("Error updating user config:")
        st.error(str(e))


def create_user_config(creator_user_id: str, config_name: str, settings: dict) -> None:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    print(creator_user_id)
    # check if filter with the same creator_user_id and filter_name exists. Throw error if it does
    try:
        response = (
            supabase.table("saved_configs")
            .select("*")
            .eq("creator_user_id", creator_user_id)
            .eq("config_name", config_name)
            .execute()
        )
        if response.data:
            st.error(
                "Filter with the same name already exists. Please choose a different name."
            )
            return
        else:
            supabase.table("saved_configs").insert(
                {
                    "creator_user_id": creator_user_id,
                    "config_name": config_name,
                    "settings": settings,
                }
            ).execute()
            st.success(f"Config {config_name} saved successfully!")

    except Exception as e:
        st.error("Error fetching user filters:")
        st.error(str(e))


def delete_user_config(
    creator_user_id: str,
    filter_name: str,
) -> None:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)

    try:
        supabase.table("saved_configs").delete().eq("creator_user_id", creator_user_id).eq(
            "config_name", filter_name
        ).execute()

    except Exception as e:
        st.error("Error deleting user saved config:")
        st.error(str(e))
