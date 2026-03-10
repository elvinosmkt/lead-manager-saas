import asyncio
from scraper_otimizado import GoogleMapsScraperOtimizado
from webhook_trigger import send_n8n_webhook
import sys

def mock_progress(data):
    print("Progresso:", data)
    if data.get('latest_lead'):
        print(f"Disparando webhook para {data['latest_lead']['nome']}")
        send_n8n_webhook(data['latest_lead'])

if __name__ == "__main__":
    from config import CONFIG
    CONFIG['MAX_BUSINESSES'] = 3
    
    print("Iniciando Busca de Teste: Mecânicas em Joinville")
    scraper = GoogleMapsScraperOtimizado("mecanica", "Joinville", callback=mock_progress)
    leads = scraper.scrape()
    
    print(f"\nFinalizado! Foram encontrados leads sem site.")
