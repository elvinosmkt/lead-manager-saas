"""
Scraper CORRIGIDO - Atualizado para Google Maps 2024
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os
from datetime import datetime
import pandas as pd
from config import CONFIG


class GoogleMapsScraperAtualizado:
    def __init__(self, nicho: str, cidade: str):
        self.nicho = nicho
        self.cidade = cidade
        self.businesses = []
        self.empresas_processadas = set()
        self.driver = None
    
    def scrape(self):
        print("🌐 Iniciando navegador...")
        
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            driver_path = ChromeDriverManager().install()
            driver_dir = os.path.dirname(driver_path)
            
            chromedriver_path = None
            for file in os.listdir(driver_dir):
                if file == 'chromedriver':
                    chromedriver_path = os.path.join(driver_dir, file)
                    break
            
            os.chmod(chromedriver_path, 0o755)
            
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.maximize_window()
            
            # Busca
            search_query = f"{self.nicho} em {self.cidade}"
            print(f"🔍 Buscando: {search_query}")
            
            self.driver.get("https://www.google.com/maps")
            time.sleep(3)
            
            # Busca
            wait = WebDriverWait(self.driver, 10)
            search_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
            search_box.clear()
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.ENTER)
            time.sleep(5)
            
            # Scroll para carregar resultados
            print("📜 Carregando resultados...")
            try:
                results_panel = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[role="feed"]')
                ))
                
                for i in range(10):  # Scroll menor mas mais eficiente
                    self.driver.execute_script(
                        "arguments[0].scrollTop = arguments[0].scrollHeight;",
                        results_panel
                    )
                    time.sleep(1)
            except:
                print("⚠️  Painel de resultados não encontrado, tentando alternativa...")
            
            print(f"✓ Resultados carregados!")
            
            # Coleta leads
            print(f"\n📊 Col etando leads...")
            time.sleep(2)
            
            # SELETORES ATUALIZADOS 2024
            result_selectors = [
                'a[href*="/maps/place/"]',  # Links para lugares
                'div.Nv2PK',  # Container de resultado
                'div[jsaction]',  # Div com ação
            ]
            
            all_results = []
            for selector in result_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        all_results = elements
                        print(f"✅ Encontrados {len(elements)} resultados com seletor: {selector}")
                        break
                except:
                    continue
            
            if not all_results:
                print("❌ Nenhum resultado encontrado!")
                return
            
            total_processadas = 0
            max_leads = min(len(all_results), CONFIG["MAX_BUSINESSES"])
            
            print(f"📍 Processando até {max_leads} empresas...\n")
            
            for idx in range(max_leads):
                try:
                    # Re-busca elementos (atualiza DOM)
                    current_results = self.driver.find_elements(By.CSS_SELECTOR, result_selectors[1] if len(result_selectors) > 1 else result_selectors[0])
                    
                    if idx >= len(current_results):
                        break
                    
                    result = current_results[idx]
                    
                    # Scroll até o elemento
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", result)
                    time.sleep(0.5)
                    
                    # Clica
                    try:
                        result.click()
                        time.sleep(3)  # Tempo para carregar detalhes
                    except:
                        try:
                            self.driver.execute_script("arguments[0].click();", result)
                            time.sleep(3)
                        except:
                            continue
                    
                    # Extrai dados
                    data = self._extract_data_atualizado()
                    
                    if data and data.get('nome'):
                        if data['nome'] not in self.empresas_processadas:
                            self.empresas_processadas.add(data['nome'])
                            self.businesses.append(data)
                            total_processadas += 1
                            
                            status_parts = []
                            if not data.get('tem_site', True):
                                status_parts.append("🚫 SEM SITE")
                            if data.get('telefone'):
                                status_parts.append("📞 Tel")
                            if data.get('whatsapp'):
                                status_parts.append("✅ WhatsApp")
                            
                            print(f"  [{total_processadas}] ✅ {data['nome'][:40]} | {' | '.join(status_parts)}")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"  ⚠️  Erro no item {idx}: {str(e)[:50]}")
                    continue
            
            print(f"\n🎉 Coleta concluída: {len(self.businesses)} leads\n")
            self._print_stats()
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.businesses
    
    def _extract_data_atualizado(self):
        """Extração atualizada para Google Maps 2024"""
        try:
            data = {}
            time.sleep(1)
            
            # Nome - MÚLTIPLOS SELETORES
            nome_selectors = ['h1.DUwDvf', 'h1', 'div.qBF1Pd', 'span.fontHeadlineLarge']
            nome = None
            for selector in nome_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    nome = elem.text.strip()
                    if nome and len(nome) > 2:
                        break
                except:
                    continue
            
            if not nome or len(nome) < 3:
                return None
            
            data['nome'] = nome
            data['google_maps_link'] = self.driver.current_url
            
            # Telefone - MÚLTIPLOS SELETORES
            telefone = ""
            phone_selectors = [
                'button[data-item-id*="phone"]',
                'button[aria-label*="Telefone"]',
                'button[aria-label*="Phone"]',
                'div[data-tooltip*="Telefone"]'
            ]
            
            for selector in phone_selectors:
                try:
                    phone_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    phone_text = phone_elem.get_attribute('aria-label') or phone_elem.text
                    if phone_text:
                        telefone = phone_text.replace('Telefone:', '').replace('Phone:', '').replace('Copiar', '').strip()
                        if telefone:
                            break
                except:
                    continue
            
            data['telefone'] = telefone
            
            # WhatsApp
            whatsapp = ""
            if telefone:
                clean = re.sub(r'\D', '', telefone)
                if len(clean) >= 10:
                    if not clean.startswith('55'):
                        clean = '55' + clean
                    whatsapp = clean
            
            data['whatsapp'] = whatsapp
            data['whatsapp_link'] = f"https://wa.me/{whatsapp}" if whatsapp else ""
            
            # Website
            tem_site = False
            website = ""
            try:
                website_elem = self.driver.find_element(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
                href = website_elem.get_attribute('href')
                if href:
                    plataformas_nao_site = [
                        'instagram.com', 'facebook.com', 'fb.com', 'whatsapp.com',
                        'wa.me', 'tiktok.com', 'twitter.com', 'linkedin.com',
                        'google.com', 'maps.google.com'
                    ]
                    
                    if not any(plat in href.lower() for plat in plataformas_nao_site):
                        tem_site = True
                        website = href
            except:
                pass
            
            data['tem_site'] = tem_site
            data['website'] = website
            
            # Endereço
            try:
                address_elem = self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"]')
                address = address_elem.get_attribute('aria-label')
                data['endereco'] = address.replace('Endereço:', '').strip() if address else ""
            except:
                data['endereco'] = ""
            
            # Avaliação
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, 'div.F7nice span[aria-hidden="true"]')
                data['avaliacao'] = rating_elem.text.strip()
            except:
                data['avaliacao'] = ""
            
            # Número de avaliações
            try:
                reviews_elem = self.driver.find_element(By.CSS_SELECTOR, 'div.F7nice span[aria-label*="avaliações"]')
                data['num_avaliacoes'] = reviews_elem.get_attribute('aria-label').strip()
            except:
                data['num_avaliacoes'] = ""
            
            # Segmento
            try:
                category_elem = self.driver.find_element(By.CSS_SELECTOR, 'button[jsaction*="category"]')
                data['segmento'] = category_elem.get_attribute('aria-label').strip()
            except:
                data['segmento'] = self.nicho
            
            # Metadados
            data['nicho'] = self.nicho
            data['cidade'] = self.cidade
            data['data_coleta'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['contatado'] = 'Não'
            data['respondeu'] = 'Não'
            data['observacoes'] = ''
            
            return data
            
        except Exception as e:
            print(f"  ⚠️  Erro ao extrair: {str(e)[:50]}")
            return None
    
    def _print_stats(self):
        total = len(self.businesses)
        sem_site = sum(1 for b in self.businesses if not b.get('tem_site', True))
        com_tel = sum(1 for b in self.businesses if b.get('telefone'))
        com_whats = sum(1 for b in self.businesses if b.get('whatsapp'))
        qualificados = sum(1 for b in self.businesses if not b.get('tem_site', True) and b.get('whatsapp'))
        
        print(f"🎯 Estatísticas:")
        print(f"   📊 Total: {total}")
        print(f"   🚫 Sem site: {sem_site}")
        print(f"   📞 Com telefone: {com_tel}")
        print(f"   💬 Com WhatsApp: {com_whats}")
        print(f"   ⭐ Qualificados: {qualificados}")
    
    def save_to_excel(self, filename=None):
        if not self.businesses:
            print("⚠️  Nenhum lead para salvar!")
            return
        
        os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cidade_limpa = self.cidade.replace(",", "").replace(" ", "_")
            filename = f"{CONFIG['OUTPUT_DIR']}/leads_{self.nicho}_{cidade_limpa}_{timestamp}.xlsx"
        
        df = pd.DataFrame(self.businesses)
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n💾 Salvo: {filename}")
        return filename
