import os
import time
import hashlib
import requests
import json

# 1. Configurações e Variáveis de Ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID")
SHOPEE_SECRET = os.getenv("SHOPEE_SECRET")

SHOPEE_GRAPHQL_URL = "https://open-api.affiliate.shopee.com.br/graphql"
HISTORICO_FILE = "historico_posts.json"

def gerar_assinatura_shopee(payload_str, timestamp):
    """Gera a assinatura HMAC-SHA256 exigida pela API da Shopee."""
    base_string = f"{SHOPEE_APP_ID}{timestamp}{payload_str}{SHOPEE_SECRET}"
    return hashlib.sha256(base_string.encode('utf-8')).hexdigest()

def carregar_historico():
    """Carrega a lista de produtos já postados para evitar repetição."""
    if os.path.exists(HISTORICO_FILE):
        try:
            with open(HISTORICO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_historico(historico):
    """Salva a lista atualizada de produtos postados."""
    with open(HISTORICO_FILE, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

def buscar_e_gerar_oferta():
    """Consulta a API de Afiliados da Shopee e evita produtos repetidos."""
    timestamp = int(time.time())
    
    query = """
    query {
      productOfferV2(page: 1, limit: 30, sortType: 1) {
        nodes {
          itemId
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
    
    if "data" in dados and "productOfferV2" in dados["data"]:
        produtos = dados["data"]["productOfferV2"]["nodes"]
        if produtos:
            historico = carregar_historico()
            
            # Filtra apenas os produtos que NÃO estão no histórico recente
            produtos_disponiveis = [p for p in produtos if str(p.get("itemId")) not in historico]
            
            # Se todos já foram postados, limpa o histórico para recomeçar o ciclo
            if not produtos_disponiveis:
                produtos_disponiveis = produtos
                historico = []
            
            import random
            produto = random.choice(produtos_disponiveis)
            
            # Guarda no histórico (mantém os últimos 50 produtos)
            item_id = str(produto.get("itemId"))
            historico.append(item_id)
            if len(historico) > 50:
                historico.pop(0)
            salvar_historico(historico)
            
            # Formata os preços
            preco_atual = float(produto.get('priceMin', 0))
            if preco_atual == 0:
                preco_atual = float(produto.get('price', 0))
                
            preco_por = f"R$ {preco_atual:.2f}"
            preco_de = f"R$ {preco_atual * 1.35:.2f}" # Exibe um valor de referência cortado
            
            return {
                "titulo": produto.get("productName"),
                "preco_de": preco_de,
                "preco_por": preco_por,
                "link": produto.get("offerLink"),
                "imagem": produto.get("imageUrl")
            }
    return None

def enviar_telegram(oferta):
    """Envia a oferta formatada com aviso de alteração de preço para o canal."""
    mensagem = (
        f"🔥 <b>{oferta['titulo']}</b>\n\n"
        f"❌ De: <s>{oferta['preco_de']}</s>\n"
        f"✅ Por apenas: <b>{oferta['preco_por']}</b>\n\n"
        f"🛒 <b>Compre aqui:</b> {oferta['link']}\n\n"
        f"⚠️ <i>Atenção: Os preços e a disponibilidade podem sofrer alterações a qualquer momento pela loja. Corra para garantir o seu!</i>"
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
