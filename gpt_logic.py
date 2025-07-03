# gpt_logic.py
import openai
import os
from dotenv import load_dotenv
from database import get_context, update_context

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_question(phone_number):
    context = get_context(phone_number)
    messages = [
        {"role": "system", "content": "You are a helpful interview assistant."},
        {"role": "user", "content": context['job_description']},
        {"role": "user", "content": context['resume']},
    ]
    for exchange in context.get("conversation", []):
        messages.append({"role": "assistant", "content": exchange['question']})
        messages.append({"role": "user", "content": exchange['answer']})

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages + [{"role": "system", "content": "Ask the next interview question."}]
    )
    question = completion.choices[0].message['content']
    return question

def save_answer(phone_number, question, answer):
    update_context(phone_number, question, answer)
