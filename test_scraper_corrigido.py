#!/usr/bin/env python3
"""
Teste do scraper CORRIGIDO
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_corrigido import GoogleMapsScraperAtualizado

print("🧪 TESTE DO SCRAPER CORRIGIDO\n")
print("=" * 60)

nicho = "barbearia"
cidade = "Curitiba, PR"

print(f"\n📊 Teste rápido:")
print(f"   Nicho: {nicho}")
print(f"   Cidade: {cidade}")
print(f"   Máximo: 10 leads\n")

try:
    from config import CONFIG
    CONFIG['MAX_BUSINESSES'] = 10
    
    scraper = GoogleMapsScraperAtualizado(nicho, cidade)
    print("✅ Scraper corrigido criado\n")
    
    scraper.scrape()
    
    leads = scraper.businesses
    
    print(f"\n" + "=" * 60)
    if leads and len(leads) > 0:
        print(f"✅ SUCESSO! {len(leads)} leads coletados")
        print(f"\n📋 Primeiro lead:")
        print(f"   Nome: {leads[0]['nome']}")
        print(f"   Telefone: {leads[0].get('telefone', 'N/A')}")
        print(f"   WhatsApp: {leads[0].get('whatsapp', 'N/A')}")
        print(f"   Endereço: {leads[0].get('endereco', 'N/A')[:50]}...")
    else:
        print("⚠️  Nenhum lead coletado - verifique os seletores CSS")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
