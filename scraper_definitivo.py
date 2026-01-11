# -*- coding: utf-8 -*-
"""
Scraper Turbo v2 - Extração via Painel Lateral (5x mais rápido)
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
from selenium.webdriver.common.action_chains import ActionChains
from config import CONFIG

class GoogleMapsScraperDefinitivo:
    def __init__(self, nicho, cidade):
        self.nicho = nicho
        self.cidade = cidade
        self.driver = None
        self.businesses = []
        self.empresas_processadas = set()
        
        # Callbacks (injetados pelo backend)
        self.on_lead_found_callback = None
        self.check_stop = None
        self.on_progress_update = None  # NOVO: Para atualizar progresso
        
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
        
        # Performance
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.page_load_strategy = 'eager'
        
        # Desabilitar imagens para velocidade
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)

        print("🔧 Iniciando Chrome Driver (Turbo Mode)...")
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"❌ Erro ao iniciar Chrome: {e}")
            # Fallback
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
            
            # Espera lista carregar
            try:
                WebDriverWait(self.driver, 12).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']"))
                )
                print("✅ Lista de resultados carregada")
            except:
                print("⚠️ Timeout no carregamento inicial")

            # Scroll para carregar mais resultados
            self._scroll_results()
            
            # Coleta via CLIQUE (Método Turbo)
            print("📊 Extraindo dados via painel lateral...")
            self._collect_via_panel_click()
            
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
        """Scroll no painel de resultados para carregar mais itens"""
        try:
            panel = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            
            max_scrolls = 5  # Menos scrolls, mas suficiente
            for i in range(max_scrolls):
                if self.check_stop and self.check_stop(): break
                
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;", 
                    panel
                )
                time.sleep(1)
                
        except Exception as e:
            print(f"⚠️ Scroll: {e}")

    def _collect_via_panel_click(self):
        """
        MÉTODO TURBO: Clica em cada resultado para abrir o painel lateral
        e extrai os dados SEM navegar para outra página.
        """
        try:
            # Pega todos os cards de resultado
            # O Google Maps mostra cada resultado como um <a> ou <div> clicável
            results = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
            
            if not results:
                # Fallback: tenta outro seletor
                results = self.driver.find_elements(By.CSS_SELECTOR, 'div[jsaction*="click"] div[role="article"]')
            
            max_leads = min(len(results), CONFIG.get("MAX_BUSINESSES", 100))
            filters = CONFIG.get('FILTERS', {})
            
            print(f"📍 {len(results)} resultados encontrados. Processando {max_leads}...")

            for idx, result in enumerate(results[:max_leads]):
                if self.check_stop and self.check_stop():
                    print("🛑 Parada solicitada")
                    break

                try:
                    # Scroll para o elemento (garante visibilidade)
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", result)
                    time.sleep(0.3)
                    
                    # Clica para abrir o painel lateral
                    result.click()
                    time.sleep(1.5)  # Espera painel carregar
                    
                    # Extrai dados do painel
                    data = self._extract_from_panel()
                    
                    if not data or not data.get('nome'):
                        continue
                    
                    # Aplica Filtros
                    if filters.get('site') == 'sem-site' and data.get('tem_site'):
                        continue
                    if filters.get('site') == 'com-site' and not data.get('tem_site'):
                        continue
                    if filters.get('whats') == 'com-whats' and not data.get('whatsapp'):
                        continue

                    # Evita duplicatas
                    if data['nome'] in self.empresas_processadas:
                        continue
                    
                    self.empresas_processadas.add(data['nome'])
                    self.businesses.append(data)
                    
                    # CALLBACK: Envia lead em tempo real
                    if self.on_lead_found_callback:
                        try:
                            self.on_lead_found_callback(data)
                        except: pass
                    
                    # Log visual
                    site_icon = "🌐" if data.get('tem_site') else "❌"
                    whats_icon = "💬" if data.get('whatsapp') else ""
                    print(f"✅ [{idx+1}/{max_leads}] {data['nome'][:30]}... {site_icon} {whats_icon}")

                except Exception as e:
                    # Erro em um item específico, continua
                    pass

        except Exception as e:
            print(f"Erro coleta: {e}")
            traceback.print_exc()

    def _extract_from_panel(self):
        """Extrai dados do painel lateral aberto"""
        data = {}
        
        try:
            # NOME (H1 ou aria-label principal)
            nome = ""
            try:
                h1 = self.driver.find_element(By.CSS_SELECTOR, "h1")
                nome = h1.text.strip()
            except:
                try:
                    # Fallback: Título no painel
                    el = self.driver.find_element(By.CSS_SELECTOR, "[role='main'] h1, div[aria-label]")
                    nome = el.get_attribute("aria-label") or el.text
                except: pass
            
            if not nome or len(nome) < 2:
                return None
            
            data['nome'] = nome
            data['google_maps_link'] = self.driver.current_url
            
            # TELEFONE
            telefone = ""
            try:
                # Botão com data-item-id="phone"
                phone_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-item-id*='phone']")
                telefone = phone_btn.get_attribute("aria-label") or phone_btn.text
                telefone = telefone.replace("Telefone:", "").replace("Ligar:", "").strip()
            except:
                # Fallback: Regex no texto da página
                try:
                    body_text = self.driver.find_element(By.CSS_SELECTOR, "[role='main']").text
                    phones = re.findall(r'\(?\d{2}\)?\s?\d{4,5}[\s-]?\d{4}', body_text)
                    if phones:
                        telefone = phones[0]
                except: pass
            
            data['telefone'] = telefone
            
            # WHATSAPP (deriva do telefone)
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
                web_link = self.driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']")
                website = web_link.get_attribute("href")
            except: pass
            
            data['website'] = website
            data['tem_site'] = bool(website and len(website) > 5)
            
            # AVALIAÇÃO
            avaliacao = "0.0"
            try:
                star_el = self.driver.find_element(By.CSS_SELECTOR, "span[aria-label*='estrela'], span[role='img'][aria-label*='star']")
                val = star_el.get_attribute("aria-label")
                match = re.search(r'(\d+[.,]\d+)', val)
                if match:
                    avaliacao = match.group(1).replace(',', '.')
            except: pass
            data['avaliacao'] = avaliacao
            
            # ENDEREÇO
            endereco = ""
            try:
                addr_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-item-id='address']")
                endereco = addr_btn.get_attribute("aria-label") or addr_btn.text
                endereco = endereco.replace("Endereço:", "").strip()
            except: pass
            data['endereco'] = endereco
            
            # Metadata
            data['nicho'] = self.nicho
            data['cidade'] = self.cidade
            
            return data

        except Exception as e:
            return None
