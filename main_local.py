import os
import time
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
CORS(app)

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# ======================
# FIX 1: Handle GET requests
# ======================
@app.route('/analytics', methods=['GET', 'POST'])
def analytics():
    """Handle both GET and POST requests gracefully"""
    if request.method == 'GET':
        return jsonify({
            "error": "Use POST instead",
            "example_request": {
                "userAgent": "YourUserAgent",
                "sessionId": "abc123",
                "platform": "Windows/Linux/macOS"
            }
        }), 405

    try:
        # ======================
        # FIX 2: Skip Discord in test mode
        # ======================
        data = request.get_json()
        if data.get('skipDiscord'):
            logger.info("Test mode - skipping Discord")
            return jsonify({"status": "test_success"})

        # ======================
        # FIX 3: Rate limiting handling
        # ======================
        if not DISCORD_WEBHOOK_URL:
            logger.error("Discord webhook not configured")
            return jsonify({"status": "error"}), 500

        discord_message = {
            "embeds": [{
                "title": " Mango Paradise - New Visitor",
                "color": 16753920,
                "fields": [
                    {
                        "name": " Browser",
                        "value": f"`{data.get('userAgent', 'Unknown')[:200]}`",
                        "inline": False
                    }
                ]
            }]
        }

        # First attempt
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=discord_message,
            timeout=5
        )

        # Handle rate limits
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 3))
            logger.warning(f"Rate limited - retrying after {retry_after}s")
            time.sleep(retry_after)
            response = requests.post(
                DISCORD_WEBHOOK_URL,
                json=discord_message,
                timeout=5
            )

        if response.status_code == 204:
            return jsonify({"status": "success"})
        
        logger.error(f"Discord error: {response.status_code}")
        return jsonify({
            "status": "error",
            "discord_status": response.status_code
        }), 500

    except Exception as e:
        logger.error(f"Failed: {str(e)}")
        return jsonify({"status": "error"}), 500

# ======================
# FIX 4: Favicon and health checks
# ======================
@app.route('/favicon.ico')
def favicon():
    return "", 204

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "discord_configured": bool(DISCORD_WEBHOOK_URL)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))