#!/usr/bin/env python3
"""
Command-line interface for MyGPT application
"""
import os
import sys
import argparse
from pathlib import Path


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='MyGPT - AI Chat Assistant')
    parser.add_argument(
        '--host', 
        default='127.0.0.1', 
        help='Host to bind to (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=5000, 
        help='Port to bind to (default: 5000)'
    )
    parser.add_argument(
        '--debug', 
        action='store_true', 
        help='Run in debug mode'
    )
    parser.add_argument(
        '--env', 
        choices=['development', 'production', 'testing'], 
        default='development',
        help='Environment configuration (default: development)'
    )
    
    args = parser.parse_args()
    
    # Set environment
    os.environ.setdefault('FLASK_ENV', args.env)
    
    # Import after setting environment
    from .app import create_app
    from .routes import init_routes
    
    app = create_app()
    init_routes(app)
    
    if args.debug or args.env == 'development':
        app.run(host=args.host, port=args.port, debug=True)
    else:
        # Use Waitress for production
        from waitress import serve
        print(f"Starting MyGPT on {args.host}:{args.port}")
        serve(app, host=args.host, port=args.port)


if __name__ == '__main__':
    main()