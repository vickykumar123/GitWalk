"""
Development server runner with graceful shutdown handling.

Usage:
    python run_dev.py

This script provides better Ctrl+C handling on Windows compared to
running uvicorn directly from the command line.
"""
import uvicorn
import signal
import sys


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n👋 Shutting down gracefully...")
    sys.exit(0)


# Register signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    print("🚀 Starting development server...")
    print("📍 Server will run on: http://localhost:9999")
    print("📚 API docs available at: http://localhost:9999/docs")
    print("🔄 Auto-reload enabled - changes will restart the server")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9999,
        reload=True,
        reload_dirs=["app"],  # Only watch app/ folder for changes
        log_level="info"
    )
