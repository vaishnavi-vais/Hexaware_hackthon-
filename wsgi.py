#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""

from run import create_app
import os

app = create_app(os.environ.get('FLASK_CONFIG', 'production'))

if __name__ == "__main__":
    app.run()
