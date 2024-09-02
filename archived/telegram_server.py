import telebot
import supabase_controller as db
import streamlit as st

# Initialize the bot with your token
API_TOKEN = st.secrets["TELEGRAM_BOT_API_TOKEN"]
bot = telebot.TeleBot(API_TOKEN)

# Function to send a message
def send_message(chat_id=27392018, message="Hi there!"):
    print("Sending Message..")
    bot.send_message(chat_id, message)

@bot.message_handler(commands=['linkaccount'])
def print_overview(message):
    # Prompt user to input their user_id in telegram
    sent_msg = bot.send_message(message.chat.id, "Please enter your Optilens user_id to link your account.")
    bot.register_next_step_handler(sent_msg, link_optilens_account) #Next message will call the name_handler function

def link_optilens_account(message):
    user_id = message.text
    user_data = db.fetch_user_data(user_id)
    if user_data.get('user') is None:
        bot.send_message(message.chat.id, "User not found. Please try again.")
        print("User not found. Please login again")
    else:
        bot.send_message(message.chat.id, "User found. Account linked successfully.")
        print("User found. Account linked successfully")
        db.update_telegram_chat_id(user_id, message.chat.id)

bot.polling()
