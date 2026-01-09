"""
SCRAPER OTIMIZADO - Versão headless com atualização em tempo real
- Roda sem abrir janela do navegador
- Atualiza leads em tempo real
- Foca APENAS em leads sem site próprio
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os
from datetime import datetime
from config import CONFIG


class GoogleMapsScraperOtimizado:
    """
    Scraper otimizado que:
    1. Roda em modo headless (invisível)
    2. Atualiza estado em tempo real
    3. Pega APENAS leads sem site
    4. Melhor estratégia de coleta
    """
    
    def __init__(self, nicho: str, cidade: str, callback=None):
        self.nicho = nicho
        self.cidade = cidade
        self.businesses = []
        self.empresas_processadas = set()
        self.driver = None
        self.callback = callback  # Função para atualizar estado em tempo real
        
    def _update_progress(self, current, total, lead=None):
        """Atualiza progresso em tempo real"""
        if self.callback:
            self.callback({
                'progress': int((current / total) * 100) if total > 0 else 0,
                'current': current,
                'total': total,
                'leads_found': len(self.businesses),
                'latest_lead': lead
            })
    
    def scrape(self):
        """Executa scraping completo"""
        print("🚀 Iniciando scraper otimizado...")
        
        chrome_options = Options()
        
        # MODO HEADLESS - Não abre janela visível
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent realista
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            # Configura driver
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
            
            # Remove detecção de webdriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            search_query = f"{self.nicho} em {self.cidade}"
            print(f"🔍 Buscando: {search_query}")
            
            # Vai para Google Maps
            maps_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
            self.driver.get(maps_url)
            print("⏳ Aguardando resultados...")
            time.sleep(5)
            
            # Scroll para carregar TODOS os resultados
            print("📜 Carregando todos os resultados...")
            self._scroll_all_results()
            
            # Coleta todos os links
            print("📊 Coletando links...")
            links = self._get_all_business_links()
            
            if not links:
                print("❌ Nenhum resultado encontrado!")
                return self.businesses
            
            print(f"✅ Encontrados {len(links)} estabelecimentos")
            
            # Processa cada link e filtra apenas SEM SITE
            self._process_businesses(links)
            
            print(f"\n🎉 Coleta concluída!")
            print(f"🎯 Leads SEM SITE encontrados: {len(self.businesses)}")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.businesses
    
    def _scroll_all_results(self):
        """Scroll agressivo para carregar TODOS os resultados"""
        try:
            wait = WebDriverWait(self.driver, 15)
            
            # Localiza o painel de resultados
            panel_selectors = [
                'div[role="feed"]',
                'div.m6QErb.DxyBCb.kA9KIf.dS8AEf',
                'div[aria-label*="Resultados"]'
            ]
            
            panel = None
            for selector in panel_selectors:
                try:
                    panel = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"✅ Painel encontrado!")
                    break
                except:
                    continue
            
            if not panel:
                print("⚠️ Painel não encontrado, usando scroll de página")
                for i in range(10):
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(1)
                return
            
            # Scroll até o final - estratégia agressiva
            print("🔄 Scrolling para carregar todos os resultados...")
            previous_height = 0
            no_change_count = 0
            scroll_count = 0
            
            while no_change_count < 3 and scroll_count < 30:  # Máximo 30 scrolls
                # Scroll down
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;",
                    panel
                )
                time.sleep(2)
                
                # Verifica altura
                current_height = self.driver.execute_script(
                    "return arguments[0].scrollHeight;",
                    panel
                )
                
                if current_height == previous_height:
                    no_change_count += 1
                else:
                    no_change_count = 0
                
                previous_height = current_height
                scroll_count += 1
                
                if scroll_count % 5 == 0:
                    print(f"  Scroll {scroll_count}... ({no_change_count}/3 sem mudança)")
            
            print(f"✓ Scroll completo! ({scroll_count} scrolls realizados)")
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️ Erro no scroll: {e}")
    
    def _get_all_business_links(self):
        """Coleta TODOS os links de estabelecimentos"""
        links = set()
        
        try:
            # Estratégia 1: CSS Selector
            elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
            for elem in elements:
                href = elem.get_attribute('href')
                if href and '/maps/place/' in href:
                    clean_link = href.split('?')[0] if '?' in href else href
                    links.add(clean_link)
            
            print(f"  Estratégia 1: {len(links)} links")
            
            # Estratégia 2: JavaScript (fallback)
            if len(links) < 5:
                script = """
                let links = new Set();
                document.querySelectorAll('a').forEach(a => {
                    if (a.href && a.href.includes('/maps/place/')) {
                        links.add(a.href.split('?')[0]);
                    }
                });
                return Array.from(links);
                """
                js_links = self.driver.execute_script(script)
                links.update(js_links)
                print(f"  Estratégia 2 (JS): {len(links)} links total")
            
            return list(links)
            
        except Exception as e:
            print(f"⚠️ Erro ao coletar links: {e}")
            return []
    
    def _process_businesses(self, links):
        """Processa cada estabelecimento e adiciona APENAS os sem site"""
        max_leads = CONFIG.get("MAX_BUSINESSES", 200)
        total_to_process = min(len(links), max_leads * 3)  # Processa mais para compensar filtro
        
        print(f"\n🎯 Processando até {total_to_process} estabelecimentos...")
        print(f"📌 Buscando {max_leads} leads SEM SITE\n")
        
        for idx, link in enumerate(links[:total_to_process]):
            # Para se já temos leads suficientes
            if len(self.businesses) >= max_leads:
                print(f"\n✅ Meta atingida: {max_leads} leads sem site!")
                break
            
            try:
                # Atualiza progresso
                self._update_progress(idx + 1, total_to_process)
                
                print(f"[{idx+1}/{total_to_process}] Verificando... ", end='')
                
                # Abre o link
                self.driver.get(link)
                time.sleep(2.5)
                
                # Extrai dados
                data = self._extract_business_data()
                
                if not data or not data.get('nome'):
                    print("⏭️ Dados incompletos")
                    continue
                
                # FILTRO CRÍTICO: Adiciona APENAS se NÃO tem site
                if data.get('tem_site'):
                    print(f"🚫 {data['nome'][:35]} - TEM SITE (ignorado)")
                    continue
                
                # Verifica se já foi processado
                if data['nome'] in self.empresas_processadas:
                    print(f"⏭️ {data['nome'][:35]} - Duplicado")
                    continue
                
                # ADICIONA O LEAD (sem site!)
                self.empresas_processadas.add(data['nome'])
                self.businesses.append(data)
                
                # Atualiza com o novo lead
                self._update_progress(idx + 1, total_to_process, data)
                
                # Log bonito
                status = []
                if data.get('telefone'): status.append("📞")
                if data.get('whatsapp'): status.append("💬")
                status.append("🎯 SEM SITE")
                
                print(f"✅ {data['nome'][:35]} {' '.join(status)} [{len(self.businesses)}/{max_leads}]")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Erro: {str(e)[:40]}")
                continue
        
        print(f"\n📊 Total de leads SEM SITE: {len(self.businesses)}")
    
    def _extract_business_data(self):
        """Extrai dados do estabelecimento"""
        try:
            data = {}
            
            # NOME
            nome = self._extract_text([
                'h1.DUwDvf',
                'h1.fontHeadlineLarge',
                'h1'
            ])
            
            if not nome or len(nome) < 2:
                return None
            
            data['nome'] = nome
            data['google_maps_link'] = self.driver.current_url
            
            # TELEFONE
            telefone = self._extract_phone()
            data['telefone'] = telefone
            
            # WHATSAPP
            whatsapp = ""
            if telefone:
                clean = re.sub(r'\D', '', telefone)
                if len(clean) >= 10:
                    if not clean.startswith('55'):
                        clean = '55' + clean
                    whatsapp = clean
            data['whatsapp'] = whatsapp
            data['whatsapp_link'] = f"https://wa.me/{whatsapp}" if whatsapp else ""
            
            # WEBSITE (CRÍTICO PARA FILTRO!)
            website_data = self._extract_website()
            data['tem_site'] = website_data['tem_site']
            data['website'] = website_data['website']
            
            # ENDEREÇO
            endereco = self._extract_text([
                'button[data-item-id="address"]',
                'div[data-item-id="address"]'
            ], attr='aria-label')
            data['endereco'] = endereco.replace('Endereço:', '').strip() if endereco else ""
            
            # AVALIAÇÃO
            avaliacao = self._extract_text([
                'div.F7nice span[aria-hidden="true"]',
                'span.ceNzKf'
            ])
            data['avaliacao'] = avaliacao
            
            # REVIEWS
            reviews = self._extract_text([
                'div.F7nice span[aria-label*="avaliações"]'
            ], attr='aria-label')
            data['num_avaliacoes'] = reviews
            
            # CATEGORIA
            categoria = self._extract_text([
                'button[jsaction*="category"]'
            ], attr='aria-label')
            data['segmento'] = categoria if categoria else self.nicho
            
            # Metadados
            data['nicho'] = self.nicho
            data['cidade'] = self.cidade
            data['data_coleta'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['contatado'] = 'Não'
            data['respondeu'] = 'Não'
            data['observacoes'] = ''
            data['tags'] = ''
            
            return data
            
        except Exception as e:
            return None
    
    def _extract_text(self, selectors, attr=None):
        """Tenta múltiplos seletores"""
        for selector in selectors:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                if attr:
                    text = elem.get_attribute(attr)
                else:
                    text = elem.text
                
                if text and len(text.strip()) > 0:
                    return text.strip()
            except:
                continue
        return ""
    
    def _extract_phone(self):
        """Extrai telefone"""
        phone_selectors = [
            'button[data-item-id*="phone"]',
            'button[aria-label*="Telefone"]',
            'button[aria-label*="Phone"]'
        ]
        
        for selector in phone_selectors:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                phone = elem.get_attribute('aria-label')
                if phone:
                    phone = phone.replace('Telefone:', '').replace('Phone:', '').replace('Copiar', '').strip()
                    if phone:
                        return phone
            except:
                continue
        
        return ""
    
    def _extract_website(self):
        """
        Extrai website e determina se é site próprio
        CRÍTICO: Plataformas sociais NÃO contam como site
        """
        try:
            # Tenta encontrar link do website
            selectors = [
                'a[data-item-id="authority"]',
                'a[aria-label*="Site"]',
                'a[aria-label*="Website"]'
            ]
            
            for selector in selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    href = elem.get_attribute('href')
                    
                    if href:
                        # Plataformas que NÃO são sites próprios
                        plataformas_sociais = [
                            'instagram.com', 'facebook.com', 'whatsapp.com',
                            'wa.me', 'tiktok.com', 'twitter.com', 'linkedin.com',
                            'google.com', 'maps.google.com', 'youtube.com',
                            't.me', 'telegram.org', 'telegram.me'
                        ]
                        
                        is_social = any(plat in href.lower() for plat in plataformas_sociais)
                        
                        if is_social:
                            # Tem link mas é rede social = NÃO tem site
                            return {'tem_site': False, 'website': ""}
                        else:
                            # Tem site próprio
                            return {'tem_site': True, 'website': href}
                except:
                    continue
            
            # Não encontrou nenhum link = não tem site
            return {'tem_site': False, 'website': ""}
            
        except:
            return {'tem_site': False, 'website': ""}
