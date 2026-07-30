import httpx
import os
import logging
from google import genai
from tempfile import NamedTemporaryFile

class AudioTranscriptionService:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        # Usaremos o modelo mais recente e capaz para transcrição
        self.model_name = "gemini-1.5-flash"

    async def transcribe_audio_from_url(self, url: str) -> str:
        """
        Baixa um arquivo de áudio de uma URL, salva-o temporariamente
        e o envia para a API do Gemini para transcrição.
        """
        try:
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(url, follow_redirects=True)
                response.raise_for_status()

            # Salva o conteúdo de áudio em um arquivo temporário
            with NamedTemporaryFile(delete=True, suffix=".ogg") as temp_file:
                temp_file.write(response.content)
                temp_file.flush()

                # Envia o arquivo para a API Gemini
                audio_file = self.client.files.create(
                    file_path=temp_file.name,
                    display_name="whatsapp_audio_message"
                )
                
                logging.info(f"Arquivo de áudio enviado para a API Gemini: {audio_file.name}")

                # Prepara o prompt para o modelo multimodal
                model = self.client.models.get(self.model_name)
                response = model.generate_content(
                    [
                        "Transcreva o seguinte áudio de um cliente da doceria de forma literal. Apenas o texto, sem adicionar nenhuma formatação ou comentário.",
                        audio_file
                    ]
                )
                
                # Limpa o arquivo após o uso
                self.client.files.delete(name=audio_file.name)
                
                return response.text.strip() if response.text else ""

        except httpx.HTTPStatusError as e:
            logging.error(f"Erro ao baixar o áudio: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado na transcrição: {e}")
            raise
