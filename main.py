import os
import requests
from flask import Flask, request, jsonify
from slack_sdk.signature import SignatureVerifier
from google.cloud import aiplatform

app = Flask(__name__)
# Slack credentials from environment variables
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

# Vertex AI configuration from environment variables
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION")
MODEL_NAME = os.environ.get("MODEL_NAME")

aiplatform.init(project=PROJECT_ID, location=LOCATION)
model = aiplatform.GenerativeModel(MODEL_NAME)
verifier = SignatureVerifier(SLACK_SIGNING_SECRET)

@app.route("/", methods=["POST"])
def slack_events():
    """Endpoint for Slack event subscriptions."""
    # First, handle the URL verification challenge
    if request.json and "challenge" in request.json:
        return jsonify({"challenge": request.json["challenge"]})

    # Verify the request signature to ensure it's from Slack
    if not verifier.is_valid(
        body=request.get_data(),
        timestamp=request.headers.get("X-Slack-Request-Timestamp"),
        signature=request.headers.get("X-Slack-Signature"),
    ):
        return "Invalid request signature", 403

    # Parse the request payload and handle the event
    data = request.json
    if "event" in data and data["event"]["type"] == "app_mention":
        text = data["event"]["text"]
        channel_id = data["event"]["channel"]
        thread_ts = data["event"].get("thread_ts", data["event"]["ts"])
        query = text.split(">", 1)[1].strip()
        
        try:
            response_text = generate_response_from_vertex_ai(query)
        except Exception as e:
            response_text = f"Sorry, I encountered an error: {str(e)}"
        
        post_to_slack(channel_id, response_text, thread_ts)

    return "OK", 200

def generate_response_from_vertex_ai(prompt):api
    """Calls the Vertex AI API to get a generated response."""
    response = model.generate_content(prompt)
    return response.text

def post_to_slack(channel, text, thread_ts):
    """Posts a message to Slack."""
    payload = {
        "channel": channel,
        "text": text,
        "thread_ts": thread_ts
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SLACK_TOKEN}"
    }
    requests.post("https://slack.com/api/chat.postMessage", json=payload, headers=headers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
