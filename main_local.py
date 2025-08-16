import os
import requests
from flask import Flask, render_template, request, jsonify
import logging
from flask_cors import CORS  # For handling CORS in production

# Configure production-ready logging
logging.basicConfig(
    level=logging.WARNING,  # Reduced from INFO to WARNING for production
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes (adjust in production as needed)

# Discord webhook from environment variable
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

@app.route('/')
def index():
    """Serve the mango-themed page"""
    return render_template('index.html')

@app.route('/MangoZack858.com')
@app.route('/mangozack858')
def mangozack858():
    """Alternative access route"""
    return render_template('index.html')

@app.route('/analytics', methods=['POST'])
def analytics():
    """Handle visitor analytics and send to Discord webhook"""
    try:
        if not DISCORD_WEBHOOK_URL:
            logger.error("Discord webhook URL not configured")
            return jsonify({"status": "error", "message": "Service not configured"}), 500

        data = request.get_json()
        
        # Sanitized logging
        logger.info(
            "Analytics request: %s on %s (%s)",
            data.get('browserInfo', 'Unknown'),
            data.get('platform', 'Unknown'),
            data.get('sessionId', 'Unknown')[:8] + "..."
        )

        # Create Discord message
        discord_message = {
            "embeds": [{
                "title": " Mango Paradise - New Visitor",
                "description": f"**Session:** `{data.get('sessionId', 'Unknown')}`",
                "color": 16753920,
                "fields": [
                    {"name": " Browser", "value": f"**{data.get('browserInfo', 'Unknown')}**\n{data.get('userAgent', 'Unknown')[:200]}...", "inline": False},
                    {"name": " Device", "value": f"**OS:** {data.get('platform', 'Unknown')}\n**Screen:** {data.get('screenResolution', 'Unknown')}", "inline": True},
                    {"name": " Location", "value": f"**TZ:** {data.get('timezone', 'Unknown')}\n**Lang:** {data.get('language', 'Unknown')}", "inline": True}
                ]
            }]
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=discord_message, timeout=5)
        
        if response.status_code == 204:
            return jsonify({"status": "success"})
        logger.error(f"Discord error: {response.status_code}")
        return jsonify({"status": "error"}), 500
            
    except Exception as e:
        logger.error(f"Analytics failed: {str(e)}", exc_info=True)
        return jsonify({"status": "error"}), 500

if __name__ == '__main__':
    # Production configuration
    app.run(host='0.0.0.0', port=5000, debug=False)