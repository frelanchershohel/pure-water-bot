import os
import requests
from flask import Flask, request

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "purewaterverifytoken")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return "Pure Water Electronic Bot is running!"

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403
    return "Hello world", 200

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                if messaging_event.get("message") and messaging_event["message"].get("text"):
                    message_text = messaging_event["message"]["text"]
                    handle_message(sender_id, message_text)
    return "ok", 200

def handle_message(sender_id, message_text):
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        
        system_instruction = (
            "You are an autonomous AI customer support chatbot for 'Pure Water Electronic'. "
            "Products & Pricing: \n"
            "- Premium Package: 3 filters, 970 BDT\n"
            "- Gold Package: 6 filters, 1200 BDT\n"
            "Delivery Fees: 80 BDT for Dhaka, 135 BDT for Outside Dhaka.\n"
            "Be polite, helpful, and concise in Bengali or English based on user query."
        )
        
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
        response = model.generate_content(message_text)
        reply_text = response.text
    except Exception as e:
        reply_text = "Hello! Welcome to Pure Water Electronic. How can we help you today?"

    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": sender_id},
        "message": {"text": reply_text}
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
