import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from vonage import Webhook
from vonage.voice import Voice
from elevenlabs_mcp import MCPClient
from dotenv import load_dotenv

# Configure system path for MCP
sys.path.append(str(Path("C:/Users/hp/Desktop/elevenlabs-mcp")))
load_dotenv()

# Initialize FastAPI with middleware
app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware)

# Configure logging
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize clients
vonage_voice = Voice(
    key=os.getenv("VONAGE_API_KEY"),
    secret=os.getenv("VONAGE_API_SECRET"),
    application_id=os.getenv("VONAGE_APPLICATION_ID"),
    private_key=os.getenv("VONAGE_PRIVATE_KEY_PATH")
)

mcp_client = MCPClient(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
    agent_id=os.getenv("ELEVENLABS_AGENT_ID"),
    base_url=os.getenv("MCP_SERVER_URL", "http://localhost:5000"),
    webhook_url=os.getenv("ELEVENLABS_WEBHOOK_URL")
)

# Global state
active_calls = {}

@app.on_event("startup")
async def startup():
    """Initialize resources"""
    logging.info("Starting up AI Calling Agent")
    await mcp_client.warmup()

@app.post("/vonage-webhook")
async def handle_vonage_webhook(request: Request):
    """Handle all Vonage call events"""
    try:
        # Verify signed webhook
        webhook = Webhook(
            dict(request.query_params),
            dict(request.headers),
            os.getenv("VONAGE_SIGNATURE_SECRET")
        )
        data = await request.json()
        logging.info(f"Vonage Webhook: {data}")

        # Handle different event types
        event_type = data.get('status')
        call_id = data.get('uuid')

        if event_type == "started":
            active_calls[call_id] = {
                "status": "in-progress",
                "start_time": data.get('start_time')
            }
        elif event_type == "completed":
            active_calls.pop(call_id, None)

        return JSONResponse({"status": "processed"})

    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        raise HTTPException(400, detail="Invalid webhook")

@app.post("/elevenlabs-webhook")
async def handle_elevenlabs_webhook(request: Request):
    """Handle ElevenLabs audio generation events"""
    try:
        data = await request.json()
        logging.info(f"ElevenLabs Webhook: {data}")
        return {"status": "received"}
    except Exception as e:
        logging.error(f"ElevenLabs webhook error: {str(e)}")
        raise HTTPException(400, detail=str(e))

@app.post("/call")
async def initiate_call(request: Request):
    """Initiate outbound call"""
    try:
        data = await request.json()
        to_number = data['to_number']
        is_smart = data.get('smart_number', False)

        ncco = [
            {
                "action": "connect",
                "endpoint": [
                    {
                        "type": "websocket",
                        "uri": f"wss://{os.getenv('APP_URL').replace('https://', '')}/ws",
                        "content-type": "audio/l16;rate=16000",
                        "headers": {
                            "caller": os.getenv("VONAGE_PHONE_NUMBER"),
                            "callee": to_number,
                            "smart_number": str(is_smart)
                        }
                    }
                ]
            }
        ]

        response = vonage_voice.create_call({
            "to": [{"type": "phone", "number": to_number}],
            "from": {"type": "phone", "number": os.getenv("VONAGE_PHONE_NUMBER")},
            "ncco": ncco,
            "smart": is_smart  # Smart Numbers flag
        })

        call_id = response['uuid']
        active_calls[call_id] = {
            "status": "initiated",
            "to_number": to_number,
            "smart_number": is_smart
        }

        return JSONResponse({
            "status": "success",
            "call_id": call_id
        })

    except Exception as e:
        logging.error(f"Call initiation failed: {str(e)}")
        raise HTTPException(500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle real-time audio streaming"""
    await websocket.accept()
    try:
        # Authenticate connection
        headers = dict(websocket.headers)
        caller = headers.get('caller')
        callee = headers.get('callee')
        is_smart = headers.get('smart_number', 'false').lower() == 'true'

        if not caller or not callee:
            await websocket.close(code=1008)
            return

        while True:
            data = await websocket.receive_json()
            
            # Process audio streaming
            if data.get('type') == 'audio':
                await handle_audio_stream(data, websocket, is_smart)
            elif data.get('type') == 'hangup':
                break

    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()

async def handle_audio_stream(data: dict, websocket: WebSocket, is_smart: bool):
    """Process audio chunks with MCP"""
    try:
        text = data.get('text')
        if not text:
            return

        # Smart Numbers specific processing
        if is_smart:
            text = f"[SMART] {text}"

        async for chunk in mcp_client.stream(
            text=text,
            voice_id=os.getenv("ELEVENLABS_VOICE_ID"),
            model="eleven_turbo_v2",
            latency_optimization=4
        ):
            await websocket.send_bytes(chunk)
            await asyncio.sleep(0.01)  # 10ms delay

    except Exception as e:
        logging.error(f"Audio streaming error: {str(e)}")
        # Fallback to static audio
        with open("static/fallback.wav", "rb") as f:
            await websocket.send_bytes(f.read())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_calls": len(active_calls),
        "version": "1.0.0"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return {
        "active_calls": len(active_calls),
        "mcp_status": "connected" if mcp_client.connected else "disconnected"
    }