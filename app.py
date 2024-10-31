from flask import Flask, render_template, jsonify
import requests
import threading
import time
import re

app = Flask(__name__)

# URLs for the two chat APIs
url_1 = "https://api-chat-one-mu.vercel.app/api/chat"
url_2 = "https://chat-api-kappa-six.vercel.app/api/chat"

# Define the starting topic for the conversation
topic = "Let's talk about the future of AI and technology."
conversation_log = []
is_running = True

# Define your Render app's own URL for self-pinging (update this after deployment)
SELF_PING_URL = "http://localhost:5000/ping"  # Replace with your deployed URL on Render

def clean_response(text):
    """Remove <split></split> tags from the response text."""
    return re.sub(r"<split></split>", "", text)

def run_conversation():
    """Runs an infinite conversation between the two APIs in a background thread."""
    global topic, conversation_log, is_running
    question = topic
    while is_running:
        # Send question to the first API
        response_1 = requests.get(url_1, params={"question": question})
        if response_1.status_code == 200:
            answer_1_raw = response_1.json().get("response", "No response from API 1")
            answer_1 = clean_response(answer_1_raw)
            developer_1 = response_1.json().get("developer", "Unknown")
            conversation_log.append(f"API 1 ({developer_1}): {answer_1}")
        else:
            conversation_log.append("Error with API 1")
            break

        # Send answer from API 1 as question to the second API
        response_2 = requests.get(url_2, params={"question": answer_1})
        if response_2.status_code == 200:
            answer_2_raw = response_2.json().get("response", "No response from API 2")
            answer_2 = clean_response(answer_2_raw)
            developer_2 = response_2.json().get("developer", "Unknown")
            conversation_log.append(f"API 2 ({developer_2}): {answer_2}")
        else:
            conversation_log.append("Error with API 2")
            break

        # Use API 2's answer as the next question for API 1
        question = answer_2

        # Limit the log size to 50 messages to keep memory usage manageable
        if len(conversation_log) > 50:
            conversation_log.pop(0)

        # Pause briefly to avoid overwhelming the APIs
        time.sleep(1)

def auto_ping():
    """Pings the app's own /ping endpoint every 5 minutes to keep it awake."""
    while True:
        try:
            requests.get(SELF_PING_URL)
            print("Pinged self to stay awake.")
        except requests.RequestException as e:
            print(f"Failed to ping: {e}")
        time.sleep(300)  # Ping every 5 minutes

@app.route("/")
def index():
    """Renders the web interface for viewing the conversation."""
    return render_template("index.html")

@app.route("/conversation")
def get_conversation():
    """Returns the current conversation log as JSON."""
    return jsonify(conversation_log)

@app.route("/stop", methods=["POST"])
def stop_conversation():
    """Stops the conversation by setting is_running to False."""
    global is_running
    is_running = False
    return "Conversation stopped"

@app.route("/ping")
def ping():
    """Ping endpoint for self-pinging to keep the app awake."""
    return "pong"

if __name__ == "__main__":
    # Start the conversation and auto-ping in separate background threads
    conversation_thread = threading.Thread(target=run_conversation, daemon=True)
    conversation_thread.start()
    
    ping_thread = threading.Thread(target=auto_ping, daemon=True)
    ping_thread.start()

    # Run the Flask app
    app.run(host="0.0.0.0", port=5000)
