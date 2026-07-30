from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from chat.chat_service import ChatService
from .transcription import AudioTranscriptionService

router = APIRouter()
chat_service = ChatService()
transcription_service = AudioTranscriptionService()

# --- Pydantic Models for WhatsApp Webhook ---
# (Estes são modelos genéricos. Você pode precisar ajustá-los
# dependendo do provedor de API do WhatsApp que escolher, ex: Twilio, Z-API)

class WhatsAppMessage(BaseModel):
    id: str
    from_number: str = Field(..., alias='from')
    type: str  # 'text' or 'audio'
    text: Optional[str] = None
    audio_url: Optional[str] = None # URL para baixar o arquivo de áudio

class WhatsAppWebhookPayload(BaseModel):
    messages: List[WhatsAppMessage]

# --- Webhook Endpoint ---

@router.post("/whatsapp/webhook", tags=["whatsapp"])
async def whatsapp_webhook(payload: WhatsAppWebhookPayload):
    """
    Este endpoint recebe notificações de novas mensagens do WhatsApp
    de um provedor de API (Gateway).
    """
    if not payload.messages:
        raise HTTPException(status_code=400, detail="No messages in payload")

    # Processa a primeira mensagem da lista
    message = payload.messages[0]
    session_id = f"whatsapp:{message.from_number}"
    
    try:
        if message.type == 'text':
            user_text = message.text
            if not user_text:
                logging.warning("Received empty text message.")
                return {"status": "ok", "message": "Empty text message ignored"}
        
        elif message.type == 'audio':
            if not message.audio_url:
                raise HTTPException(status_code=400, detail="Audio message missing URL")
            
            logging.info(f"Transcribing audio from {message.from_number}...")
            user_text = await transcription_service.transcribe_audio_from_url(message.audio_url)
            logging.info(f"Transcription complete: '{user_text}'")
            
        else:
            logging.warning(f"Unsupported message type: {message.type}")
            # Responda de forma cortês se o tipo não for suportado
            # (a lógica de resposta precisa ser implementada para enviar de volta ao gateway)
            return {"status": "ok", "message": "Unsupported message type ignored"}
            
        # Gera a resposta usando o serviço de chat existente
        response_text = await chat_service.generate_response(session_id, user_text)
        
        # AQUI: Lógica para enviar a 'response_text' de volta ao cliente
        # através do seu provedor de API do WhatsApp.
        # Ex: client.send_message(to=message.from_number, body=response_text)
        
        logging.info(f"Generated response for {session_id}: '{response_text}'")
        
        # Retorna uma representação da resposta que seria enviada
        return {
            "status": "success",
            "recipient": session_id,
            "response_sent": response_text
        }
        
    except Exception as e:
        logging.error(f"Error processing webhook for session {session_id}: {e}")
        # Retorne um erro 500 para que o gateway saiba que algo deu errado
        raise HTTPException(status_code=500, detail=str(e))
