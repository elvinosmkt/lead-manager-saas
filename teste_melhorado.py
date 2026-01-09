"""
Teste rápido do scraper melhorado
"""
from scraper_melhorado import GoogleMapsScraperMelhorado


def main():
    nicho = "estética"
    cidade = "Curitiba, PR"
    
    print("🧪 TESTE DO SCRAPER MELHORADO")
    print("=" * 60)
    print(f"📌 {nicho} em {cidade}")
    print("🔍 Apenas empresas SEM site + COM WhatsApp\n")
    
    scraper = GoogleMapsScraperMelhorado(nicho, cidade)
    
    try:
        scraper.scrape()
        
        if scraper.businesses:
            scraper.save_to_excel()
            print("\n✅ Teste concluído!")
        else:
            print("\n⚠️ Nenhum lead encontrado neste teste.")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")


if __name__ == "__main__":
    main()
