from fastapi import FastAPI
from ingestion.api import router as ingestion_router
from chat.api import router as chat_router
from whatsapp.api import router as whatsapp_router

app = FastAPI(
    title="Doceria Doce Vida - Assistente de Vendas RAG",
    description="API para o assistente de vendas da doceria, com ingestão de dados, chat e webhook para WhatsApp.",
    version="1.0.0"
)

app.include_router(ingestion_router, prefix="/v1")
app.include_router(chat_router, prefix="/v1")
app.include_router(whatsapp_router, prefix="/v1")


@app.get("/")
async def root():
    return {"message": "HelloAPI!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=7000)