# twilio_logic.py
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from fastapi.responses import Response
import os
from dotenv import load_dotenv
load_dotenv()


TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
NGROK_URL = os.getenv("PUBLIC_BASE_URL")

client = Client(TWILIO_SID, TWILIO_AUTH)

def initiate_call(phone_number: str) -> str:
    call = client.calls.create(
    url=f"{NGROK_URL}/twilio/voice",  # make sure NGROK_URL is defined
    to=phone_number,
    from_=TWILIO_NUMBER
)


    
    return call.sid

def handle_twilio_callback(request) -> Response:
    response = VoiceResponse()
    response.say("Hello, welcome to the AI voice interview.")
    response.record(
        timeout=5,
        transcribe=True,
        action=f"{NGROK_URL}/twilio/next-question",
        method="POST"
    )
    return Response(content=str(response), media_type="application/xml")


