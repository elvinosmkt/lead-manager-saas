#!/usr/bin/env python3
"""
Teste diagnóstico da busca
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_simples import GoogleMapsScraperSimples

print("🔍 TESTE DIAGNÓSTICO - BUSCA DE LEADS\n")
print("=" * 60)

# Teste básico
nicho = "barbearia"
cidade = "Curitiba, PR"
max_leads = 5

print(f"\n📊 Testando busca:")
print(f"   Nicho: {nicho}")
print(f"   Cidade: {cidade}")
print(f"   Máximo: {max_leads} leads\n")

try:
    scraper = GoogleMapsScraperSimples(nicho, cidade)
    print("✅ Scraper criado com sucesso")
    
    # Modifica config para teste rápido
    from config import CONFIG
    CONFIG['MAX_BUSINESSES'] = max_leads
    
    print("\n🚀 Iniciando busca...\n")
    scraper.scrape()
    
    leads = scraper.businesses
    
    print(f"\n" + "=" * 60)
    print(f"✅ BUSCA CONCLUÍDA!")
    print(f"📊 Total de leads encontrados: {len(leads)}")
    print("=" * 60)
    
    if leads:
        print(f"\n📋 Exemplo de lead coletado:")
        print(f"   Nome: {leads[0].get('nome', 'N/A')}")
        print(f"   Telefone: {leads[0].get('telefone', 'N/A')}")
        print(f"   WhatsApp: {'Sim' if leads[0].get('whatsapp') else 'Não'}")
        print(f"   Tem Site: {'Sim' if leads[0].get('tem_site') else 'Não'}")
        print(f"   Cidade: {leads[0].get('cidade', 'N/A')}")
        print(f"   Google Maps: {leads[0].get('google_maps_link', 'N/A')[:50]}...")
        
        print(f"\n✅ Campos disponíveis no lead:")
        for key in leads[0].keys():
            print(f"   - {key}")
    else:
        print("\n⚠️  NENHUM LEAD ENCONTRADO!")
        print("Possíveis causas:")
        print("   1. Nicho/cidade sem resultados")
        print("   2. Erro no scraping")
        print("   3. Elementos do Google Maps mudaram")
    
except Exception as e:
    print(f"\n❌ ERRO DURANTE O TESTE:")
    print(f"   {str(e)}")
    import traceback
    print(f"\n📋 Traceback completo:")
    traceback.print_exc()
    
print("\n" + "=" * 60)
print("🏁 TESTE FINALIZADO")
print("=" * 60 + "\n")
