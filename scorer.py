# scorer.py
import openai
import os
from dotenv import load_dotenv
from database import get_context

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_and_score(phone_number):
    context = get_context(phone_number)
    conversation = context.get("conversation", [])

    if not conversation:
        return {"summary": "No answers recorded.", "score": 0}

    messages = [
        {"role": "system", "content": "You are a hiring expert analyzing candidate responses."},
        {"role": "user", "content": f"Here is the job description: {context['job_description']}"},
        {"role": "user", "content": f"Here is the resume: {context['resume']}"},
        {"role": "user", "content": f"Conversation: {conversation}"}
    ]

    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages + [{"role": "system", "content": "Give a summary and score (out of 10)."}]
    )

    content = result.choices[0].message['content']
    return {"summary_and_score": content}
