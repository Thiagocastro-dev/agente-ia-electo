# Arquivo: src/llm/langchain_gemini.py (ou substituindo o conteúdo do langchain_azure.py)

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def get_llm():
    """
    Inicializa e retorna a instância do modelo Gemini via LangChain.
    """
    # Verifica se a chave foi carregada corretamente
    if not os.environ.get("GOOGLE_API_KEY"):
        raise ValueError("A variável de ambiente GOOGLE_API_KEY não está configurada.")

    # Inicializa o modelo Gemini (você pode escolher a versão, como gemini-1.5-flash ou gemini-1.5-pro)
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.7, # Ajuste a criatividade conforme necessário
        # max_output_tokens=1024, # Opcional: limite de tokens de resposta
    )
    
    return llm

# Teste simples de inicialização
if __name__ == "__main__":
    bot = get_llm()
    resposta = bot.invoke("Olá, quem é você?")
    print(resposta.content)