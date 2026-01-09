"""
Teste: Coleta TODAS as empresas de estética em Curitiba
"""
from scraper_completo import GoogleMapsScraperCompleto


def main():
    nicho = "estética"
    cidade = "Curitiba, PR"
    
    print("=" * 60)
    print("🎯 COLETANDO TODAS AS EMPRESAS")
    print("=" * 60)
    print(f"\n📌 Nicho: {nicho}")
    print(f"📍 Cidade: {cidade}")
    print(f"\n🚀 Buscando TODAS as empresas (com e sem site)...")
    print("⏳ Aguarde...\n")
    
    scraper = GoogleMapsScraperCompleto(nicho, cidade)
    
    try:
        scraper.scrape()
        
        if scraper.businesses:
            scraper.save_to_excel()
            print("\n✅ Planilha gerada com sucesso!")
            print("\n💡 Dica: Você pode filtrar no Excel por 'tem_site' = Não")
        else:
            print("\n⚠️ Nenhuma empresa encontrada.")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")


if __name__ == "__main__":
    main()
