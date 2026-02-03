"""
06 - GQL Subscriptions with Speckle

This script demonstrates how to subscribe to real-time updates from a Speckle project ("project_id")
using GraphQL subscriptions over WebSocket.
"""

import asyncio
from gql import gql, Client
from gql.transport.websockets import WebsocketsTransport
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Your Speckle token
YOUR_TOKEN =  os.environ.get("SPECKLE_TOKEN")
PROJECT_ID = "a2d4f63c4b"

# Define the subscription query
subscription_query = gql("""
    subscription ProjectVersionsUpdated($projectId: String!) {
        projectVersionsUpdated(id: $projectId) {
            id
            modelId
            type
            version {
                id
                message
                createdAt
            }
        }
    }
""")

async def subscribe_to_project_updates():
    """
    Subscribe to project version updates using WebSocket
    """
    # Create WebSocket transport with authentication
    transport = WebsocketsTransport(
        url="wss://app.speckle.systems/graphql",
        init_payload={
            "Authorization": f"Bearer {YOUR_TOKEN}"
        }
    )
    
    # Create a GraphQL client
    client = Client(
        transport=transport,
        fetch_schema_from_transport=False,
    )
    
    try:
        async with client as session:
            print(f"🔌 Connected to Speckle WebSocket")
            print(f"📡 Listening for updates on project: {PROJECT_ID}")
            print("Press Ctrl+C to stop\n")
            
            try:
                # Subscribe to the query
                async for result in session.subscribe(
                    subscription_query,
                    variable_values={"projectId": PROJECT_ID}
                ):
                    print("=" * 50)
                    print("📦 New Update Received!")
                    print("=" * 50)
                    
                    data = result.get("projectVersionsUpdated")
                    if data:
                        print(f"ID: {data.get('id')}")
                        print(f"Model ID: {data.get('modelId')}")
                        print(f"Type: {data.get('type')}")
                        
                        version = data.get('version')
                        if version:
                            print(f"\nVersion Details:")
                            print(f"  - Version ID: {version.get('id')}")
                            print(f"  - Message: {version.get('message')}")
                            print(f"  - Created At: {version.get('createdAt')}")
                        
                        print("\n")
                    
            except asyncio.CancelledError:
                print("\n\n👋 Subscription cancelled")
                raise
            except KeyboardInterrupt:
                print("\n\n👋 Subscription stopped by user")
                raise
            
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Ensure transport is properly closed
        await transport.close()
        print("🔌 Connection closed properly")

if __name__ == "__main__":
    # Run the subscription
    asyncio.run(subscribe_to_project_updates())
