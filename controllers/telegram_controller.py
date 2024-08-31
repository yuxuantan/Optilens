import telebot
import streamlit as st
# Initialize the bot with your token
bot = telebot.TeleBot(st.secrets["TELEGRAM_BOT_API_TOKEN"])

# Function to send a message
def send_message(chat_id, message="Hi there!"):
    bot.send_message(chat_id, message, parse_mode= 'Markdown')
