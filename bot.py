import os
import time
import hashlib
import requests

# 1. Configurações e Variáveis de Ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID")
SHOPEE_SECRET = os.getenv("SHOPEE_SECRET")

SHOPEE_GRAPHQL_URL = "https://open-api.affiliate.shopee.com.br/graphql"

def gerar_assinatura_shopee(payload_str, timestamp):
    """Gera a assinatura HMAC-SHA256 exigida pela API da Shopee."""
    base_string = f"{SHOPEE_APP_ID}{timestamp}{payload_str}{SHOPEE_SECRET}"
    return hashlib.sha256(base_string.encode('utf-8')).hexdigest()

def buscar_e_gerar_oferta():
    """Consulta a API de Afiliados da Shopee para obter uma oferta e o link encurtado."""
    timestamp = int(time.time())
    
    # Query GraphQL para buscar ofertas populares na Shopee
    query = """
    query {
      productOfferV2(page: 1, limit: 10, sortType: 1) {
        nodes {
          productName
          price
          priceMin
          priceMax
          imageUrl
          offerLink
        }
      }
    }
    """
    
    payload = {"query": query}
    payload_str = str(payload).replace("'", '"')
    
    signature = gerar_assinatura_shopee(payload_str, timestamp)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={SHOPEE_APP_ID}, Timestamp={timestamp}, Signature={signature}"
    }
    
    response = requests.post(SHOPEE_GRAPHQL_URL, json=payload, headers=headers)
    dados = response.json()
    
    # Valida o retorno da API
    if "data" in dados and "productOfferV2" in dados["data"]:
        produtos = dados["data"]["productOfferV2"]["nodes"]
        if produtos:
            import random
            produto = random.choice(produtos)
            return {
                "titulo": produto.get("productName"),
                "preco": f"R$ {float(produto.get('priceMin', 0)):.2f}",
                "link": produto.get("offerLink"),
                "imagem": produto.get("imageUrl")
            }
    return None

def enviar_telegram(oferta):
    """Envia a oferta formatada para o canal do Telegram."""
    mensagem = (
        f"🔥 <b>{oferta['titulo']}</b>\n\n"
        f"💥 Por apenas: <b>{oferta['preco']}</b>\n\n"
        f"🛒 <b>Compre aqui:</b> {oferta['link']}"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": oferta["imagem"],
        "caption": mensagem,
        "parse_mode": "HTML"
    }
    
    requests.post(url, json=payload)

if __name__ == "__main__":
    oferta = buscar_e_gerar_oferta()
    if oferta:
        enviar_telegram(oferta)
    else:
        print("Não foi possível obter ofertas da API no momento.")
