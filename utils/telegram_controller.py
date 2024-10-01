import telebot
import streamlit as st
# Initialize the bot with your token

import os

try:
    bot = telebot.TeleBot(st.secrets["TELEGRAM_BOT_API_TOKEN"])
except FileNotFoundError:
    bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_API_TOKEN"))

# Function to send a message
def send_message(chat_ids=[27392018], message="Hi there!"):
    for chat_id in chat_ids:
        bot.send_message(chat_id, message, parse_mode= 'Markdown')
