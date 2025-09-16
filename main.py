import os
import requests
from flask import Flask, request, jsonify
from slack_sdk.signature import SignatureVerifier
from google.cloud import aiplatform

# Initialize Flask app
app = Flask(__name__)

# Slack credentials from environment variables
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

# Vertex AI configuration from environment variables
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION")
MODEL_NAME = os.environ.get("MODEL_NAME")

# Initialize Vertex AI client
aiplatform.init(project=PROJECT_ID, location=LOCATION)
model = aiplatform.GenerativeModel(MODEL_NAME)
verifier = SignatureVerifier(SLACK_SIGNING_SECRET)

@app.route("/", methods=["POST"])
def slack_events():
    """Endpoint for Slack event subscriptions."""
    # Verify the request signature to ensure it's from Slack
    if not verifier.is_valid(
        body=request.get_data(),
        timestamp=request.headers.get("X-Slack-Request-Timestamp"),
        signature=request.headers.get("X-Slack-Signature"),
    ):
        return "Invalid request signature", 403

    # Parse the request payload
    data = request.json
    
    # Handle Slack URL verification challenge
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})
    
    # Process app_mention events
    if "event" in data and data["event"]["type"] == "app_mention":
        text = data["event"]["text"]
        channel_id = data["event"]["channel"]
        thread_ts = data["event"].get("thread_ts", data["event"]["ts"])
        
        # Extract the user's query from the message
        # We need to remove the bot's mention from the text
        query = text.split(">", 1)[1].strip()
        
        # Get a response from Vertex AI
        try:
            response_text = generate_response_from_vertex_ai(query)
        except Exception as e:
            response_text = f"Sorry, I encountered an error: {str(e)}"
        
        # Send the response back to Slack in the same thread
        post_to_slack(channel_id, response_text, thread_ts)

    return "OK", 200

def generate_response_from_vertex_ai(prompt):
    """Calls the Vertex AI API to get a generated response."""
    # The actual call to the Vertex AI model
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
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))