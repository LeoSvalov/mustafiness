#!/usr/bin/env python3
"""
API Server Runner for FPL Data Collector

This script runs the FastAPI server with proper configuration and logging.
"""

import uvicorn
import logging
import argparse
from pathlib import Path

from src.api_service import app


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('api_server.log')
        ]
    )


def main():
    """Main function to run the API server."""
    parser = argparse.ArgumentParser(description="Mustafiness API Server")
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to (default: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload on code changes"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="Number of worker processes (default: 1)"
    )
    parser.add_argument(
        "--log-level", 
        default="INFO", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Create necessary directories
    Path("exports").mkdir(exist_ok=True)
    Path("cache").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    
    logger.info(f"Starting Mustafiness API Server")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Auto-reload: {args.reload}")
    logger.info(f"Log level: {args.log_level}")
    logger.info(f"API Documentation: http://{args.host}:{args.port}/docs")
    logger.info(f"ReDoc Documentation: http://{args.host}:{args.port}/redoc")
    
    # Run the server
    uvicorn.run(
        "src.api_service:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level=args.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()
