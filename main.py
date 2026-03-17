import os
import telebot
from flask import Flask, request
from openai import OpenAI

# 1. Fetch Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
# Render automatically provides this variable (e.g., https://your-app.onrender.com)
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") 

if not BOT_TOKEN or not HF_TOKEN:
    raise ValueError("BOT_TOKEN or HF_TOKEN environment variables are missing!")

# 2. Initialize Telegram Bot and Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 3. Initialize OpenAI Client (pointing to Hugging Face router)
hf_client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# 4. Telegram Bot Message Handlers
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am an AI bot powered by DeepSeek. Send me a message to start chatting!")

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    user_text = message.text
    
    # Show "typing" status in Telegram while waiting for the AI response
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Call the Hugging Face API using the OpenAI library format
        response = hf_client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita",
            messages=[
                {
                    "role": "user",
                    "content": user_text
                }
            ]
        )
        
        # Extract and send the AI's response
        bot_reply = response.choices[0].message.content
        bot.reply_to(message, bot_reply)
        
    except Exception as e:
        bot.reply_to(message, f"Sorry, I encountered an error: {str(e)}")

# 5. Flask Routes for Webhook
@app.route('/' + BOT_TOKEN, methods=['POST'])
def receive_update():
    # Receive updates from Telegram and pass them to the bot
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def index():
    return "Bot is running and webhook is active!", 200

# 6. Set Webhook on Startup
bot.remove_webhook()
if WEBHOOK_URL:
    # Set the webhook to the Render URL + the Bot Token path
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")

if __name__ == "__main__":
    # Note: When deploying on Render, Gunicorn will run the app, 
    # but this block handles local testing.
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
