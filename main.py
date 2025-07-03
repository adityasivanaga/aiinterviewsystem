from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from transcriptions import transcribe_twilio_recording



load_dotenv()

app = FastAPI()

# Load env variables
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
PUBLIC_URL = os.getenv("PUBLIC_URL")

client = Client(TWILIO_SID, TWILIO_AUTH)

class CallRequest(BaseModel):
    phone_number: str

@app.post("/call")
def call(request: CallRequest):
    call = client.calls.create(
        to=request.phone_number,
        from_=TWILIO_NUMBER,
        url=f"https://8537-125-62-207-143.ngrok-free.app/twilio/voice"
    )
    return {"message": "Calling now...", "sid": call.sid}


@app.post("/twilio/voice")
async def twilio_voice(request: Request):
    print("📞 Incoming call received")
    response = VoiceResponse()
    for x in range(5):
        # response.say("Hello! Welcome to the AI voice interview. Please answer the following question. Please State your name.")
        response.say('Please respond to question' + str(x))

        response.record(
            timeout=2,
            maxLength=30,
            action="/twilio/recording",  # Twilio sends the recording here
            recordingStatusCallback="/twilio/recording",
            method="POST"

        )
    print("📞 Responding to Twilio with voice instructions")
    
    
                 
                 
     
    return Response(content=str(response), media_type="application/xml")

@app.post("/twilio/recording")
async def handle_recording(request: Request):
    form = await request.form()
    recording_url = form.get("RecordingUrl")

    print(f"📼 Candidate response recorded: {recording_url}")

    # # Respond with a thank-you message
    # response = VoiceResponse()
    # response.say("Thank you. Your response has been recorded.")
    # response.hangup()

    recording_url = form.get("RecordingUrl")
    transcription = transcribe_twilio_recording(recording_url)
    print(transcription)

    # Respond to Twilio with the next prompt
    # response = VoiceResponse()
    # response.say("Thanks, moving on to the next question.")
    # response.record(
    #     timeout=2,
    #     maxLength=30,
    #     action="/twilio/recording",
    #     method="POST"
    # )
    return Response(content=str(transcription), media_type="application/xml")



# Now save this text to context or send to GPT
