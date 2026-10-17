import os
import requests
from flask import Flask, request
import google.generativeai as genai

app = Flask(__name__)

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# আপনার দোকানের সব নির্দেশাবলি ও পণ্যের বিস্তারিত তথ্য এখানে লিখুন
SYSTEM_PROMPT = """
তুমি "Pure Water Electronic" এর একজন সেরা কাস্টমার সাপোর্ট প্রতিনিধি। 
কাস্টমার যা-ই জিজ্ঞেস করবে, তুমি নিচের নিয়ম মেনে সঠিকভাবে উত্তর দেবে:

১. ভাষা: সবসময় প্রাঞ্জল ও বিনয়ী বাংলায় কথা বলবে (কাস্টমার ইংলিশ বা বাংলিশে লিখলেও বাংলায় উত্তর দেবে)।
২. আমাদের কাজ: আমরা ওয়াটার ফিল্টার বিক্রি করি ও সার্ভিসিং প্রদান করি।
৩. পণ্যের দাম ও তালিকা:
   -DAM KOTO
   - 1200 TK
   - Alkaline Filter: ১৮,০০০ টাকা
৪. ডেলিভারি ও সার্ভিস: সারা বাংলাদেশে হোম ডেলিভারি ফ্রি।
৫. অর্ডার করার নিয়ম: কাস্টমার কিনতে চাইলে তার নাম, ফোন নম্বর এবং ঠিকানা চাইবে।
৬. আচরণ: সবসময় কাস্টমারকে সম্মান দিয়ে কথা বলবে এবং প্রতিটি প্রশ্নের স্পষ্ট উত্তর দেবে।
"""

def get_gemini_response(user_message):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        full_prompt = f"{SYSTEM_PROMPT}\n\nCustomer message: {user_message}\nYour Response:"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "ধন্যবাদ Pure Water Electronic-এ যোগাযোগ করার জন্য। আমরা আপনাকে কীভাবে সাহায্য করতে পারি?"

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
    if data.get("object") == "page":
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
