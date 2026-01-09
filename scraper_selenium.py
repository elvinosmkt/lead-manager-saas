"""
Versão alternativa usando Selenium (mais estável que Playwright)
Instale com: pip install selenium webdriver-manager
"""
import time
import re
import os
from datetime import datetime
import pandas as pd
from config import CONFIG

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("❌ Selenium não está instalado!")
    print("Execute: pip install selenium webdriver-manager")
    exit(1)


class GoogleMapsScraperSelenium:
    def __init__(self, nicho: str, cidade: str):
        self.nicho = nicho
        self.cidade = cidade
        self.businesses = []
        self.driver = None
    
    def scrape(self):
        """Executa o processo completo de scraping"""
        print("🌐 Iniciando navegador Chrome...")
        
        # Configurações do Chrome
        chrome_options = Options()
        if CONFIG["HEADLESS"]:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Inicia o driver
            import os
            import glob
            
            # Baixa/localiza o ChromeDriver
            driver_path = ChromeDriverManager().install()
            driver_dir = os.path.dirname(driver_path)
            
            # Procura pelo executável chromedriver (não os arquivos de licença)
            chromedriver_path = None
            for file in os.listdir(driver_dir):
                if file == 'chromedriver' and not file.endswith('.chromedriver'):
                    chromedriver_path = os.path.join(driver_dir, file)
                    break
            
            if not chromedriver_path or not os.path.exists(chromedriver_path):
                raise Exception(f"ChromeDriver não encontrado em {driver_dir}")
            
            # Garante que tem permissão de execução
            os.chmod(chromedriver_path, 0o755)
            
            print(f"✓ ChromeDriver encontrado: {chromedriver_path}")
            
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.maximize_window()
            
            # Busca no Google Maps
            search_query = f"{self.nicho} em {self.cidade}"
            self._search_google_maps(search_query)
            
            # Aguarda os resultados carregarem
            print("⏳ Aguardando resultados...")
            time.sleep(5)
            
            # Coleta os dados das empresas
            self._collect_businesses()
            
            print(f"\n✓ Total de empresas coletadas: {len(self.businesses)}")
            
        except Exception as e:
            print(f"\n❌ Erro: {str(e)}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.businesses
    
    def _search_google_maps(self, query: str):
        """Realiza a busca no Google Maps"""
        print(f"🔍 Buscando: {query}")
        
        # Acessa o Google Maps
        self.driver.get("https://www.google.com/maps")
        time.sleep(3)
        
        # Busca pelo nicho e cidade
        print("⌨️  Digitando busca...")
        try:
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "searchboxinput"))
            )
            search_box.click()
            time.sleep(0.5)
            search_box.send_keys(query)
            time.sleep(1)
            search_box.send_keys(Keys.ENTER)
            print("✓ Busca enviada!")
            time.sleep(5)
        except Exception as e:
            print(f"❌ Erro na busca: {str(e)}")
            raise
    
    def _scroll_results(self):
        """Faz scroll na lista de resultados"""
        print("📜 Carregando mais resultados...")
        
        try:
            # Encontra o painel de resultados
            results_panel = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            
            for i in range(3):
                print(f"  Scroll {i+1}/3...")
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;",
                    results_panel
                )
                time.sleep(CONFIG["DELAY_BETWEEN_SCROLLS"])
            
            print("✓ Scroll completo")
        except Exception as e:
            print(f"⚠️ Erro ao fazer scroll: {str(e)}")
    
    def _collect_businesses(self):
        """Coleta informações das empresas"""
        print("\n📊 Coletando informações das empresas...")
        
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
                    # Re-busca os links a cada iteração (para evitar stale elements)
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
                        # Verifica se tem WhatsApp e não tem website
                        if business_data.get('whatsapp') and not business_data.get('website'):
                            self.businesses.append(business_data)
                            print(f"✅ Adicionada: {business_data['nome']}")
                        else:
                            if business_data.get('website'):
                                print(f"⏭️  Ignorada (tem website): {business_data.get('nome', 'N/A')}")
                            else:
                                print(f"⏭️  Ignorada (sem WhatsApp): {business_data.get('nome', 'N/A')}")
                    
                    time.sleep(CONFIG["DELAY_BETWEEN_BUSINESSES"])
                    
                except Exception as e:
                    print(f"⚠️ Erro ao processar empresa {idx+1}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"❌ Erro ao coletar empresas: {str(e)}")
    
    def _extract_business_info(self) -> dict:
        """Extrai informações de um negócio específico"""
        try:
            business_data = {}
            time.sleep(2)
            
            # Nome do negócio
            try:
                name_element = self.driver.find_element(By.CSS_SELECTOR, 'h1')
                business_data['nome'] = name_element.text.strip()
            except:
                print("  ⚠️ Nome não encontrado")
                return None
            
            # Telefone
            try:
                phone_element = self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id*="phone"]')
                phone_text = phone_element.get_attribute('aria-label')
                if phone_text:
                    business_data['telefone'] = phone_text.replace('Telefone: ', '').replace('Copiar número de telefone', '').strip()
            except:
                pass
            
            # Endereço
            try:
                address_element = self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"]')
                address_text = address_element.get_attribute('aria-label')
                if address_text:
                    business_data['endereco'] = address_text.replace('Endereço: ', '').strip()
            except:
                pass
            
            # Website
            try:
                website_element = self.driver.find_element(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
                website_text = website_element.get_attribute('aria-label')
                if website_text:
                    business_data['website'] = website_text.replace('Website: ', '').strip()
            except:
                pass
            
            # WhatsApp
            business_data['whatsapp'] = self._extract_whatsapp(business_data.get('telefone', ''))
            
            # Rating
            try:
                rating_element = self.driver.find_element(By.CSS_SELECTOR, 'div.F7nice span[aria-hidden="true"]')
                business_data['avaliacao'] = rating_element.text.strip()
            except:
                pass
            
            # Número de reviews
            try:
                reviews_element = self.driver.find_element(By.CSS_SELECTOR, 'div.F7nice span[aria-label*="avaliações"]')
                business_data['num_avaliacoes'] = reviews_element.get_attribute('aria-label').strip()
            except:
                pass
            
            return business_data
            
        except Exception as e:
            print(f"  ⚠️ Erro ao extrair informações: {str(e)}")
            return None
    
    def _extract_whatsapp(self, phone: str) -> str:
        """Extrai e formata número de WhatsApp"""
        if not phone:
            return ""
        
        clean_phone = re.sub(r'\D', '', phone)
        
        if len(clean_phone) >= 10:
            if not clean_phone.startswith('55'):
                clean_phone = '55' + clean_phone
            return clean_phone
        
        return ""
    
    def save_to_excel(self, filename: str = None):
        """Salva os dados coletados em um arquivo Excel"""
        if not self.businesses:
            print("⚠️ Nenhuma empresa para salvar!")
            return
        
        os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cidade_limpa = self.cidade.replace(",", "").replace(" ", "_")
            filename = f"{CONFIG['OUTPUT_DIR']}/leads_{self.nicho}_{cidade_limpa}_{timestamp}.xlsx"
        
        df = pd.DataFrame(self.businesses)
        columns = ['nome', 'telefone', 'whatsapp', 'endereco', 'avaliacao', 'num_avaliacoes']
        df = df.reindex(columns=[col for col in columns if col in df.columns], axis=1)
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n📊 Arquivo salvo: {filename}")
        print(f"📈 Total de leads: {len(self.businesses)}")
        
        return filename


def main():
    print("=" * 60)
    print("🎯 GOOGLE MAPS LEAD SCRAPER (Selenium)")
    print("=" * 60)
    
    nicho = input("\n📌 Digite o nicho (ex: estética): ").strip()
    cidade = input("📍 Digite a cidade e estado (ex: Curitiba, PR): ").strip()
    
    if not nicho or not cidade:
        print("❌ Nicho e cidade são obrigatórios!")
        return
    
    print(f"\n🚀 Iniciando busca por '{nicho}' em '{cidade}'...")
    print("⏳ Isso pode levar alguns minutos...\n")
    
    scraper = GoogleMapsScraperSelenium(nicho, cidade)
    
    try:
        scraper.scrape()
        
        if scraper.businesses:
            scraper.save_to_excel()
            print("\n✅ Processo concluído com sucesso!")
        else:
            print("\n⚠️ Nenhuma empresa encontrada com os critérios:")
            print("   - Sem website")
            print("   - Com WhatsApp")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")


if __name__ == "__main__":
    main()
