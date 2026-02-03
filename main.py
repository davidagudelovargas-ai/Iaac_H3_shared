"""
Authentication module for Speckle.
This module provides a reusable get_client() function for all other scripts.

Usage:
    from main import get_client
    client = get_client()
"""

import os
from dotenv import load_dotenv
from specklepy.api.client import SpeckleClient


def get_client() -> SpeckleClient:
    """
    Authenticate and return a SpeckleClient instance.
    
    Requires SPECKLE_TOKEN in environment or .env file.
    Optionally set SPECKLE_SERVER (defaults to app.speckle.systems).
    """
    # Load environment variables from a local .env file, if present
    load_dotenv()

    # Get token and server host from environment
    token = os.environ.get("SPECKLE_TOKEN")
    server_host = os.environ.get("SPECKLE_SERVER", "app.speckle.systems")

    if not token:
        raise ValueError("Set SPECKLE_TOKEN in your .env file and re-run.")

    # Authenticate
    client = SpeckleClient(host=server_host)
    client.authenticate_with_token(token)

    return client


if __name__ == "__main__":
    # Test authentication when running this script directly
    client = get_client()
    user = client.active_user.get()
    print(f"OK Logged in as {user.name} on {client.url}")