import os
import openai
from fastapi import FastAPI, Response, HTTPException
from dotenv import load_dotenv
from twilio.rest import Client
import requests

# Load environment variables from .env
load_dotenv()

# Initialize OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Twilio credentials
twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE")

# ElevenLabs credentials
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
DESIREE_AGENT_URL = os.getenv("DESIREE_AGENT_URL")

# Initialize Twilio client
client = Client(twilio_account_sid, twilio_auth_token)

# GPT conversation state
gpt_conversation = [
    {
        "role": "system",
        "content": "You are Desiree, a friendly insurance agent doing a home survey. Ask short and specific questions and do not chit-chat."
    },
    {
        "role": "user",
        "content": "Begin the survey call."
    }
]

# FastAPI app
app = FastAPI()

@app.get("/twiml")
async def twiml():
    try:
        # Get the next GPT response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=gpt_conversation
        )

        reply = response['choices'][0]['message']['content']
        gpt_conversation.append({"role": "assistant", "content": reply})

        # Generate ElevenLabs audio URL for Desiree's voice
        audio_url = generate_audio(reply)

        # Return TwiML with <Play> for dynamic audio
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
</Response>"""

        return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        print(f"Error in /twiml: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def generate_audio(text):
    """Generate audio from ElevenLabs Desiree agent"""
    response = requests.get(f"{DESIREE_AGENT_URL}&text={text}")
    if response.status_code == 200:
        return response.json().get("audio_url")
    else:
        raise Exception("Failed to generate audio: " + response.text)


@app.get("/make-call/{to_number}")
def make_call(to_number: str):
    try:
        print(f"Calling: {to_number}")
        call = client.calls.create(
            to=to_number,
            from_=twilio_number,
            url="https://ai-calling-agent-6mzv.onrender.com/twiml"  # ← FINAL Render URL here
        )
        print(f"Call SID: {call.sid}")
        return {"message": "Call initiated", "sid": call.sid}
    except Exception as e:
        print(f"Call error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
