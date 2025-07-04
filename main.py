from fastapi import FastAPI, Request, Form, Query, Body
from fastapi.responses import Response
from pydantic import BaseModel
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv
import os
import requests
from transcriptions import transcribe_audio_file
from pymongo import MongoClient
import time


load_dotenv()

app = FastAPI()

# Twilio config
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
PUBLIC_URL = os.getenv("PUBLIC_URL")

# Remote config
QUESTION_API_URL = os.getenv("QUESTION_API_URL")  # e.g., https://laptop-c.ngrok.app/next-question

client = Client(TWILIO_SID, TWILIO_AUTH)

# MongoDB setup
mongo_client = MongoClient("mongodb+srv://adityuhsiv:DontForget123@cluster0.s5n1lug.mongodb.net/")
db = mongo_client["interview"]
collection = db["conversations"]

class CallRequest(BaseModel):
    phone_number: str
    job_description: str
    job_resume: str

@app.post("/call")
def initiate_call(request: CallRequest = Body(...)):
    session_id = str(uuid4())  # generate session_id first

    # Store session in MongoDB
    collection.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "session_id": session_id,
                "phone_number": request.phone_number,
                "job_description": request.job_description,
                "job_resume": request.job_resume,
                "context": []
            }
        },
        upsert=True
    )

    # ✅ Embed the session_id in the webhook URL right here
    call = client.calls.create(
        to=request.phone_number,
        from_=TWILIO_NUMBER,
        url=f"https://fd82-122-171-188-194.ngrok-free.app/twilio/voice?q=0&session_id={session_id}"
    )

    return {"message": "Calling now...", "sid": call.sid, "session_id": session_id}
from uuid import uuid4


@app.post("/twilio/voice")
async def twilio_voice(request: Request, q: int = 0, session_id: str = Query(...)):
    form = await request.form()
    call_sid = form.get("CallSid")
    print(f"☎️ Incoming call SID: {call_sid}, Question index: {q}")

    response = VoiceResponse()
    time.sleep(5)
    # Fetch next question from external API
    try:
        r = requests.get(f"https://7406-2a09-bac5-3b25-1aa0-00-2a7-6e.ngrok-free.app/generate-remote-question?session_id={session_id}")
        r.raise_for_status()
        question_data = r.json()
        question = question_data.get("question", "Sorry, no question available at the moment.")
    except Exception as e:
        print(f"❌ Error fetching question: {e}")
        question = "There was an error retrieving your next interview question."

    response.say(question)
    response.record(
        timeout=2,
        maxLength=30,
        action=f"https://fd82-122-171-188-194.ngrok-free.app/twilio/recording?call_sid={call_sid}&q={q}&session_id={session_id}",
        recordingStatusCallback=f"https://fd82-122-171-188-194.ngrok-free.app/twilio/recording?call_sid={call_sid}&q={q}&session_id={session_id}",
        method="POST"
    )

    return Response(content=str(response), media_type="application/xml")

@app.post("/twilio/recording")
async def twilio_recording(request: Request):
    form = await request.form()
    query_params = request.query_params
    call_sid = query_params.get("call_sid")
    session_id = query_params.get("session_id")
    q = int(query_params.get("q", 0))

    recording_url = form.get("RecordingUrl") + ".mp3"
    print(f"📼 Recording received: {recording_url}")

    filename = f"{call_sid}_q{q}.mp3"
    auth = (TWILIO_SID, TWILIO_AUTH)
    audio = requests.get(recording_url, auth=auth)

    if audio.status_code == 200:
        with open(filename, "wb") as f:
            f.write(audio.content)
        print(f"✅ Saved recording: {filename}")
        transcription = transcribe_audio_file(filename)
        print(f"📝 Transcription: {transcription}")
    else:
        print(f"❌ Failed to download recording: {audio.status_code}")

    response = VoiceResponse()
    next_q = q + 1
    if next_q < 5:
        response.redirect(f"https://fd82-122-171-188-194.ngrok-free.app/twilio/voice?q={next_q}&session_id={session_id}", method="POST")
    else:
        response.say("Thank you. The interview is complete.")
        response.hangup()

    return Response(content=str(response), media_type="application/xml")

class QuestionPayload(BaseModel):
    session_id: str
    question: str

@app.post("/receive-question")
async def receive_question(payload: QuestionPayload):
    print(f"📥 Received question for session {payload.session_id}: {payload.question}")
    return {"status": "received", "question": payload.question}


@app.get("/get-profile")
async def get_profile(session_id: str = Query(...)):
    profile = collection.find_one({"session_id": session_id})
    if not profile:
        return {"error": "Session not found"}

    return {
        "job_description": profile.get("job_description", ""),
        "job_resume": profile.get("job_resume", "")
    }
