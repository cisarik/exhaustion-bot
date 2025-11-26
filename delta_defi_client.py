import asyncio
import websockets
import json
import logging
from typing import Callable, Awaitable

logger = logging.getLogger("DeltaDefiClient")

class DeltaDefiClient:
    """
    Async WebSocket Client for DeltaDefi Protocol.
    Based on standard patterns: Connect -> Subscribe -> Listen loop.
    """
    def __init__(self, uri: str = "wss://api.deltadefi.io/ws", api_key: str = None):
        self.uri = uri
        self.api_key = api_key
        self.connection = None
        self.callbacks = []
        self.running = False

    async def connect(self):
        """Establishes WebSocket connection."""
        try:
            logger.info(f"Connecting to DeltaDefi WS: {self.uri}")
            self.connection = await websockets.connect(self.uri)
            self.running = True
            
            # Authenticate if needed
            if self.api_key:
                await self.send({"action": "auth", "key": self.api_key})
                
            logger.info("Connected.")
            
            # Start listener loop in background
            asyncio.create_task(self.listen())
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise

    async def subscribe(self, topic: str, params: dict = {}):
        """Subscribes to a specific topic (e.g., 'candles', 'trades')."""
        if not self.connection:
            raise Exception("Not connected")
            
        payload = {
            "action": "subscribe",
            "topic": topic,
            "params": params
        }
        await self.send(payload)
        logger.info(f"Subscribed to {topic}")

    async def send(self, data: dict):
        await self.connection.send(json.dumps(data))

    def on_message(self, callback: Callable[[dict], Awaitable[None]]):
        """Register a callback function to handle incoming messages."""
        self.callbacks.append(callback)

    async def listen(self):
        """Main loop to read messages."""
        try:
            async for message in self.connection:
                data = json.loads(message)
                # Dispatch to callbacks
                for cb in self.callbacks:
                    try:
                        await cb(data)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed.")
            self.running = False
        except Exception as e:
            logger.error(f"Listener error: {e}")
            self.running = False

    async def close(self):
        self.running = False
        if self.connection:
            await self.connection.close()

# Example Usage Mock
async def main():
    # Mock Server for testing logic (since we don't have real URL access)
    client = DeltaDefiClient("wss://echo.websocket.org") # Echo for test
    await client.connect()
    
    async def handler(msg):
        print(f"Received: {msg}")

    client.on_message(handler)
    
    # Simulate sub
    await client.subscribe("candles_1m", {"symbol": "ADA/USDC"})
    
    # Wait a bit
    await asyncio.sleep(5)
    await client.close()

if __name__ == "__main__":
    # Needs 'websockets' lib
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except Exception as e:
        print(e)
