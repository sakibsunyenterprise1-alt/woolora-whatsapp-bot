import os
from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

def save_to_google_sheet(customer_phone, message_body):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("Woolora_Order_Ledger").sheet1
        sheet.append_row([customer_phone, message_body, "Pending"])
        print("Data saved to Google Sheet successfully!")
    except Exception as e:
        print(f"Error saving to Google Sheet: {e}")

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    VERIFY_TOKEN = "woolora_secure_token_123"
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403
    return "Woolora WhatsApp Webhook is live!", 200

@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.get_json()
    try:
        if "entry" in data:
            for entry in data["entry"]:
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        message = value["messages"][0]
                        sender_phone = message["from"]
                        if message["type"] == "text":
                            message_body = message["text"]["body"]
                            print(f"Order received from {sender_phone}: {message_body}")
                            save_to_google_sheet(sender_phone, message_body)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
