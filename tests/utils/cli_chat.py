#!/usr/bin/env python3
import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import httpx
import websockets
from websockets.exceptions import ConnectionClosed


# Server configuration
TEST_BASE_URL = "http://localhost:8080"
TEST_WS_URL = "ws://localhost:8080"


class ChatCLI:
    """Interactive CLI for WebSocket chat testing."""

    def __init__(self):
        self.base_url = TEST_BASE_URL
        self.ws_url = TEST_WS_URL
        self.access_token = None
        self.user_id = None
        self.chat_id = None
        self.websocket = None
        self.running = True

    async def create_user(self) -> dict:
        """Create a test user and get auth tokens."""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                "/v1/users",
                json={"apple_id": "cli_test_user"}
            )
            response.raise_for_status()
            data = response.json()
            return data["data"]

    async def create_chat(self) -> dict:
        """Create a test chat."""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(
                "/v1/chats",
                json={"title": "CLI Test Chat"},
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            response.raise_for_status()
            return response.json()

    async def delete_user(self):
        """Delete the test user (cascades to chats and messages)."""
        if not self.access_token:
            return

        try:
            async with httpx.AsyncClient(base_url=self.base_url) as client:
                response = await client.delete(
                    "/v1/users",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                print("\nTest data cleaned up successfully")
        except Exception as e:
            print(f"\nError cleaning up test data: {e}")

    async def setup(self):
        """Initialize user and chat."""
        print("Setting up test environment...")

        # Create user
        user_data = await self.create_user()
        self.access_token = user_data["tokens"]["access_token"]
        self.user_id = user_data["user"]["id"]
        print(f"User created: {self.user_id}")

        # Create chat
        chat_data = await self.create_chat()
        self.chat_id = chat_data["id"]
        print(f"Chat created: {self.chat_id}")
        print("\nReady to chat! Type your messages (Ctrl+C to exit)\n")

    async def cleanup(self):
        """Cleanup resources."""
        print("\nCleaning up...")

        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass

        await self.delete_user()

    async def receive_messages(self):
        """Receive and display messages from WebSocket."""
        try:
            async for message in self.websocket:
                data = json.loads(message)

                if data.get("type") == "history":
                    messages = data.get("messages", [])
                    if messages:
                        print("\n--- Chat History ---")
                        for msg in messages:
                            role = msg["role"].upper()
                            content = msg["content"]
                            print(f"[{role}]: {content}")
                        print("--- End History ---\n")

                elif data.get("type") == "message":
                    msg = data.get("data", {})
                    role = msg.get("role", "").upper()
                    content = msg.get("content", "")

                    if role == "USER":
                        print(f"[YOU]: {content}")
                    elif role == "ASSISTANT":
                        print(f"[ASSISTANT]: {content}\n")

                elif data.get("type") == "error":
                    error_msg = data.get("error", "Unknown error")
                    print(f"\nError: {error_msg}\n")

                elif data.get("type") == "pong":
                    # Ignore pong responses
                    pass

        except ConnectionClosed:
            if self.running:
                print("\nConnection closed by server")
                self.running = False
        except Exception as e:
            if self.running:
                print(f"\nError receiving messages: {e}")
                self.running = False

    async def send_message(self, content: str):
        """Send a message through WebSocket."""
        try:
            message = {
                "type": "message",
                "content": content
            }
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending message: {e}")
            self.running = False

    async def read_input(self):
        """Read user input from stdin."""
        loop = asyncio.get_event_loop()

        while self.running:
            try:
                # Read input in a non-blocking way
                content = await loop.run_in_executor(
                    None,
                    lambda: input("> ")
                )

                if not content.strip():
                    continue

                if content.lower() in ["exit", "quit", "q"]:
                    self.running = False
                    break

                await self.send_message(content)

            except EOFError:
                self.running = False
                break
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                if self.running:
                    print(f"\nError reading input: {e}")

    async def connect_websocket(self):
        """Connect to WebSocket and handle chat."""
        ws_url = f"{self.ws_url}/v1/chat/ws/{self.chat_id}"

        try:
            async with websockets.connect(
                ws_url,
                additional_headers={
                    "Authorization": f"Bearer {self.access_token}"
                }
            ) as websocket:
                self.websocket = websocket

                # Run receive and input tasks concurrently
                receive_task = asyncio.create_task(self.receive_messages())
                input_task = asyncio.create_task(self.read_input())

                # Wait for either task to complete
                done, pending = await asyncio.wait(
                    [receive_task, input_task],
                    return_when=asyncio.FIRST_COMPLETED
                )

                # Cancel remaining tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

        except ConnectionRefusedError:
            print("Could not connect to server. Is the server running?")
            print(f"   Trying to connect to: {ws_url}")
        except Exception as e:
            print(f"WebSocket error: {e}")

    async def run(self):
        """Main run loop."""
        try:
            await self.setup()
            await self.connect_websocket()
        except httpx.HTTPError as e:
            print(f"HTTP error: {e}")
            if hasattr(e, 'response'):
                print(f"   Response: {e.response.text}")
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()


async def main():
    """Entry point."""
    print("=" * 60)
    print("WebSocket Chat CLI Test Tool")
    print("=" * 60)
    print()

    cli = ChatCLI()
    await cli.run()

    print("\nGoodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
