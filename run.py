#!/usr/bin/env python3
"""
Mini Dropbox - Distributed File Storage System
Main application entry point
"""

import os
from app import create_app, socketio

# Create Flask app
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    # Run the application
    socketio.run(app, debug=debug, host=host, port=port)