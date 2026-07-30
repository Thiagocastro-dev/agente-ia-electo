from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from chat.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat_endpoint(request: ChatRequest):
    try:
        response_text = await chat_service.generate_response(
            session_id=request.session_id,
            user_message=request.message
        )
        return ChatResponse(response=response_text)
    except Exception as e:
        import logging
        logging.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/session/{session_id}", tags=["chat"])
async def clear_session(session_id: str):
    try:
        chat_service.chat_repo.clear_chat_history(session_id)
        return {"message": f"Chat history for session {session_id} successfully cleared."}
    except Exception as e:
        import logging
        logging.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
