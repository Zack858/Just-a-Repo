import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

@app.route('/')
def home():
    """Root endpoint with service info"""
    return jsonify({
        "service": "Mango Paradise Backend",
        "status": "running",
        "frontend": "Use Netlify deployment for UI",
        "endpoints": {
            "analytics": {"methods": ["POST"], "purpose": "Send visitor data to Discord"},
            "health": {"methods": ["GET"], "purpose": "Service status check"}
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "discord_configured": bool(DISCORD_WEBHOOK_URL)
    })

@app.route('/analytics', methods=['POST'])
def analytics():
    """Process analytics data and forward to Discord"""
    try:
        # Debug mode bypass
        data = request.get_json()
        if data.get('skipDiscord'):
            logger.info("Test mode activated - skipping Discord")
            return jsonify({"status": "test_success"})

        if not DISCORD_WEBHOOK_URL:
            logger.error("Discord webhook not configured")
            return jsonify({"status": "error", "message": "Webhook not configured"}), 500

        # Prepare minimal Discord payload
        discord_msg = {
            "embeds": [{
                "title": " New Visitor",
                "color": 0xFF6B35,  # Mango orange
                "fields": [
                    {"name": "Device", "value": data.get('userAgent', 'Unknown')[:100]},
                    {"name": "Session", "value": data.get('sessionId', 'Unknown')[:20]}
                ]
            }]
        }

        # Send to Discord with timeout
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=discord_msg,
            timeout=5  # 5-second timeout
        )

        if response.status_code == 204:
            return jsonify({"status": "success"})
        
        logger.error(f"Discord error: {response.status_code}")
        return jsonify({"status": "error", "discord_status": response.status_code}), 500

    except Exception as e:
        logger.error(f"Analytics processing failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)