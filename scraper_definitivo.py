# -*- coding: utf-8 -*-
"""
Scraper Robusto v4 - Com logs detalhados e seletores múltiplos
"""
import time
import re
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GoogleMapsScraperDefinitivo:
    def __init__(self, nicho, cidade, max_leads=10, filters=None):
        self.nicho = nicho
        self.cidade = cidade
        self.max_leads = max_leads  # Recebe direto
        self.filters = filters or {}  # Filtros: site, whats
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
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.page_load_strategy = 'eager'

        print("🔧 Iniciando Chrome Driver...")
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(45)
            print("✅ Chrome iniciado com sucesso")
        except Exception as e:
            print(f"❌ Erro Chrome direto: {e}")
            try:
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print("✅ Chrome iniciado via WebDriver Manager")
            except Exception as e2:
                print(f"❌ Falha total Chrome: {e2}")
                raise e2

    def scrape(self):
        try:
            query = f"{self.nicho} em {self.cidade}"
            print(f"🔍 Buscando: {query} (max: {self.max_leads} leads)")
            
            url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}/?hl=pt-BR"
            print(f"🌐 URL: {url}")
            
            self.driver.get(url)
            print("📄 Página carregada, aguardando resultados...")
            
            # Espera resultados carregarem
            time.sleep(5)
            
            # Verifica se a página carregou certo
            title = self.driver.title
            print(f"📰 Título: {title}")
            
            # Scroll para carregar mais
            self._scroll_results()
            
            # Coleta links dos resultados
            links = self._get_business_links()
            print(f"📍 {len(links)} links únicos encontrados")
            
            if not links:
                print("⚠️ NENHUM link encontrado - verificando página...")
                # Debug: salva screenshot
                try:
                    page_source_preview = self.driver.page_source[:500]
                    print(f"📄 Preview HTML: {page_source_preview}")
                except:
                    pass
                return []
            
            # Processa cada link
            for idx, link in enumerate(links):
                if self.check_stop and self.check_stop():
                    print("🛑 Parada solicitada pelo usuário")
                    break
                    
                if len(self.businesses) >= self.max_leads:
                    print(f"✅ Atingiu limite de {self.max_leads} leads")
                    break
                
                print(f"⏳ [{idx+1}/{len(links)}] Processando: {link[:60]}...")
                
                try:
                    data = self._extract_business_data(link)
                    
                    if not data or not data.get('nome'):
                        print(f"  ⚠️ Dados vazios, pulando...")
                        continue
                    
                    # Evita duplicatas
                    if data['nome'] in self.empresas_processadas:
                        print(f"  ⚠️ Duplicado: {data['nome'][:30]}")
                        continue
                    
                    # Aplica Filtros
                    site_filter = self.filters.get('site', 'todos')
                    whats_filter = self.filters.get('whats', 'todos')
                    
                    # Filtro Site
                    if site_filter == 'sem-site' and data.get('tem_site'):
                        print(f"  ⏭️ Pulando (tem site): {data['nome'][:30]}")
                        continue
                    if site_filter == 'com-site' and not data.get('tem_site'):
                        print(f"  ⏭️ Pulando (sem site): {data['nome'][:30]}")
                        continue
                    
                    # Filtro WhatsApp
                    if whats_filter == 'com-whats' and not data.get('whatsapp'):
                        print(f"  ⏭️ Pulando (sem WhatsApp): {data['nome'][:30]}")
                        continue
                    if whats_filter == 'sem-whats' and data.get('whatsapp'):
                        print(f"  ⏭️ Pulando (tem WhatsApp): {data['nome'][:30]}")
                        continue
                    
                    self.empresas_processadas.add(data['nome'])
                    self.businesses.append(data)
                    
                    # Callback tempo real
                    if self.on_lead_found_callback:
                        try:
                            self.on_lead_found_callback(data)
                        except Exception as cb_err:
                            print(f"  ⚠️ Callback error: {cb_err}")
                    
                    site_icon = "🌐" if data.get('tem_site') else "❌"
                    whats_icon = "💬" if data.get('whatsapp') else ""
                    print(f"  ✅ SUCESSO: {data['nome'][:35]} {site_icon} {whats_icon}")
                    
                except Exception as e:
                    print(f"  ❌ Erro: {str(e)[:50]}")
                    continue
            
            print(f"\n🎉 COLETA FINALIZADA: {len(self.businesses)} leads captados\n")
            
        except Exception as e:
            print(f"❌ ERRO GERAL: {e}")
            traceback.print_exc()
        finally:
            if self.driver:
                try: 
                    self.driver.quit()
                    print("🔒 Chrome fechado")
                except: 
                    pass
        
        return self.businesses

    def _scroll_results(self):
        """Scroll no painel de resultados"""
        print("📜 Fazendo scroll para carregar mais resultados...")
        try:
            # Múltiplos seletores para o painel
            panel_selectors = [
                'div[role="feed"]',
                'div.m6QErb.DxyBCb.kA9KIf.dS8AEf',
                'div.m6QErb',
                'div[aria-label*="Resultados"]'
            ]
            
            panel = None
            for sel in panel_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if elements:
                        panel = elements[0]
                        print(f"  ✅ Painel encontrado: {sel}")
                        break
                except:
                    continue
            
            if not panel:
                print("  ⚠️ Painel de scroll não encontrado - tentando scroll na página")
                for i in range(3):
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(1)
                return
            
            # Faz scroll no painel
            for i in range(6):
                if self.check_stop and self.check_stop(): 
                    break
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;", 
                    panel
                )
                time.sleep(1.5)
                print(f"  📜 Scroll {i+1}/6")
                
        except Exception as e:
            print(f"  ⚠️ Erro scroll: {e}")

    def _get_business_links(self):
        """Pega todos os links de negócios"""
        print("🔗 Coletando links dos resultados...")
        links = []
        
        # Múltiplos seletores - tenta todos
        link_selectors = [
            'a.hfpxzc',
            'a[href*="/maps/place/"]',
            'div[role="feed"] a[href*="maps"]',
            'div.Nv2PK a',
        ]
        
        for sel in link_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                print(f"  🔍 Seletor '{sel}': {len(elements)} elementos")
                
                if elements:
                    for e in elements:
                        href = e.get_attribute('href')
                        if href and '/maps/place/' in href and href not in links:
                            links.append(href)
                    
                    if len(links) > 0:
                        print(f"  ✅ {len(links)} links válidos com seletor: {sel}")
                        break
            except Exception as e:
                print(f"  ⚠️ Erro {sel}: {e}")
                continue
        
        # Remove duplicatas mantendo ordem
        unique = []
        seen = set()
        for link in links:
            if link not in seen:
                seen.add(link)
                unique.append(link)
        
        return unique

    def _extract_business_data(self, url):
        """Extrai dados de uma página de negócio"""
        data = {}
        
        try:
            self.driver.get(url)
            time.sleep(2.5)
            
            data['google_maps_link'] = url
            
            # NOME - tenta múltiplos seletores
            nome = ""
            name_selectors = ['h1.DUwDvf', 'h1', 'div.lMbq3e h1', 'span.DkMIZd']
            for sel in name_selectors:
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if el and el.text.strip():
                        nome = el.text.strip()
                        break
                except:
                    continue
            
            data['nome'] = nome
            if not nome:
                return None
            
            # Pega texto da página
            page_text = ""
            try:
                main = self.driver.find_element(By.CSS_SELECTOR, "div[role='main']")
                page_text = main.text
            except:
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                except:
                    pass
            
            # TELEFONE
            telefone = ""
            try:
                phone_btn = self.driver.find_element(By.CSS_SELECTOR, "button[data-item-id*='phone']")
                telefone = phone_btn.get_attribute('aria-label') or phone_btn.text
                telefone = re.sub(r'[^0-9()\-\s+]', '', telefone).strip()
            except:
                # Fallback: regex no texto
                phone_patterns = [r'\(?\d{2}\)?\s?\d{4,5}[-\s]?\d{4}']
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
                pass
            
            data['website'] = website
            data['tem_site'] = bool(website and len(website) > 5)
            
            # AVALIAÇÃO
            avaliacao = "0.0"
            try:
                rating_el = self.driver.find_element(By.CSS_SELECTOR, "div.F7nice span[aria-hidden='true']")
                avaliacao = rating_el.text.replace(',', '.')
            except:
                try:
                    match = re.search(r'(\d[,\.]\d)\s*estrela', page_text, re.IGNORECASE)
                    if match:
                        avaliacao = match.group(1).replace(',', '.')
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
                pass
            data['endereco'] = endereco
            
            # INSTAGRAM - busca link para instagram.com
            instagram = ""
            try:
                # Método 1: Botão específico de redes sociais
                social_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='instagram.com']")
                for btn in social_buttons:
                    href = btn.get_attribute('href')
                    if href and 'instagram.com' in href:
                        instagram = href
                        break
            except:
                pass
            
            if not instagram:
                try:
                    # Método 2: Busca no texto da página por @username
                    ig_match = re.search(r'@([a-zA-Z0-9_\.]+)', page_text)
                    if ig_match:
                        username = ig_match.group(1)
                        # Verifica se parece ser Instagram (não email)
                        if not '@' in username and len(username) > 2:
                            instagram = f"https://instagram.com/{username}"
                except:
                    pass
            
            if not instagram:
                try:
                    # Método 3: Links em qualquer lugar da página
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in all_links:
                        href = link.get_attribute('href') or ""
                        if 'instagram.com' in href and '/p/' not in href:  # Evita posts específicos
                            instagram = href
                            break
                except:
                    pass
            
            data['instagram'] = instagram
            data['tem_instagram'] = bool(instagram)
            
            # Metadata
            data['nicho'] = self.nicho
            data['cidade'] = self.cidade
            
            return data
            
        except Exception as e:
            print(f"    ⚠️ Extração erro: {e}")
            return None
