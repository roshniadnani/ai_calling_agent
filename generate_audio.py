import os
import sys
sys.path.append("elevenlabs-mcp")
import json
import backoff
import websockets
from dotenv import load_dotenv
from elevenlabs_mcp.elevenlabs.mcp import AgentClient  # ✅ Fixed import

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")

class MCPStreamClient(AgentClient):
    def __init__(self, websocket):
        super().__init__(api_key=ELEVENLABS_API_KEY)
        self.websocket = websocket
        self.stability = 0.5
        self.similarity_boost = 0.75
        self.style = 0.1

    async def on_audio_chunk(self, chunk):
        await self.websocket.send(chunk)

    async def connect(self):
        self.ws = await websockets.connect(f"wss://api.elevenlabs.io/v1/mcp/stream")

    async def disconnect(self):
        if hasattr(self, "ws") and self.ws.open:
            await self.ws.close()

@backoff.on_exception(backoff.expo, Exception, max_tries=3)
async def stream_audio_mcp(text: str, websocket: websockets.WebSocketServerProtocol):
    try:
        client = MCPStreamClient(websocket)
        await client.connect()
        await client.generate(
            voice_id=ELEVENLABS_AGENT_ID,
            text=text,
            model="eleven_multilingual_v2",
            optimize_streaming_latency=True,
            stability=client.stability,
            similarity_boost=client.similarity_boost,
            style=client.style
        )
    except Exception as e:
        print(f"❌ MCP Audio Error: {e}")
        await websocket.send(json.dumps({"error": "Audio streaming failed"}))
    finally:
        await client.disconnect()