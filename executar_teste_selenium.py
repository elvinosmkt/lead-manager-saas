"""
Script de teste: Estética em Curitiba (Selenium)
"""
from scraper_selenium import GoogleMapsScraperSelenium


def main():
    # Parâmetros do teste
    nicho = "estética"
    cidade = "Curitiba, PR"
    
    print("=" * 60)
    print("🎯 BUSCANDO LEADS NO GOOGLE MAPS (SELENIUM)")
    print("=" * 60)
    print(f"\n📌 Nicho: {nicho}")
    print(f"📍 Cidade: {cidade}")
    print(f"\n🚀 Iniciando busca...")
    print("⏳ Isso pode levar alguns minutos...\n")
    
    # Cria e executa o scraper
    scraper = GoogleMapsScraperSelenium(nicho, cidade)
    
    try:
        scraper.scrape()
        
        # Salva os resultados
        if scraper.businesses:
            scraper.save_to_excel()
            print(f"\n✅ Sucesso! {len(scraper.businesses)} leads prontos para contato!")
        else:
            print("\n⚠️ Nenhuma empresa encontrada com os critérios:")
            print("   - Sem website")
            print("   - Com WhatsApp")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")


if __name__ == "__main__":
    main()
