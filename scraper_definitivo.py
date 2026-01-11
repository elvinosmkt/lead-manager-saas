# -*- coding: utf-8 -*-
"""
Scraper Estável v3 - Método clássico com seletores robustos
"""
import time
import re
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import CONFIG

class GoogleMapsScraperDefinitivo:
    def __init__(self, nicho, cidade):
        self.nicho = nicho
        self.cidade = cidade
        self.driver = None
        self.businesses = []
        self.empresas_processadas = set()
        
        # Callbacks
        self.on_lead_found_callback = None
        self.check_stop = None
        
        self._setup_driver()

    def _setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--lang=pt-BR")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.page_load_strategy = 'eager'

        print("🔧 Iniciando Chrome Driver...")
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
        except Exception as e:
            print(f"❌ Erro Chrome: {e}")
            try:
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e2:
                raise e2

    def scrape(self):
        try:
            query = f"{self.nicho} em {self.cidade}"
            print(f"🔍 Buscando: {query}")
            
            url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}/?hl=pt-BR"
            self.driver.get(url)
            
            # Espera resultados carregarem
            time.sleep(4)
            
            # Scroll para carregar mais
            self._scroll_results()
            
            # Coleta links dos resultados
            links = self._get_business_links()
            print(f"📍 {len(links)} links encontrados")
            
            if not links:
                print("⚠️ Nenhum resultado encontrado")
                return []
            
            max_leads = CONFIG.get("MAX_BUSINESSES", 10)
            filters = CONFIG.get('FILTERS', {})
            
            # Processa cada link
            for idx, link in enumerate(links[:max_leads * 2]):  # Pega mais para compensar filtros
                if self.check_stop and self.check_stop():
                    print("🛑 Parada solicitada")
                    break
                    
                if len(self.businesses) >= max_leads:
                    break
                
                try:
                    data = self._extract_business_data(link)
                    
                    if not data or not data.get('nome'):
                        continue
                    
                    # Filtros
                    if filters.get('site') == 'sem-site' and data.get('tem_site'):
                        continue
                    if filters.get('site') == 'com-site' and not data.get('tem_site'):
                        continue
                    
                    # Evita duplicatas
                    if data['nome'] in self.empresas_processadas:
                        continue
                    
                    self.empresas_processadas.add(data['nome'])
                    self.businesses.append(data)
                    
                    # Callback tempo real
                    if self.on_lead_found_callback:
                        try:
                            self.on_lead_found_callback(data)
                        except: pass
                    
                    site_icon = "🌐" if data.get('tem_site') else "❌"
                    whats_icon = "💬" if data.get('whatsapp') else ""
                    print(f"✅ [{len(self.businesses)}/{max_leads}] {data['nome'][:35]}... {site_icon} {whats_icon}")
                    
                except Exception as e:
                    print(f"⚠️ Erro item: {e}")
                    continue
            
            print(f"\n🎉 Coleta concluída: {len(self.businesses)} leads\n")
            
        except Exception as e:
            print(f"❌ Erro Geral: {e}")
            traceback.print_exc()
        finally:
            if self.driver:
                try: self.driver.quit()
                except: pass
        
        return self.businesses

    def _scroll_results(self):
        """Scroll no painel de resultados"""
        try:
            # Tenta encontrar o painel de resultados
            selectors = [
                'div[role="feed"]',
                'div.m6QErb[aria-label]',
                'div.m6QErb.DxyBCb'
            ]
            
            panel = None
            for sel in selectors:
                try:
                    panel = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if panel:
                        break
                except:
                    continue
            
            if not panel:
                print("⚠️ Painel de scroll não encontrado")
                return
            
            for i in range(5):
                if self.check_stop and self.check_stop(): break
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;", 
                    panel
                )
                time.sleep(1.5)
                
        except Exception as e:
            print(f"⚠️ Scroll: {e}")

    def _get_business_links(self):
        """Pega todos os links de negócios"""
        links = []
        
        try:
            # Seletores para links de negócios no Maps
            selectors = [
                'a.hfpxzc',  # Seletor principal atual
                'a[href*="/maps/place/"]',
                'div[role="article"] a[href*="maps"]',
            ]
            
            for sel in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if elements:
                        links = [e.get_attribute('href') for e in elements if e.get_attribute('href')]
                        if links:
                            break
                except:
                    continue
            
            # Remove duplicatas mantendo ordem
            seen = set()
            unique_links = []
            for link in links:
                if link and link not in seen:
                    seen.add(link)
                    unique_links.append(link)
            
            return unique_links
            
        except Exception as e:
            print(f"⚠️ Erro links: {e}")
            return []

    def _extract_business_data(self, url):
        """Extrai dados de uma página de negócio"""
        data = {}
        
        try:
            self.driver.get(url)
            time.sleep(2)
            
            data['google_maps_link'] = url
            
            # NOME
            try:
                h1 = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
                )
                data['nome'] = h1.text.strip()
            except:
                data['nome'] = ""
            
            if not data['nome']:
                return None
            
            # Pega todo o texto da página para extrair dados
            page_text = ""
            try:
                main = self.driver.find_element(By.CSS_SELECTOR, "div[role='main']")
                page_text = main.text
            except:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # TELEFONE (regex)
            telefone = ""
            phone_patterns = [
                r'\(?\d{2}\)?\s?\d{4,5}[-\s]?\d{4}',
                r'\+55\s?\d{2}\s?\d{4,5}[-\s]?\d{4}'
            ]
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    telefone = matches[0]
                    break
            data['telefone'] = telefone
            
            # WHATSAPP
            data['whatsapp'] = ""
            if telefone:
                nums = re.sub(r'\D', '', telefone)
                if len(nums) >= 10:
                    if not nums.startswith('55'):
                        nums = '55' + nums
                    data['whatsapp'] = nums
            
            # WEBSITE
            website = ""
            try:
                web_btn = self.driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']")
                website = web_btn.get_attribute('href') or ""
            except:
                # Fallback: procura no texto
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='http']")
                    for link in links:
                        href = link.get_attribute('href') or ""
                        if href and 'google' not in href and 'facebook' not in href.lower():
                            website = href
                            break
                except:
                    pass
            
            data['website'] = website
            data['tem_site'] = bool(website and len(website) > 5)
            
            # AVALIAÇÃO
            avaliacao = "0.0"
            try:
                rating_match = re.search(r'(\d[,\.]\d)\s*estrela', page_text, re.IGNORECASE)
                if rating_match:
                    avaliacao = rating_match.group(1).replace(',', '.')
                else:
                    spans = self.driver.find_elements(By.CSS_SELECTOR, "span[aria-label*='estrela'], span[role='img']")
                    for span in spans:
                        label = span.get_attribute('aria-label') or ""
                        match = re.search(r'(\d[,\.]\d)', label)
                        if match:
                            avaliacao = match.group(1).replace(',', '.')
                            break
            except:
                pass
            data['avaliacao'] = avaliacao
            
            # ENDEREÇO
            endereco = ""
            try:
                addr_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-item-id='address']")
                endereco = addr_btn.get_attribute('aria-label') or addr_btn.text
                endereco = endereco.replace('Endereço:', '').strip()
            except:
                # Fallback: procura padrão de endereço no texto
                addr_match = re.search(r'([A-Z][^,]+,\s*\d+[^,]*,\s*[^,]+)', page_text)
                if addr_match:
                    endereco = addr_match.group(1)
            data['endereco'] = endereco
            
            # Metadata
            data['nicho'] = self.nicho
            data['cidade'] = self.cidade
            
            return data
            
        except Exception as e:
            print(f"⚠️ Extração: {e}")
            return None
