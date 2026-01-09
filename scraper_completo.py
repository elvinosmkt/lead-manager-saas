"""
Versão que salva TODAS as empresas, mostrando quais têm/não têm site
"""
from scraper_selenium import GoogleMapsScraperSelenium
import pandas as pd
import os
from datetime import datetime
from config import CONFIG


class GoogleMapsScraperCompleto(GoogleMapsScraperSelenium):
    """Versão que coleta TODAS as empresas, independente de ter site ou WhatsApp"""
    
    def _collect_businesses(self):
        """Coleta informações de TODAS as empresas"""
        from selenium.webdriver.common.by import By
        import time
        
        print("\n📊 Coletando informações de TODAS as empresas...")
        
        try:
            # Scroll para carregar mais resultados
            self._scroll_results()
            
            # Pega todos os links de empresas
            print("🔎 Buscando links de empresas...")
            business_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
            
            if not business_links:
                print("⚠️ Nenhuma empresa encontrada")
                return
            
            total = min(len(business_links), CONFIG["MAX_BUSINESSES"])
            print(f"📍 Encontradas {len(business_links)} empresas. Processando até {total}...\n")
            
            for idx in range(total):
                try:
                    # Re-busca os links a cada iteração
                    business_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
                    if idx >= len(business_links):
                        break
                    
                    print(f"[{idx+1}/{total}] Processando empresa...")
                    
                    # Clica no negócio
                    business_links[idx].click()
                    time.sleep(3)
                    
                    # Extrai as informações
                    business_data = self._extract_business_info()
                    
                    if business_data:
                        # Adiciona TODAS as empresas
                        # Marca status
                        business_data['tem_site'] = 'Sim' if business_data.get('website') else 'Não'
                        business_data['tem_whatsapp'] = 'Sim' if business_data.get('whatsapp') else 'Não'
                        
                        self.businesses.append(business_data)
                        
                        status = []
                        if not business_data.get('website'):
                            status.append("SEM SITE")
                        if business_data.get('whatsapp'):
                            status.append("COM WHATSAPP")
                        
                        if status:
                            print(f"✅ {business_data['nome']} [{', '.join(status)}]")
                        else:
                            print(f"📋 {business_data['nome']}")
                    
                    time.sleep(CONFIG["DELAY_BETWEEN_BUSINESSES"])
                    
                except Exception as e:
                    print(f"⚠️ Erro ao processar empresa {idx+1}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"❌ Erro ao coletar empresas: {str(e)}")
    
    def save_to_excel(self, filename: str = None):
        """Salva TODAS as empresas com indicador de site/whatsapp"""
        if not self.businesses:
            print("⚠️ Nenhuma empresa para salvar!")
            return
        
        os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cidade_limpa = self.cidade.replace(",", "").replace(" ", "_")
            filename = f"{CONFIG['OUTPUT_DIR']}/todas_empresas_{self.nicho}_{cidade_limpa}_{timestamp}.xlsx"
        
        df = pd.DataFrame(self.businesses)
        
        # Reordena as colunas
        columns = ['nome', 'tem_site', 'tem_whatsapp', 'telefone', 'whatsapp',  'endereco', 'avaliacao', 'num_avaliacoes', 'website']
        df = df[[col for col in columns if col in df.columns]]
        
        # Salva no Excel
        df.to_excel(filename, index=False, engine='openpyxl')
        
        # Estatísticas
        sem_site = len([b for b in self.businesses if not b.get('website')])
        com_whatsapp = len([b for b in self.businesses if b.get('whatsapp')])
        leads_qualificados = len([b for b in self.businesses if not b.get('website') and b.get('whatsapp')])
        
        print(f"\n📊 Arquivo salvo: {filename}")
        print(f"📈 Total de empresas: {len(self.businesses)}")
        print(f"🔍 Sem website: {sem_site}")
        print(f"💬 Com WhatsApp: {com_whatsapp}")
        print(f"🎯 Leads qualificados (sem site + com WhatsApp): {leads_qualificados}")
        
        return filename


def main():
    print("=" * 60)
    print("🎯 GOOGLE MAPS - TODAS AS EMPRESAS")
    print("=" * 60)
    
    nicho = input("\n📌 Digite o nicho (ex: estética): ").strip()
    cidade = input("📍 Digite a cidade e estado (ex: Curitiba, PR): ").strip()
    
    if not nicho or not cidade:
        print("❌ Nicho e cidade são obrigatórios!")
        return
    
    print(f"\n🚀 Iniciando busca por '{nicho}' em '{cidade}'...")
    print("⏳ Isso pode levar alguns minutos...\n")
    
    scraper = GoogleMapsScraperCompleto(nicho, cidade)
    
    try:
        scraper.scrape()
        
        if scraper.businesses:
            scraper.save_to_excel()
            print("\n✅ Processo concluído com sucesso!")
        else:
            print("\n⚠️ Nenhuma empresa encontrada.")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")


if __name__ == "__main__":
    main()
