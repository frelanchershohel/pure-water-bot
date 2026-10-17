import os
import requests
from flask import Flask, request
from google import genai

app = Flask(__name__)

# New Google GenAI Client Configuration
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY.strip()) if GEMINI_KEY else None

SYSTEM_PROMPT = """
তুমি "Pure Water Electronic" এর একজন কাস্টমার সাপোর্ট প্রতিনিধি।
তোমার কাজ কাস্টমারের প্রশ্ন বুঝে সঠিক ও বিনয়ী উত্তর দেওয়া।

আমাদের ফিল্টারের দাম ও তথ্য:
- RO Water Filter: ১৫,০০০ টাকা
- Alkaline Water Filter: ১৮,০০০ টাকা
- UV Water Filter: ৮,০০০ টাকা
- অন্যান্য সকল ওয়াটার ফিল্টার: ১২,০০০ টাকা থেকে ৩৫,০০০ টাকার মধ্যে।
- ডেলিভারি: সারা বাংলাদেশে ফ্রি হোম ডেলিভারি।

কাস্টমার দাম (Dam / Price) জানতে চাইলে সরাসরি ফিল্টারগুলোর আসল দাম উল্লেখ করে উত্তর দেবে।
"""

def get_gemini_response(user_message):
    try:
        if not client:
            return "আমাদের সব ধরনের ওয়াটার ফিল্টারের দাম ১২,০০০ টাকা থেকে ৩৫,০০০ টাকা পর্যন্ত।"
            
        full_prompt = f"{SYSTEM_PROMPT}\n\nCustomer: {user_message}\nResponse:"
        
        # New SDK model format
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
        )
        
        if response and response.text:
            return response.text
        else:
            return "আমাদের ওয়াটার ফিল্টারের দাম ১২,০০০ টাকা থেকে ৩৫,০০০ টাকা পর্যন্ত। আপনি কোনটি সম্পর্কে জানতে চান?"
            
    except Exception as e:
        print(f"CRITICAL GEMINI ERROR: {e}")
        return f"আমাদের সব ধরনের ওয়াটার ফিল্টারের দাম ১২,০০০ টাকা থেকে ৩৫,০০০ টাকা পর্যন্ত। RO Filter: ১৫,০০০ টাকা, Alkaline Filter: ১৮,০০০ টাকা। আপনি কোনটি নিতে চান?"

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
                    bot_reply = get_gemini_response(user_text)
                    send_message(sender_id, bot_reply)
    return "EVENT_RECEIVED", 200

def send_message(recipient_id, text):
    page_access_token = os.environ.get("PAGE_ACCESS_TOKEN")
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={page_access_token}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    requests.post(url, json=payload)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
