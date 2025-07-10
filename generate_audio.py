import asyncio
from elevenlabs_mcp import MCPClient
from dotenv import load_dotenv
import os
import logging
from pathlib import Path

load_dotenv()
logging.basicConfig(filename='logs/audio_errors.log', level=logging.ERROR)

class AudioService:
    def __init__(self):
        self.client = MCPClient(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            agent_id=os.getenv("ELEVENLABS_AGENT_ID"),
            base_url=os.getenv("MCP_SERVER_URL", "http://localhost:5000")
        )
        self.fallback_audio = Path("static/fallback.wav")

    async def stream_audio(self, text: str, websocket):
        try:
            stream = self.client.stream(
                text=text,
                voice_id=os.getenv("ELEVENLABS_VOICE_ID"),
                model="eleven_turbo_v2",
                latency_optimization=4,
                stream_chunk_size=2048
            )
            
            async for chunk in stream:
                await websocket.send_bytes(chunk)
                await asyncio.sleep(0.01)  # 10ms delay between chunks
                
        except Exception as e:
            logging.error(f"Audio streaming failed: {str(e)}")
            await self.send_fallback(websocket)

    async def send_fallback(self, websocket):
        try:
            if self.fallback_audio.exists():
                with open(self.fallback_audio, "rb") as f:
                    await websocket.send_bytes(f.read())
        except Exception as e:
            logging.error(f"Fallback audio failed: {str(e)}")