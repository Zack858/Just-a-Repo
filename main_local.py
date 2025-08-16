import os
import requests
from flask import Flask, request, jsonify
import logging
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS

# Discord webhook from environment variable
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

@app.route('/')
def home():
    """Root endpoint with service info"""
    return jsonify({
        "service": "Mango Paradise Analytics",
        "status": "running",
        "endpoints": {
            "analytics": "POST /analytics",
            "health": "GET /health"
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
    """Handle visitor analytics and send to Discord"""
    try:
        # Verify webhook configured
        if not DISCORD_WEBHOOK_URL:
            logger.error("Discord webhook not configured")
            return jsonify({"status": "error", "message": "Service not configured"}), 500

        # Validate request
        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({"status": "error", "message": "No data provided"}), 400

        logger.info(f"Analytics request from: {data.get('userAgent', 'Unknown')}")

        # Prepare Discord message
        discord_message = {
            "embeds": [{
                "title": " Mango Paradise - New Visitor",
                "description": f"**Session:** `{data.get('sessionId', 'Unknown')}`",
                "color": 16753920,  # Orange
                "fields": [
                    {
                        "name": " Browser",
                        "value": f"**{data.get('browserInfo', 'Unknown')}**\n{data.get('userAgent', 'Unknown')[:200]}...",
                        "inline": False
                    },
                    {
                        "name": " Device",
                        "value": f"**OS:** {data.get('platform', 'Unknown')}\n**Screen:** {data.get('screenResolution', 'Unknown')}",
                        "inline": True
                    }
                ]
            }]
        }

        # Send to Discord
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=discord_message,
            timeout=5
        )

        if response.status_code == 204:
            logger.info("Analytics sent to Discord")
            return jsonify({"status": "success"})
        
        logger.error(f"Discord error: {response.status_code}")
        return jsonify({"status": "error", "discord_status": response.status_code}), 500

    except Exception as e:
        logger.error(f"Analytics failed: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)