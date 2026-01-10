"""
SCRAPER DEFINITIVO - Usa Playwright para maior confiabilidade
Instale: pip install playwright
Execute: playwright install chromium
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
import json
from datetime import datetime
import pandas as pd
from config import CONFIG
# Integração Supabase
try:
    from db_config import save_lead_to_cloud
except ImportError:
    save_lead_to_cloud = None


class GoogleMapsScraperDefinitivo:
    """
    Scraper ultra-robusto com múltiplas estratégias de fallback
    """
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
        
        # User agent realista
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Modo Headless (Obrigatório para Servidores/Railway)
        if os.environ.get('CHROMEDRIVER_PATH') or os.environ.get('HEADLESS', 'false') == 'true':
            print("🖥️  Modo Servidor detectado: Rodando em Headless")
            chrome_options.add_argument('--headless=new')

        try:
            # Tenta usar o driver do sistema (Docker/Railway)
            system_driver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
            
            if os.path.exists(system_driver_path):
                print(f"🔧 Usando driver do sistema: {system_driver_path}")
                service = Service(system_driver_path)
            else:
                # Fallback para instalação automática (Local)
                print("⬇️  Baixando driver automaticamente...")
                driver_path = ChromeDriverManager().install()
                # Ajuste para novas versões do webdriver_manager que retornam caminho completo
                if os.path.isfile(driver_path):
                     service = Service(driver_path)
                else:
                    # Fallback para lógica antiga de diretório
                    driver_dir = os.path.dirname(driver_path)
                    chromedriver_path = os.path.join(driver_dir, 'chromedriver')
                    if not os.path.exists(chromedriver_path):
                         # Tenta encontrar em qualquer lugar do diretório
                         for root, dirs, files in os.walk(driver_dir):
                            if 'chromedriver' in files:
                                chromedriver_path = os.path.join(root, 'chromedriver')
                                break
                    service = Service(chromedriver_path)

            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Remove webdriver flag
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            search_query = f"{self.nicho} em {self.cidade}"
            print(f"🔍 Buscando: {search_query}")
            
            # Vai direto para Maps com busca
            maps_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
            self.driver.get(maps_url)
            print("⏳ Aguardando resultados...")
            time.sleep(5)
            
            # Scroll para carregar mais resultados
            print("📜 Carregando resultados...")
            self._scroll_results()
            
            # Extrai links dos resultados
            print("📊 Coletando dados...")
            self._collect_businesses()
            
            print(f"\n🎉 Coleta concluída: {len(self.businesses)} leads\n")
            if self.businesses:
                self._print_stats()
            else:
                print("⚠️  ATENÇÃO: Nenhum lead coletado!")
                print("💡 SOLUÇÃO TEMPORÁRIA: Use o arquivo de teste em dados_teste/leads_teste_100.xlsx")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.businesses
    
    def _scroll_results(self):
        """Scroll inteligente no painel de resultados"""
        try:
            # Tenta localizar o painel de resultados
            wait = WebDriverWait(self.driver, 10)
            
            # Múltiplos seletores para o painel
            panel_selectors = [
                'div[role="feed"]',
                'div.m6QErb',
                'div[aria-label*="Resultados"]',
                'div[jsaction*="mouseover"]'
            ]
            
            panel = None
            for selector in panel_selectors:
                try:
                    panel = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"✅ Painel encontrado com: {selector}")
                    break
                except:
                    continue
            
            if panel:
                for i in range(8):
                    # CHECAGEM DE CANCELAMENTO
                    if hasattr(self, 'check_stop') and self.check_stop():
                        print("🛑 Parada forçada pelo usuário (Scraper cancelado)!")
                        break
                    self.driver.execute_script(
                        "arguments[0].scrollTop = arguments[0].scrollHeight;",
                        panel
                    )
                    time.sleep(1.5)
                    if i % 3 == 0:
                        print(f"  Scroll {i+1}/8...")
            else:
                # Fallback: scroll na página
                print("⚠️  Usando scroll alternativo...")
                for i in range(5):
                    self.driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(1)
            
            print("✓ Resultados carregados!")
            
        except Exception as e:
            print(f"⚠️  Erro no scroll: {e}")
    
    def _collect_businesses(self):
        """Coleta dados dos negócios com múltiplas estratégias"""
        
        # ESTRATÉGIA 1: Coletar links primeiro
        links = self._get_business_links()
        
        if not links:
            print("⚠️  Nenhum link encontrado com ESTRATÉGIA 1")
            # ESTRATÉGIA 2: Fallback
            links = self._get_business_links_fallback()
        
        if not links:
            print("❌ Nenhum resultado encontrado com nenhuma estratégia!")
            return
        
        print(f"📍 Encontrados {len(links)} resultados")
        
        max_leads = min(len(links), CONFIG.get("MAX_BUSINESSES", 50))
        
        for idx, link in enumerate(links[:max_leads]):
            try:
                print(f"\n[{idx+1}/{max_leads}] Processando...")
                
                # Abre o link
                self.driver.get(link)
                time.sleep(3)
                
                # Extrai dados
                data = self._extract_business_data()
                
                if data and data.get('nome'):
                    if data['nome'] not in self.empresas_processadas:
                        self.empresas_processadas.add(data['nome'])
                        self.businesses.append(data)
                        
                        status = []
                        if data.get('telefone'): status.append("📞")
                        if data.get('whatsapp'): status.append("💬")
                        if not data.get('tem_site'): status.append("🎯")
                        
                        print(f"✅ {data['nome'][:40]} {' '.join(status)}")
                        
                        # Salva na nuvem
                        if save_lead_to_cloud:
                            save_lead_to_cloud(data)
                            
                    else:
                        print(f"⏭️  Já processado: {data['nome'][:40]}")
                else:
                    print(f"⚠️  Dados incompletos, pulando...")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Erro no item {idx}: {str(e)[:50]}")
                continue
    
    def _get_business_links(self):
        """Estratégia 1: Pega links dos resultados"""
        links = []
        try:
            # Procura todos os links que apontam para /maps/place/
            elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
            
            for elem in elements:
                href = elem.get_attribute('href')
                if href and '/maps/place/' in href:
                    # Remove parâmetros extras
                    clean_link = href.split('?')[0] if '?' in href else href
                    if clean_link not in links:
                        links.append(clean_link)
            
            return links[:CONFIG.get("MAX_BUSINESSES", 50)]
            
        except Exception as e:
            print(f"⚠️  Erro ao coletar links: {e}")
            return []
    
    def _get_business_links_fallback(self):
        """Estratégia 2: Fallback usando JavaScript"""
        try:
            script = """
            let links = [];
            document.querySelectorAll('a').forEach(a => {
                if (a.href && a.href.includes('/maps/place/')) {
                    links.push(a.href.split('?')[0]);
                }
            });
            return [...new Set(links)];
            """
            links = self.driver.execute_script(script)
            return links[:CONFIG.get("MAX_BUSINESSES", 50)]
        except:
            return []
    
    def _extract_business_data(self):
        """Extrai dados com múltiplos seletores de fallback"""
        try:
            data = {}
            
            # NOME - Múltiplas tentativas
            nome = self._extract_text([
                'h1.DUwDvf',
                'h1.fontHeadlineLarge',
                'h1',
                '[data-item-id*="title"]',
                'div.fontHeadlineLarge'
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
            
            # WEBSITE
            website_data = self._extract_website()
            data['tem_site'] = website_data['tem_site']
            data['website'] = website_data['website']
            
            # ENDEREÇO
            endereco = self._extract_text([
                'button[data-item-id="address"]',
                'div[data-item-id="address"]',
                '[aria-label*="Endereço"]',
            ], attr='aria-label')
            data['endereco'] = endereco.replace('Endereço:', '').strip() if endereco else ""
            
            # AVALIAÇÃO
            avaliacao = self._extract_text([
                'div.F7nice span[aria-hidden="true"]',
                'span.ceNzKf',
                '[aria-label*="estrelas"]'
            ])
            data['avaliacao'] = avaliacao
            
            # REVIEWS
            reviews = self._extract_text([
                'div.F7nice span[aria-label*="avaliações"]',
                'span.F7nice > span:last-child'
            ], attr='aria-label')
            data['num_avaliacoes'] = reviews
            
            # CATEGORIA
            categoria = self._extract_text([
                'button[jsaction*="category"]',
                '[class*="DkEaL"]'
            ], attr='aria-label')
            data['segmento'] = categoria if categoria else self.nicho
            
            # Metadados
            data['nicho'] = self.nicho
            data['cidade'] = self.cidade
            data['data_coleta'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['contatado'] = 'Não'
            data['respondeu'] = 'Não'
            data['observacoes'] = ''
            
            return data
            
        except Exception as e:
            print(f"⚠️  Erro na extração: {str(e)[:50]}")
            return None
    
    def _extract_text(self, selectors, attr=None):
        """Tenta múltiplos seletores até achar texto"""
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
        """Extração robusta de telefone"""
        # Tenta clicar no botão de telefone se existir
        phone_selectors = [
            'button[data-item-id*="phone"]',
            'button[aria-label*="Telefone"]',
            'button[aria-label*="Phone"]',
            '[data-tooltip*="phone"]'
        ]
        
        for selector in phone_selectors:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                
                # Tenta pegar do aria-label
                phone = elem.get_attribute('aria-label')
                if phone:
                    phone = phone.replace('Telefone:', '').replace('Phone:', '').replace('Copiar', '').strip()
                    if phone:
                        return phone
                
                # Tenta clicar e pegar
                try:
                    elem.click()
                    time.sleep(0.5)
                    phone = elem.get_attribute('aria-label') or elem.text
                    if phone:
                        return phone.replace('Telefone:', '').replace('Copiar', '').strip()
                except:
                    pass
                    
            except:
                continue
        
        return ""
    
    def _extract_website(self):
        """Extrai website e determina se é próprio"""
        try:
            elem = self.driver.find_element(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
            href = elem.get_attribute('href')
            
            if href:
                plataformas_nao_site = [
                    'instagram.com', 'facebook.com', 'whatsapp.com',
                    'wa.me', 'tiktok.com', 'twitter.com', 'linkedin.com',
                    'google.com', 'maps.google.com', 'youtube.com'
                ]
                
                is_plataforma = any(plat in href.lower() for plat in plataformas_nao_site)
                
                return {
                    'tem_site': not is_plataforma,
                    'website': href if not is_plataforma else ""
                }
        except:
            pass
        
        return {'tem_site': False, 'website': ""}
    
    def _print_stats(self):
        total = len(self.businesses)
        sem_site = sum(1 for b in self.businesses if not b.get('tem_site', True))
        com_tel = sum(1 for b in self.businesses if b.get('telefone'))
        com_whats = sum(1 for b in self.businesses if b.get('whatsapp'))
        qualificados = sum(1 for b in self.businesses if not b.get('tem_site', True) and b.get('whatsapp'))
        
        print(f"\n🎯 Estatísticas:")
        print(f"   📊 Total: {total}")
        print(f"   🚫 Sem site: {sem_site}")
        print(f"   📞 Com telefone: {com_tel}")
        print(f"   💬 Com WhatsApp: {com_whats}")
        print(f"   ⭐ Qualificados: {qualificados}")
    
    def save_to_excel(self, filename=None):
        if not self.businesses:
            print("⚠️  Nenhum lead para salvar!")
            return
        
        os.makedirs(CONFIG.get("OUTPUT_DIR", "output"), exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cidade_limpa = self.cidade.replace(",", "").replace(" ", "_")
            filename = f"{CONFIG.get('OUTPUT_DIR', 'output')}/leads_{self.nicho}_{cidade_limpa}_{timestamp}.xlsx"
        
        df = pd.DataFrame(self.businesses)
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n💾 Salvo: {filename}")
        return filename
