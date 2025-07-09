from fastapi import FastAPI, WebSocket
from gpt_utils import ask_gpt
from generate_audio import stream_mcp_audio
from google_sheets import log_response
from script_blocks import ScriptFlow
from fastapi.responses import HTMLResponse
import uuid

app = FastAPI()
script = ScriptFlow()

@app.get("/")
def index():
    return HTMLResponse("<h2>AI Calling Agent is running</h2>")

@app.get("/call")
async def simulate_call():
    conversation_id = str(uuid.uuid4())
    print(f"\n📞 Starting call simulation: {conversation_id}")
    for block in script.blocks:
        print(f"🤖 Desiree: {block['text']}")
        if block.get("question"):
            response = await ask_gpt(block["text"])
            print(f"🗣️ User: {response}")
            await log_response(conversation_id, block["id"], response)
        if block.get("end_call"):
            print("📴 Call ended.\n")
            break
    return {"status": "Call completed", "conversation_id": conversation_id}

@app.websocket("/call_socket/{conversation_id}")
async def call_socket(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    print(f"\n🔗 MCP socket opened for: {conversation_id}")
    for block in script.blocks:
        if block.get("skip_if_answered"):
            continue
        await websocket.send_text(block["text"])
        if block.get("question"):
            user_reply = await websocket.receive_text()
            if not user_reply.strip() and block.get("requires_response"):
                clarification = await ask_gpt("Please rephrase or clarify that.")
                await websocket.send_text(clarification)
                user_reply = await websocket.receive_text()
            await log_response(conversation_id, block["id"], user_reply)
        if block.get("end_call"):
            await websocket.send_text("Thank you. Goodbye!")
            await websocket.close()
            print(f"📴 Call ended: {conversation_id}")
            break
