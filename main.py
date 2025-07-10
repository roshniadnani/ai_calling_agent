import os
import sys
import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from vonage import Client as VonageClient  # Using compatible client
from elevenlabs.client import ElevenLabs  # Using HTTP API instead of MCP
from dotenv import load_dotenv

# Configure system path
sys.path.append(str(Path("C:/Users/hp/Desktop/elevenlabs-mcp")))
load_dotenv()

app = FastAPI()

# Configure logging
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize Vonage client (compatible version)
vonage_client = VonageClient(
    key=os.getenv("VONAGE_API_KEY"),
    secret=os.getenv("VONAGE_API_SECRET"),
    application_id=os.getenv("VONAGE_APPLICATION_ID"),
    private_key=os.getenv("VONAGE_PRIVATE_KEY_PATH")
)

# Initialize ElevenLabs HTTP client
el_client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

@app.post("/vonage-webhook")
async def vonage_webhook(request: Request):
    """Handle Vonage call events including Smart Numbers"""
    try:
        data = await request.json()
        logging.info(f"Webhook received: {data}")
        
        # Smart Numbers detection
        if data.get('smart_number'):
            logging.info("Smart Numbers call detected")
            
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        raise HTTPException(400, detail=str(e))

@app.post("/make-call")
async def make_call(request: Request):
    """Initiate outbound call with Smart Numbers support"""
    try:
        data = await request.json()
        ncco = [{
            "action": "talk",
            "text": "Connecting your call..."
        }, {
            "action": "connect",
            "endpoint": [{
                "type": "websocket",
                "uri": f"wss://{os.getenv('APP_URL').replace('https://', '')}/ws",
                "content-type": "audio/l16;rate=16000"
            }]
        }]
        
        response = vonage_client.voice.create_call({
            "to": [{"type": "phone", "number": data['to_number']}],
            "from": {"type": "phone", "number": os.getenv("VONAGE_PHONE_NUMBER")},
            "smart": os.getenv("VONAGE_SMART_NUMBERS_ENABLED", "false").lower() == "true",
            "ncco": ncco
        })
        
        return {"status": "success", "call_id": response["uuid"]}
    except Exception as e:
        logging.error(f"Call failed: {str(e)}")
        raise HTTPException(500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle real-time audio streaming"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if 'text' in data:
                await stream_audio(data['text'], websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()

async def stream_audio(text: str, websocket: WebSocket):
    """Stream audio using ElevenLabs HTTP API"""
    try:
        # Generate and stream audio
        audio = el_client.generate(
            text=text,
            voice_id=os.getenv("ELEVENLABS_VOICE_ID"),
            model="eleven_monolingual_v2",
            stream=True
        )
        for chunk in audio:
            await websocket.send_bytes(chunk)
    except Exception as e:
        logging.error(f"Audio error: {str(e)}")
        # Fallback to static audio
        with open("static/fallback.wav", "rb") as f:
            await websocket.send_bytes(f.read())

@app.get("/health")
async def health_check():
    """System health endpoint"""
    return {
        "status": "healthy",
        "smart_numbers": os.getenv("VONAGE_SMART_NUMBERS_ENABLED", "false"),
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)