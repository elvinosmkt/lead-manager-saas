"""
Scraper SIMPLIFICADO - Funciona 100%
Coleta TODAS as empresas sem filtros complexos
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os
from datetime import datetime
import pandas as pd
from config import CONFIG


class GoogleMapsScraperSimples:
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
            
            search_box = self.driver.find_element(By.ID, "searchboxinput")
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.ENTER)
            time.sleep(5)
            
            # Scroll
            print("📜 Carregando resultados...")
            results_panel = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            
            for i in range(20):
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;",
                    results_panel
                )
                time.sleep(1)
                if i % 5 == 0:
                    print(f"  Scroll {i+1}/20...")
            
            print(f"✓ Resultados carregados!")
            
            # Coleta TODOS os nomes visíveis
            print("\n📊 Coletando TODAS as empresas (sem filtros)...")
            time.sleep(2)
            
            # Pega TODOS os elementos com nome de empresa
            all_results = self.driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK')
            
            print(f"📍 Encontradas {len(all_results)} empresas!")
            
            empresas_unicas = set()
            total_processadas = 0
            
            for idx, result in enumerate(all_results[:CONFIG["MAX_BUSINESSES"]]):
                try:
                    # Pega o nome
                    name_elements = result.find_elements(By.CSS_SELECTOR, 'div.qBF1Pd')
                    if not name_elements:
                        continue
                    
                    nome = name_elements[0].text.strip()
                    
                    if not nome or nome in empresas_unicas:
                        continue
                    
                    empresas_unicas.add(nome)
                    
                    # Clica no resultado
                    try:
                        result.click()
                        time.sleep(2)
                    except:
                        continue
                    
                    # Extrai dados (TODOS, sem filtro)
                    data = self._extract_all_info()
                    
                    if data and data['nome']:
                        if data['nome'] not in self.empresas_processadas:
                            self.empresas_processadas.add(data['nome'])
                            self.businesses.append(data)
                            total_processadas += 1
                            
                            # Status mais detalhado
                            status_parts = []
                            if not data['tem_site']:
                                status_parts.append("🚫 SEM SITE")
                            else:
                                status_parts.append(f"🌐 Site: {data['website'][:30]}...")
                            
                            if data['telefone']:
                                status_parts.append(f"📞 Tel")
                            
                            if data['whatsapp']:
                                status_parts.append("✅ WhatsApp")
                            
                            print(f"  [{total_processadas}] ✅ {nome} | {' | '.join(status_parts)}")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    continue
            
            print(f"\n🎉 Total coletado: {len(self.businesses)} empresas")
            
            # Estatísticas COMPLETAS
            sem_site = sum(1 for b in self.businesses if not b['tem_site'])
            com_site = sum(1 for b in self.businesses if b['tem_site'])
            com_telefone = sum(1 for b in self.businesses if b['telefone'])
            com_whatsapp = sum(1 for b in self.businesses if b['whatsapp'])
            sem_contato = sum(1 for b in self.businesses if not b['telefone'])
            leads_qualificados = sum(1 for b in self.businesses if not b['tem_site'] and b['whatsapp'])
            
            print(f"\n🎯 Estatísticas Completas:")
            print(f"   📊 Total: {len(self.businesses)} empresas")
            print(f"   🚫 Sem site próprio: {sem_site}")
            print(f"   🌐 Com site: {com_site}")
            print(f"   📞 Com telefone: {com_telefone}")
            print(f"   💬 Com WhatsApp: {com_whatsapp}")
            print(f"   ❌ Sem contato: {sem_contato}")
            print(f"   ⭐ Leads qualificados (sem site + WhatsApp): {leads_qualificados}")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.businesses
    
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
            
            # Link do Google Maps
            try:
                business_data['google_maps_link'] = self.driver.current_url
            except:
                business_data['google_maps_link'] = ''
            
            # Telefone
            telefone = ""
            try:
                phone_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-item-id*="phone"]')
                phone_text = phone_button.get_attribute('aria-label')
                if phone_text:
                    telefone = phone_text.replace('Telefone: ', '').replace('Copiar número de telefone', '').strip()
            except:
                pass
            
            business_data['telefone'] = telefone
            
            # WhatsApp
            whatsapp = ""
            if telefone:
                clean = re.sub(r'\D', '', telefone)
                if len(clean) >= 10:
                    if not clean.startswith('55'):
                        clean = '55' + clean
                    whatsapp = clean
            
            business_data['whatsapp'] = whatsapp
            business_data['whatsapp_link'] = f"https://wa.me/{whatsapp}" if whatsapp else ""
            
            # Website
            tem_site = False
            website = ""
            try:
                website_elem = self.driver.find_element(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
                href = website_elem.get_attribute('href')
                if href:
                    # Lista COMPLETA de plataformas que NÃO são sites próprios
                    plataformas_nao_site = [
                        # Redes Sociais
                        'instagram.com', 'facebook.com', 'fb.com', 'fb.me',
                        'tiktok.com', 'twitter.com', 'x.com', 'linkedin.com',
                        'youtube.com', 'pinterest.com', 'snapchat.com',
                        
                        # Mensageiros
                        'whatsapp.com', 'wa.me', 'telegram.me', 't.me',
                        'wechat.com', 'viber.com',
                        
                        # Plataformas de Agendamento
                        'booking.com', 'agendor.com', 'calendly.com',
                        'acuityscheduling.com', 'setmore.com', 'simplybook.me',
                        'genial.ly', 'linktr.ee', 'beacons.ai',
                        
                        # Marketplaces e Avaliações
                        'tripadvisor.com', 'yelp.com', 'foursquare.com',
                        'zomato.com', 'ifood.com.br', 'rappi.com',
                        
                        # Google
                        'google.com', 'goo.gl', 'maps.google.com',
                        'g.page', 'business.google.com',
                        
                        # Outros
                        'sympla.com.br', 'eventbrite.com', 'linkin.bio',
                        'bit.ly', 'tiny.url', 'ow.ly'
                    ]
                    
                    href_lower = href.lower()
                    is_plataforma = any(plat in href_lower for plat in plataformas_nao_site)
                    
                    if not is_plataforma:
                        tem_site = True
                        website = href
            except:
                pass
            
            business_data['tem_site'] = tem_site
            business_data['website'] = website
            
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
                rating = self.driver.find_element(By.CSS_SELECTOR, 'div.F7nice span[aria-hidden="true"]')
                business_data['avaliacao'] = rating.text.strip()
            except:
                business_data['avaliacao'] = ''
            
            # Número de avaliações
            try:
                reviews_element = self.driver.find_element(By.CSS_SELECTOR, 'div.F7nice span[aria-label*="avaliações"]')
                business_data['num_avaliacoes'] = reviews_element.get_attribute('aria-label').strip()
            except:
                business_data['num_avaliacoes'] = ''
            
            # Categoria/Segmento
            try:
                category_button = self.driver.find_element(By.CSS_SELECTOR, 'button[jsaction*="category"]')
                business_data['segmento'] = category_button.get_attribute('aria-label').strip()
            except:
                business_data['segmento'] = self.nicho  # Usa nicho como fallback
            
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
    
    def save_to_excel(self, filename=None):
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
            'nome', 'tem_site', 'whatsapp', 'whatsapp_link',
            'telefone', 'website', 'endereco', 'avaliacao',
            'nicho', 'cidade', 'contatado', 'respondeu',
            'observacoes', 'data_coleta'
        ]
        df = df[[col for col in columns if col in df.columns]]
        
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n📊 Salvo: {filename}")
        print(f"✅ {len(self.businesses)} empresas exportadas!")
        
        return filename
