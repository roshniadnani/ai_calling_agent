from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
import os
import openai
from elevenlabs.client import ElevenLabs
from google_sheets import log_response
from script_blocks import ScriptFlow
from generate_audio import generate_audio_for_text

load_dotenv()

app = FastAPI()
script_flow = ScriptFlow()

# Load API Keys
openai.api_key = os.getenv("OPENAI_API_KEY")
eleven = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

@app.get("/")
def root():
    return {"status": "AI Agent Live - Local Test Mode"}

@app.post("/webhooks/answer")
async def answer_call():
    block = script_flow.get_block("greeting")
    generate_audio_for_text(block.text)  # This will save to static/desiree_response.mp3
    return FileResponse("static/desiree_response.mp3", media_type="audio/mpeg")

@app.post("/webhooks/event")
async def handle_event(request: Request):
    event = await request.json()
    print("Vonage Event:", event)
    return JSONResponse(content={"status": "event received"})

@app.post("/call")
async def start_call(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    user_input = data.get("user_input")
    block_id = data.get("block_id", "greeting")

    block = script_flow.get_block(block_id)
    next_block_id = script_flow.get_next_block_id(block_id, user_input)

    if not next_block_id:
        return {"done": True, "message": "Survey complete or call ended."}

    next_block = script_flow.get_block(next_block_id)
    audio_path = generate_audio_for_text(next_block.text)

    background_tasks.add_task(log_response, data.get("caller_number"), block_id, user_input)

    return {
        "next_block": next_block.id,
        "text": next_block.text,
        "audio_url": f"/static/{os.path.basename(audio_path)}"
    }