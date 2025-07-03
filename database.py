# database.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["interviewDB"]
collection = db["interviews"]

def save_context(phone_number, context):
    collection.update_one(
        {"phone_number": phone_number},
        {"$set": context},
        upsert=True
    )

def get_context(phone_number):
    return collection.find_one({"phone_number": phone_number}) or {}

def update_context(phone_number, question, answer):
    collection.update_one(
        {"phone_number": phone_number},
        {"$push": {"conversation": {"question": question, "answer": answer}}},
        upsert=True
    )

