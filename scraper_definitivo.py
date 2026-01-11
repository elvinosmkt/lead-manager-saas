
# -*- coding: utf-8 -*-
import time
import re
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import CONFIG
from db_config import save_lead_to_cloud

class GoogleMapsScraperDefinitivo:
    def __init__(self, nicho, cidade):
        self.nicho = nicho
        self.cidade = cidade
        self.driver = None
        self.businesses = []
        self.empresas_processadas = set()
        
        # Callback opcional para streaming (injetado por fora)
        self.on_lead_found_callback = None
        self.check_stop = None # Função para verificar cancelamento
        
        self._setup_driver()

    def _setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless") # Headless para servidor
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1366,768")
        chrome_options.add_argument("--lang=pt-BR")
        
        # User Agent Rotativo (Básico)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Otimizações de Performance
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-images") # Economiza banda
        chrome_options.page_load_strategy = 'eager' # Não espera carregar tudo

        print("🔧 Iniciando Chrome Driver...")
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"❌ Erro ao iniciar Chrome: {e}. Tentando fallback...")
            # Fallback para execução local se driver do path falhar
            try:
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e2:
                print(f"❌ Falha crítica no driver: {e2}")
                raise e2

    def scrape(self):
        try:
            query = f"{self.nicho} em {self.cidade}"
            print(f"🔍 Buscando por: {query}")
            
            url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}/?hl=pt-BR"
            self.driver.get(url)
            
            # Espera carregar
            try:
                WebDriverWait(self.driver, 10).until(
                   EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed'], div.m6QErb, div[aria-label*='Resultados']"))
                )
            except:
                print("⚠️ Demora no carregamento inicial ou layout diferente.")

            # Scroll e Coleta de Links
            self._scroll_results()
            
            # Coleta Dados
            print("📊 Coletando dados detalhados...")
            self._collect_businesses()
            
            print(f"\n🎉 Coleta concluída: {len(self.businesses)} leads\n")
            
        except Exception as e:
            print(f"❌ Erro Geral: {e}")
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.businesses
    
    def _scroll_results(self):
        """Scroll agressivo para carregar lista"""
        try:
            # Tenta achar o container de scroll (Painel lateral)
            # O Google Maps usa role="feed" frequentemente
            panel = None
            try:
                panel = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            except:
                try:
                    # Fallback para divs genéricas que contem muitos links de places
                    panel = self.driver.find_element(By.XPATH, "//div[contains(@aria-label, 'Resultados')]")
                except:
                    pass

            max_scrolls = 6 # ~40 resultados
            
            if panel:
                print("✅ Painel de scroll encontrado.")
                for i in range(max_scrolls):
                    if self.check_stop and self.check_stop(): break
                    
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", panel)
                    time.sleep(1.2) # Sleep menor
            else:
                print("⚠️ Usando scroll na janela (Painel não detectado)")
                for i in range(max_scrolls):
                    if self.check_stop and self.check_stop(): break
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(1)

        except Exception as e:
            print(f"Erro no scroll: {e}")

    def _collect_businesses(self):
        """Coleta links e visita um por um"""
        links = self._get_business_links()
        
        if not links:
            print("❌ Nenhum link encontrado!")
            return

        max_leads = min(len(links), CONFIG.get("MAX_BUSINESSES", 100))
        # Filtra quantidade solicitada
        
        print(f"📍 Encontrados {len(links)} locais. Processando {max_leads}...")
        
        for idx, link in enumerate(links[:max_leads]):
            # CHECK STOP
            if self.check_stop and self.check_stop():
                print("🛑 Parada solicitada.")
                break

            try:
                print(f"[{idx+1}/{max_leads}] Extraindo...", end="\r")
                self.driver.get(link)
                
                # Wait dinâmico (até aparecer o título H1)
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.TagName, "h1"))
                    )
                except: pass # Continua mesmo se timeout, tenta extrair o que der.

                data = self._extract_business_data()
                
                if data and data.get('nome'):
                    # Validação de Filtros (Se injetados no config)
                    filters = CONFIG.get('FILTERS', {})
                    
                    # Filtro Site
                    if filters.get('site') == 'sem-site' and data.get('tem_site'):
                        continue # Pula quem tem site
                    if filters.get('site') == 'com-site' and not data.get('tem_site'):
                        continue

                    # Filtro Whats (Básico: só verifica se achou tel celular)
                    if filters.get('whats') == 'com-whats' and not data.get('whatsapp'):
                        continue

                    if data['nome'] not in self.empresas_processadas:
                        self.empresas_processadas.add(data['nome'])
                        self.businesses.append(data)
                        
                        # Streaming Callback
                        if self.on_lead_found_callback:
                            try:
                                self.on_lead_found_callback(data)
                            except Exception as cb_err:
                                print(f"Erro callback: {cb_err}")

                        # Console Info
                        site_icon = "🌐" if data.get('tem_site') else "❌"
                        whats_icon = "💬" if data.get('whatsapp') else ""
                        print(f"✅ [{idx+1}] {data['nome'][:25]}... {site_icon} {whats_icon}")
            
            except Exception as e:
                print(f"Erro item {idx}: {e}")

    def _get_business_links(self):
        try:
            # Pega todos hrefs que pareçam leads
            elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
            links = []
            for e in elements:
                href = e.get_attribute('href')
                if href:
                    clean = href.split('?')[0] # Remove tracking params
                    if clean not in links:
                        links.append(clean)
            return links
        except: return []

    def _extract_business_data(self):
        data = {}
        try:
            # 1. NOME (H1 ou Aria-Label)
            # Tenta vários seletores pois o Google muda classes dinâmicas (ex: .DUwDvf, .fontHeadlineLarge)
            # Mas a tag H1 costuma ser consistente.
            nome = ""
            try:
                h1 = self.driver.find_element(By.TAG_NAME, "h1")
                nome = h1.text
            except:
                # Fallback: Procura elemento com classe que parece título
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, "[role='main'] [aria-label]")
                    nome = el.get_attribute("aria-label")
                except: pass
            
            if not nome: return None # Sem nome, lead inválido
            
            data['nome'] = nome
            data['google_maps_link'] = self.driver.current_url
            
            # 2. TELEFONE (Botão ou Texto)
            # Procura botão com aria-label contendo "Telefone: ..." ou ícone de phone
            # O seletor mais genérico é procurar botões que começam com "data-item-id='phone'"
            telefone = ""
            try:
                # Tenta achar elemento de texto que parece telefone (regex simples no texto da página visible)
                # Mais lento, mas robusto. Ou busca seletor de botão específico.
                # Botões de ação geralmente têm data-item-id="phone:tel:..."
                
                # Estratégia Botão com ícone de img
                btns = self.driver.find_elements(By.CSS_SELECTOR, "button[data-item-id*='phone']")
                if btns:
                    telefone = btns[0].get_attribute("aria-label") or btns[0].text
                    telefone = telefone.replace("Telefone: ", "").strip()
                
                if not telefone:
                    # Estratégia Texto Puro na lateral
                    # Procura divs que contenham (XX) XXXX-XXXX
                     body_text = self.driver.find_element(By.TAG_NAME, "body").text
                     phones = re.findall(r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}', body_text)
                     if phones:
                         telefone = phones[0] # Pega o primeiro que encontrar (arriscado mas funciona)
            except: pass
            
            data['telefone'] = telefone
            
            # Whats
            data['whatsapp'] = ""
            if telefone:
                nums = re.sub(r'\D', '', telefone)
                if len(nums) >= 10:
                    if not nums.startswith('55'): nums = '55' + nums
                    data['whatsapp'] = nums
                    
            # 3. WEBSITE
            # Botão com data-item-id="authority" geralmente é o site
            website = ""
            try:
                web_btns = self.driver.find_elements(By.CSS_SELECTOR, "a[data-item-id='authority']")
                if web_btns:
                    website = web_btns[0].get_attribute("href")
            except: pass
            
            data['website'] = website
            data['tem_site'] = bool(website)
            
            # 4. Avaliação
            avaliacao = "0.0"
            try:
                # Procura span com aria-label="X.X estrelas"
                star_el = self.driver.find_element(By.CSS_SELECTOR, "span[aria-label*='estrelas'], span[aria-label*='stars']")
                val = star_el.get_attribute("aria-label")
                # Extrai numero float
                match = re.search(r'(\d+[.,]\d+)', val)
                if match: avaliacao = match.group(1).replace(',', '.')
            except: pass
            data['avaliacao'] = avaliacao

            # 5. Endereço
            endereco = ""
            try:
                # Botão data-item-id="address"
                addr_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-item-id='address']")
                endereco = addr_btn.get_attribute("aria-label").replace("Endereço: ", "")
            except: pass
            data['endereco'] = endereco
            data['nicho'] = self.nicho
            data['cidade'] = self.cidade
            
            return data

        except Exception as e:
            # print(f"DEBUG: Erro extraçao {e}")
            return None
