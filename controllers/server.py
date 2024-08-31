import telebot
import supabase_controller as db
import schedule
import time
import threading

# Initialize the bot with your token
API_TOKEN = '5244204118:AAFLg6BjMqgfv6WNclKVDaIEgKcZhPnK818'
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

def polling_thread():
    bot.polling()

def scheduling_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Create and start the polling thread
polling_thread = threading.Thread(target=polling_thread)
polling_thread.start()

# Schedule the send_message function to run every 3 seconds
schedule.every(3).seconds.do(send_message)

# Create and start the scheduling thread
scheduling_thread = threading.Thread(target=scheduling_thread)
scheduling_thread.start()

# Wait for both threads to finish
polling_thread.join()
scheduling_thread.join()

print('hello')