import os
from dotenv import load_dotenv
from specklepy.api.client import SpeckleClient

# Load environment variables from .env file
load_dotenv()

# Get token from environment
token = os.environ.get("SPECKLE_TOKEN")
server_url = os.environ.get("SPECKLE_SERVER", "app.speckle.systems")

if not token:
    raise ValueError("SPECKLE_TOKEN environment variable not set")

# Authenticate
client = SpeckleClient(host=server_url)
client.authenticate_with_token(token)