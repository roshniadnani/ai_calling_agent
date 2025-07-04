from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import backoff

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@backoff.on_exception(backoff.expo, Exception, max_tries=3)
async def generate_question_response(script_text: str, conversation_history: list[str]) -> str:
    prompt = f"""
    You are Desiree from Millennium Information Services, conducting a Homesite interview.
    Question: {script_text}
    History: {conversation_history}
    Provide a concise, professional follow-up (max 20 words).
    """
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=50
    )
    return response.choices[0].message.content.strip()

@backoff.on_exception(backoff.expo, Exception, max_tries=3)
async def simulate_user_response(script_text: str, conversation_history: list[str]) -> str:
    prompt = f"""
    You are a homeowner in a Homesite interview.
    Question: {script_text}
    History: {conversation_history}
    Provide a realistic, concise response (max 20 words).
    """
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50
    )
    return response.choices[0].message.content.strip()