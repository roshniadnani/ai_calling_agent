import os
import base64
import httpx
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")
APP_URL = os.getenv("APP_URL")

HEADERS = {
    "xi-api-key": ELEVENLABS_API_KEY,
    "Content-Type": "application/json"
}

async def stream_mcp_audio(text: str, conversation_id: str = "call1") -> str:
    """
    Sends the text to ElevenLabs MCP and returns the MP3 file path.
    """
    payload = {
        "agent_id": ELEVENLABS_AGENT_ID,
        "voice_id": "default",  # optional, agent voice takes priority
        "text": text,
        "stream": False,
        "config": {
            "output_format": "mp3_44100_128",
            "latency_optimization_level": 3
        },
        "tools": {
            "webhook_url": f"{APP_URL}/call_socket/{conversation_id}"
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.elevenlabs.io/v1/agents/stream",
            json=payload,
            headers=HEADERS
        )

    if response.status_code != 200:
        raise Exception(f"Audio generation failed: {response.text}")

    # Save audio to file
    audio_data = response.content
    output_path = f"static/desiree_response.mp3"
    with open(output_path, "wb") as f:
        f.write(audio_data)

    return output_path
