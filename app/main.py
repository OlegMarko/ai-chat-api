from fastapi import FastAPI
from app.api import chat_router

app = FastAPI()
app.include_router(chat_router)
