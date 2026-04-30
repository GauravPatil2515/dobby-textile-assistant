"""
web.py
Light-weight Flask app entrypoint. Registers route blueprints from the
`routes` package so each endpoint lives in its own module.

This file intentionally contains minimal logic so `api/index.py` can import
`app` for Vercel deployments.
"""

import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return None

from flask import Flask, render_template
from routes import register_routes

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dobby-textile-2025')

# Register route blueprints (chat, health, vision)
register_routes(app)


@app.route('/')
def index():
    """Render the main interface shell."""
    return render_template('index.html')


if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(host=host, port=port, debug=debug)
