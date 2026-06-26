# app/core/config.py
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
MAX_TOKENS = 1024
MEMORY_WINDOW = 10                 # Keep last N messages per session

if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY is not set. Add it to your .env file.")

groq_llm = ChatGroq(
    model=MODEL,
    api_key=GROQ_API_KEY,
    temperature=0.4,
    max_tokens=MAX_TOKENS,
)
