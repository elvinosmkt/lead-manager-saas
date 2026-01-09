"""
Scraper FLEXÍVEL - Coleta TODAS as empresas e marca se têm site/WhatsApp
Melhor para análise e filtragem posterior
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os
from datetime import datetime
import pandas as pd
from config import CONFIG


class GoogleMapsScraperFlexivel:
    def __init__(self, nicho: str, cidade: str):
        self.nicho = nicho
        self.cidade = cidade
        self.businesses = []
        self.empresas_processadas = set()
        self.driver = None
    
    def scrape(self):
        """Executa o processo completo de scraping"""
        print("🌐 Iniciando navegador Chrome...")
        
        chrome_options = Options()
        if CONFIG["HEADLESS"]:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        try:
            driver_path = ChromeDriverManager().install()
            driver_dir = os.path.dirname(driver_path)
            
            chromedriver_path = None
            for file in os.listdir(driver_dir):
                if file == 'chromedriver' and not file.endswith('.chromedriver'):
                    chromedriver_path = os.path.join(driver_dir, file)
                    break
            
            if not chromedriver_path or not os.path.exists(chromedriver_path):
                raise Exception(f"ChromeDriver não encontrado em {driver_dir}")
            
            os.chmod(chromedriver_path, 0o755)
            print(f"✓ ChromeDriver encontrado: {chromedriver_path}")
            
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.maximize_window()
            
            search_query = f"{self.nicho} em {self.cidade}"
            self._search_google_maps(search_query)
            
            print("⏳ Aguardando resultados...")
            time.sleep(5)
            
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
        
        self.driver.get("https://www.google.com/maps")
        time.sleep(3)
        
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
        """Faz scroll máximo para carregar todos os resultados"""
        print("📜 Carregando MÁXIMO de resultados...")
        
        try:
            results_panel = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            
            last_height = 0
            scrolls_sem_mudanca = 0
            scroll_count = 0
            max_scrolls = 30
            
            while scroll_count < max_scrolls:
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;",
                    results_panel
                )
                
                scroll_count += 1
                if scroll_count % 5 == 0:
                    print(f"  Scroll {scroll_count}/{max_scrolls}...")
                
                time.sleep(1.5)
                
                new_height = self.driver.execute_script(
                    "return arguments[0].scrollHeight", 
                    results_panel
                )
                
                if new_height == last_height:
                    scrolls_sem_mudanca += 1
                    if scrolls_sem_mudanca >= 3:
                        print(f"  ✓ Todos os resultados carregados ({scroll_count} scrolls)")
                        break
                else:
                    scrolls_sem_mudanca = 0
                
                last_height = new_height
            
            if scroll_count >= max_scrolls:
                print(f"  ✓ Limite atingido ({max_scrolls} scrolls)")
            
        except Exception as e:
            print(f"⚠️ Erro ao fazer scroll: {str(e)}")
    
    def _collect_businesses(self):
        """Coleta TODAS as empresas e marca se têm site/WhatsApp"""
        print("\n📊 Coletando TODAS as empresas...")
        print("🔍 Mode: Análise completa\n")
        
        try:
            self._scroll_results()
            
            print("🔎 Buscando empresas...")
            time.sleep(2)
            results_feed = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            business_links = results_feed.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')
            
            if not business_links:
                print("⚠️ Nenhuma empresa encontrada")
                return
            
            unique_hrefs = set()
            unique_links = []
            for link in business_links:
                href = link.get_attribute('href')
                if href and '/maps/place/' in href and href not in unique_hrefs:
                    unique_hrefs.add(href)
                    unique_links.append(link)
            
            total = min(len(unique_links), CONFIG["MAX_BUSINESSES"])
            print(f"📍 Encontradas {len(unique_links)} empresas. Processando até {total}...\n")
            
            for idx in range(total):
                try:
                    results_feed = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
                    business_links = results_feed.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')
                    
                    unique_hrefs_new = set()
                    unique_links_new = []
                    for link in business_links:
                        href = link.get_attribute('href')
                        if href and '/maps/place/' in href and href not in unique_hrefs_new:
                            unique_hrefs_new.add(href)
                            unique_links_new.append(link)
                    
                    if idx >= len(unique_links_new):
                        break
                    
                    print(f"[{idx+1}/{total}] Processando...")
                    
                    try:
                        unique_links_new[idx].click()
                        time.sleep(2)
                    except:
                        continue
                    
                    business_data = self._extract_all_info()
                    
                    if business_data and business_data['nome']:
                        if business_data['nome'] not in self.empresas_processadas:
                            self.empresas_processadas.add(business_data['nome'])
                            self.businesses.append(business_data)
                            
                            status = []
                            if not business_data['tem_site_proprio']:
                                status.append("SEM SITE")
                            if business_data['whatsapp']:
                                status.append("COM WHATSAPP")
                            
                            print(f"  ✅ {business_data['nome']} - {' + '.join(status) if status else 'Coletado'}")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"  ⚠️ Erro: {str(e)}")
                    continue
            
            sem_site = sum(1 for b in self.businesses if not b['tem_site_proprio'])
            com_whatsapp = sum(1 for b in self.businesses if b['whatsapp'])
            leads_qualificados = sum(1 for b in self.businesses if not b['tem_site_proprio'] and b['whatsapp'])
            
            print(f"\n🎯 Estatísticas:")
            print(f"   Total: {len(self.businesses)} empresas")
            print(f"   Sem site próprio: {sem_site}")
            print(f"   Com WhatsApp: {com_whatsapp}")
            print(f"   Leads qualificados: {leads_qualificados}")
                    
        except Exception as e:
            print(f"❌ Erro ao coletar: {str(e)}")
    
    def _extract_all_info(self) -> dict:
        """Extrai TODAS as informações da empresa"""
        try:
            business_data = {}
            time.sleep(1)
            
            # Nome
            try:
                name_element = self.driver.find_element(By.CSS_SELECTOR, 'h1')
                business_data['nome'] = name_element.text.strip()
            except:
                return None
            
            # Verifica site PRÓPRIO
            tem_site_proprio, url_site, tipo_link = self._check_website()
            business_data['tem_site_proprio'] = tem_site_proprio
            business_data['website'] = url_site if tem_site_proprio else ""
            business_data['redes_sociais'] = url_site if not tem_site_proprio and url_site else ""
            
            # Telefone
            try:
                phone_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id*="phone"]')
                phone_text = phone_button.get_attribute('aria-label')
                if phone_text:
                    business_data['telefone'] = phone_text.replace('Telefone: ', '').replace('Copiar número de telefone', '').strip()
            except:
                business_data['telefone'] = ''
            
            # WhatsApp
            whatsapp_numero = self._extract_whatsapp(business_data.get('telefone', ''))
            business_data['whatsapp'] = whatsapp_numero
            business_data['whatsapp_link'] = f"https://wa.me/{whatsapp_numero}" if whatsapp_numero else ""
            
            # Endereço
            try:
                address_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"]')
                address_text = address_button.get_attribute('aria-label')
                if address_text:
                    business_data['endereco'] = address_text.replace('Endereço: ', '').strip()
            except:
                business_data['endereco'] = ''
            
            # Avaliação
            try:
                rating_element = self.driver.find_element(By.CSS_SELECTOR, 'div.F7nice span[aria-hidden="true"]')
                business_data['avaliacao'] = rating_element.text.strip()
            except:
                business_data['avaliacao'] = ''
            
            # Número de avaliações
            try:
                reviews_element = self.driver.find_element(By.CSS_SELECTOR, 'div.F7nice span[aria-label*="avaliações"]')
                business_data['num_avaliacoes'] = reviews_element.get_attribute('aria-label').strip()
            except:
                business_data['num_avaliacoes'] = ''
            
            # Metadados
            business_data['nicho'] = self.nicho
            business_data['cidade'] = self.cidade
            business_data['data_coleta'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            business_data['contatado'] = 'Não'
            business_data['respondeu'] = 'Não'
            business_data['observacoes'] = ''
            
            return business_data
            
        except Exception as e:
            print(f"  ⚠️ Erro ao extrair: {str(e)}")
            return None
    
    def _check_website(self) -> tuple[bool, str, str]:
        """
        Verifica se tem site PRÓPRIO
        Retorna: (tem_site_proprio, url, tipo)
        """
        try:
            redes_sociais = [
                'instagram.com', 'facebook.com', 'fb.com', 'fb.me',
                'tiktok.com', 'twitter.com', 'linkedin.com',
                'youtube.com', 'whatsapp.com', 'wa.me',
                'telegram.me', 't.me', 'pinterest.com',
                'google.com', 'goo.gl', 'maps.google.com'
            ]
            
            website_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
            
            if website_elements:
                for elem in website_elements:
                    href = elem.get_attribute('href')
                    if href and 'http' in href:
                        is_social = any(rede in href.lower() for rede in redes_sociais)
                        
                        if is_social:
                            return False, href, "rede_social"
                        else:
                            return True, href, "site_proprio"
            
            return False, "", "nenhum"
            
        except:
            return False, "", "erro"
    
    def _extract_whatsapp(self, phone: str) -> str:
        """Extrai e formata WhatsApp"""
        if not phone:
            return ""
        
        clean_phone = re.sub(r'\D', '', phone)
        
        if len(clean_phone) >= 10:
            if not clean_phone.startswith('55'):
                clean_phone = '55' + clean_phone
            return clean_phone
        
        return ""
    
    def save_to_excel(self, filename: str = None):
        """Salva em Excel"""
        if not self.businesses:
            print("⚠️ Nenhuma empresa para salvar!")
            return
        
        os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cidade_limpa = self.cidade.replace(",", "").replace(" ", "_")
            filename = f"{CONFIG['OUTPUT_DIR']}/empresas_{self.nicho}_{cidade_limpa}_{timestamp}.xlsx"
        
        df = pd.DataFrame(self.businesses)
        
        columns = [
            'nome', 'tem_site_proprio', 'whatsapp', 'whatsapp_link', 
            'telefone', 'website', 'redes_sociais', 'endereco',
            'avaliacao', 'num_avaliacoes', 'nicho', 'cidade',
            'contatado', 'respondeu', 'observacoes', 'data_coleta'
        ]
        df = df[[col for col in columns if col in df.columns]]
        
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n📊 Arquivo salvo: {filename}")
        print(f"✅ {len(self.businesses)} empresas exportadas!")
        
        return filename
