"""
Script de teste: Estética em Curitiba
"""
import asyncio
from scraper import GoogleMapsScraper


async def main():
    # Parâmetros do teste
    nicho = "estética"
    cidade = "Curitiba, PR"
    
    print("=" * 60)
    print("🎯 BUSCANDO LEADS NO GOOGLE MAPS")
    print("=" * 60)
    print(f"\n📌 Nicho: {nicho}")
    print(f"📍 Cidade: {cidade}")
    print(f"\n🚀 Iniciando busca...")
    print("⏳ Isso pode levar alguns minutos...\n")
    
    # Cria e executa o scraper
    scraper = GoogleMapsScraper(nicho, cidade)
    await scraper.scrape()
    
    # Salva os resultados
    if scraper.businesses:
        scraper.save_to_excel()
        print(f"\n✅ Sucesso! {len(scraper.businesses)} leads prontos para contato!")
    else:
        print("\n⚠️ Nenhuma empresa encontrada com os critérios:")
        print("   - Sem website")
        print("   - Com WhatsApp")


if __name__ == "__main__":
    asyncio.run(main())
