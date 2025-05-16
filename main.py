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

# GPT conversation state (initial conversation)
gpt_conversation = [
    {"role": "system", "content": "You are Desiree, a friendly insurance agent doing a home survey. Ask short and specific questions and do not chit-chat."},
    {"role": "user", "content": "Begin the survey call."}
]

# FastAPI application setup
app = FastAPI()

@app.get("/twiml")
async def twiml():
    try:
        # Generate the next line using OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use the model you prefer
            messages=gpt_conversation
        )

        # Extract the response text from GPT
        reply = response['choices'][0]['message']['content']
        gpt_conversation.append({"role": "assistant", "content": reply})

        # Generate the audio file URL using ElevenLabs
        audio_url = generate_audio(reply)

        # Build the TwiML response with the generated voice
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>{reply}</Say>  <!-- This will speak the GPT-generated response -->
            <Play>{audio_url}</Play> <!-- Play Desiree's dynamic voice -->
        </Response>"""
        
        return Response(content=twiml, media_type="application/xml")
    
    except Exception as e:
        print(f"Error processing TwiML: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing TwiML: {str(e)}")

# Function to generate speech using ElevenLabs API
def generate_audio(text):
    """Generate audio using Desiree's agent URL (Desiree's voice from ElevenLabs)"""
    response = requests.get(f"{DESIREE_AGENT_URL}&text={text}")

    if response.status_code == 200:
        audio_url = response.json().get("audio_url")
        return audio_url
    else:
        raise HTTPException(status_code=500, detail="Error generating audio: " + response.text)

@app.get("/make-call/{to_number}")
def make_call(to_number: str):
    try:
        print(f"Making call to: {to_number}")
        
        # Attempt to initiate the call
        call = client.calls.create(
            to=to_number,  # The phone number to call
            from_=twilio_number,  # The Twilio number to call from
            url="http://127.0.0.1:8000/twiml"  # TwiML URL for the response
        )
        
        print(f"Call SID: {call.sid}")
        return {"message": "Call initiated", "call_sid": call.sid}
    
    except Exception as e:
        print(f"Error initiating call: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initiating call: {str(e)}")
