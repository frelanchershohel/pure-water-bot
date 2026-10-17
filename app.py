import os
import requests
from flask import Flask, request
import google.generativeai as genai

app = Flask(__name__)

# Gemini API Configuration
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY.strip())

SYSTEM_PROMPT = """
তুমি "Pure Water Electronic" এর একজন কাস্টমার সাপোর্ট প্রতিনিধি।
কাস্টমার যা-ই জিজ্ঞেস করবে, তুমি নিচের নিয়ম মেনে প্রাঞ্জল বাংলায় উত্তর দেবে:

১. আমাদের কাজ: আমরা ওয়াটার ফিল্টার বিক্রি করি ও সার্ভিসিং প্রদান করি।
২. পণ্যের দাম ও তালিকা:
   - RO Water Filter: ১৫,০০০ টাকা
   - Alkaline Filter: ১৮,০০০ টাকা
   - UV Water Filter: ৮,০০০ টাকা
   - অন্যান্য ওয়াটার ফিল্টার: ১২,০০০ টাকা থেকে ৩৫,০০০ টাকার মধ্যে।
৩. ডেলিভারি ও সার্ভিস: সারা বাংলাদেশে হোম ডেলিভারি ফ্রি।
৪. কাস্টমার দাম জানতে চাইলে বা কিনতে চাইলে সরাসরি সঠিক দাম ও তথ্য জানিয়ে সাহায্য করবে।
"""

def get_gemini_response(user_message):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        full_prompt = f"{SYSTEM_PROMPT}\n\nCustomer message: {user_message}\nResponse:"
        response = model.generate_content(full_prompt)
        if response and response.text:
            return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
    
    # ব্যাকআপ উত্তর (Gemini কোনো কারণে রেসপন্স না দিলে এটি যাবে)
    return "আমাদের সব ধরনের ওয়াটার ফিল্টারের দাম ১২,০০০ টাকা থেকে ৩৫,০০০ টাকা পর্যন্ত। RO Filter: ১৫,০০০ টাকা, Alkaline Filter: ১৮,০০০ টাকা। আপনি কোনটি নিতে চান?"

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
