import os
import requests
from flask import Flask, request
import google.generativeai as genai

app = Flask(__name__)

# Gemini API Configure
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# এআই এর নিয়ম ও নির্দেশাবলি
SYSTEM_PROMPT = """
তুমি "Pure Water Electronic" এর একজন কাস্টমার সাপোর্ট প্রতিনিধি।
কাস্টমারের যেকোনো প্রশ্নের উত্তর প্রাঞ্জল বাংলায় দেবে।

আমাদের তথ্য ও দাম:
- Water Filters (দাম: ১২,০০০ টাকা থেকে ৩৫,০০০ টাকা)
- RO Water Filter: ১৫,০০০ টাকা
- Alkaline Filter: ১৮,০০০ টাকা
- ডেলিভারি: সারা বাংলাদেশে হোম ডেলিভারি সার্ভিস উপলব্ধ।

তোমার কাজ কাস্টমারকে তাদের প্রশ্ন অনুযায়ী সঠিক তথ্য দেওয়া এবং তাদের অর্ডার নিতে সাহায্য করা।
"""

def get_gemini_response(user_message):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        full_prompt = f"{SYSTEM_PROMPT}\n\nCustomer: {user_message}\nResponse:"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Gemini কাজ না করলে এই মেসেজটি যাবে
        return "ধন্যবাদ Pure Water Electronic-এ যোগাযোগ করার জন্য। আমরা কীভাবে আপনাকে সাহায্য করতে পারি?"

@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == os.environ.get("VERIFY_TOKEN"):
        return challenge, 200
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data and data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                if messaging_event.get("message") and messaging_event["message"].get("text"):
                    user_text = messaging_event["message"]["text"]
                    
                    # Gemini থেকে উত্তর আনা
                    bot_reply = get_gemini_response(user_text)
                    
                    # কাস্টমারকে মেসেজ পাঠানো
                    send_message(sender_id, bot_reply)
    return "EVENT_RECEIVED", 200

def send_message(recipient_id, text):
    page_access_token = os.environ.get("PAGE_ACCESS_TOKEN")
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={page_access_token}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    requests.post(url, json=payload)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
