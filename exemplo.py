"""
Exemplo de uso direto do scraper (sem input interativo)
"""
import asyncio
from scraper import GoogleMapsScraper


async def exemplo():
    # Configure aqui seu nicho e cidade
    nicho = "estética"
    cidade = "São Paulo, SP"
    
    print(f"🚀 Buscando leads de '{nicho}' em '{cidade}'...")
    
    # Cria e executa o scraper
    scraper = GoogleMapsScraper(nicho, cidade)
    await scraper.scrape()
    
    # Salva os resultados
    if scraper.businesses:
        scraper.save_to_excel()
        print(f"\n✅ {len(scraper.businesses)} leads encontrados!")
    else:
        print("\n⚠️ Nenhum lead encontrado.")


if __name__ == "__main__":
    asyncio.run(exemplo())
