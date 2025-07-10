import os
import sys
import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from vonage import Voice
from elevenlabs_mcp import MCPClient
from dotenv import load_dotenv

# Configure system path for MCP
sys.path.append(str(Path("C:/Users/hp/Desktop/elevenlabs-mcp")))
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Configure logging
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize Vonage client with Smart Numbers support
vonage_voice = Voice(
    key=os.getenv("VONAGE_API_KEY"),
    secret=os.getenv("VONAGE_API_SECRET"),
    application_id=os.getenv("VONAGE_APPLICATION_ID"),
    private_key=os.getenv("VONAGE_PRIVATE_KEY_PATH")
)

# Initialize ElevenLabs MCP client
mcp_client = MCPClient(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
    agent_id=os.getenv("ELEVENLABS_AGENT_ID"),
    base_url=os.getenv("MCP_SERVER_URL", "http://localhost:5000")
)

@app.post("/vonage-webhook")
async def vonage_webhook(request: Request):
    try:
        data = await request.json()
        logging.info(f"Vonage webhook received: {data}")
        
        # Handle Smart Numbers events
        if data.get('smart_number'):
            logging.info("Smart Numbers event detected")
            
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        raise HTTPException(400, detail=str(e))

@app.post("/make-call")
async def make_call(request: Request):
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
        
        call_params = {
            "to": [{"type": "phone", "number": data['to_number']}],
            "from": {"type": "phone", "number": os.getenv("VONAGE_PHONE_NUMBER")},
            "ncco": ncco,
            "smart": os.getenv("VONAGE_SMART_NUMBERS_ENABLED", "false").lower() == "true"
        }
        
        response = vonage_voice.create_call(call_params)
        return {"status": "success", "call_id": response["uuid"]}
        
    except Exception as e:
        logging.error(f"Call failed: {str(e)}")
        raise HTTPException(500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Process call data
            await process_call_data(data, websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()

async def process_call_data(data: dict, websocket: WebSocket):
    """Process incoming call data"""
    try:
        if 'text' in data:
            await stream_audio(data['text'], websocket)
    except Exception as e:
        logging.error(f"Processing error: {str(e)}")

async def stream_audio(text: str, websocket: WebSocket):
    """Stream audio using MCP"""
    try:
        async for chunk in mcp_client.stream(text):
            await websocket.send_bytes(chunk)
    except Exception as e:
        logging.error(f"Audio streaming failed: {str(e)}")
        # Fallback to static audio
        with open("static/fallback.wav", "rb") as f:
            await websocket.send_bytes(f.read())

@app.get("/health")
async def health_check():
    return {"status": "healthy", "smart_numbers": os.getenv("VONAGE_SMART_NUMBERS_ENABLED", "false")}

# For Gunicorn compatibility
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)