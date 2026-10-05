import os
import time
import requests

# Pegando as configurações salvas no servidor
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID")
SHOPEE_SECRET = os.getenv("SHOPEE_SECRET")

def enviar_mensagem_telegram(texto):
    """Envia a mensagem direto para o canal do Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": texto,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

def postar_oferta_teste():
    """Postagem automatizada de ofertas"""
    mensagem = (
        "🔥 *OFERTA IMPERDÍVEL DA SHOPEE!*\n\n"
        "📦 Confira os melhores achados de hoje no nosso canal!\n\n"
        "🛒 *Clique para aproveitar:* https://shopee.com.br"
    )
    enviar_mensagem_telegram(mensagem)

if __name__ == "__main__":
    print("Robô ativado com sucesso!")
    while True:
        postar_oferta_teste()
        # Aguarda 1 hora (3600 segundos) entre as postagens
        time.sleep(3600)
