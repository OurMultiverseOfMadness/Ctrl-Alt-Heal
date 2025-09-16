#!/usr/bin/env python3
"""
Local webhook server for Ctrl-Alt-Heal development and testing.

This script runs the FastAPI application locally for development and testing.
It can be used with ngrok to test Telegram webhooks locally.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run the local development server."""
    try:
        import uvicorn
        from ctrl_alt_heal.fargate_app import app

        logger.info("Starting Ctrl-Alt-Heal local development server...")
        logger.info("Server will be available at: http://localhost:8000")
        logger.info("Health check: http://localhost:8000/health")
        logger.info("API docs: http://localhost:8000/docs")
        logger.info("Webhook endpoint: http://localhost:8000/webhook")

        # Run the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,  # Enable auto-reload for development
            log_level="info",
        )

    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Please install development dependencies:")
        logger.error("pip install -r requirements-dev.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
