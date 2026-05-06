from fastapi import APIRouter
from app.services import generate_response
from app.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = generate_response(message=req.message, session_id=req.session_id)
    return ChatResponse(response=reply)
