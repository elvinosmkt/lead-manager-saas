"""
Scraper Melhorado - APENAS empresas SEM site + COM WhatsApp
- Verificação rigorosa de site
- Remove duplicados
- Link direto do WhatsApp
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


class GoogleMapsScraperMelhorado:
    def __init__(self, nicho: str, cidade: str):
        self.nicho = nicho
        self.cidade = cidade
        self.businesses = []
        self.empresas_processadas = set()  # Para evitar duplicados
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
            import glob
            
            driver_path = ChromeDriverManager().install()
            driver_dir = os.path.dirname(driver_path)
            
            # Procura pelo executável chromedriver
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
            
            # Busca no Google Maps
            search_query = f"{self.nicho} em {self.cidade}"
            self._search_google_maps(search_query)
            
            # Aguarda os resultados carregarem
            print("⏳ Aguardando resultados...")
            time.sleep(5)
            
            # Coleta os dados das empresas
            self._collect_businesses()
            
            print(f"\n✓ Total de LEADS QUALIFICADOS coletados: {len(self.businesses)}")
            
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
        """Faz scroll na lista de resultados até carregar o máximo possível"""
        print("📜 Carregando MÁXIMO de resultados...")
        
        try:
            results_panel = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            
            last_height = 0
            scrolls_sem_mudanca = 0
            scroll_count = 0
            max_scrolls = 30  # Máximo de 30 scrolls (carrega ~300+ empresas)
            
            while scroll_count < max_scrolls:
                # Scroll para o final
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;",
                    results_panel
                )
                
                scroll_count += 1
                if scroll_count % 5 == 0:
                    print(f"  Scroll {scroll_count}/{max_scrolls}... (~{scroll_count * 10} empresas carregadas)")
                
                time.sleep(1.5)  # Aguarda carregar
                
                # Verifica se carregou mais conteúdo
                new_height = self.driver.execute_script(
                    "return arguments[0].scrollHeight", 
                    results_panel
                )
                
                if new_height == last_height:
                    scrolls_sem_mudanca += 1
                    if scrolls_sem_mudanca >= 3:
                        print(f"  ✓ Carregados todos os resultados disponíveis ({scroll_count} scrolls)")
                        break
                else:
                    scrolls_sem_mudanca = 0
                
                last_height = new_height
            
            if scroll_count >= max_scrolls:
                print(f"  ✓ Limite de scrolls atingido ({max_scrolls} scrolls)")
            
        except Exception as e:
            print(f"⚠️ Erro ao fazer scroll: {str(e)}")
    
    def _has_website(self) -> tuple[bool, str]:
        """
        Verifica se a empresa tem website PRÓPRIO
        Instagram, Facebook, TikTok, etc = NÃO TEM SITE
        Apenas sites .com, .com.br, etc = TEM SITE
        Retorna (tem_site: bool, url_site: str)
        """
        try:
            # Lista de redes sociais/plataformas que NÃO contam como site
            redes_sociais = [
                'instagram.com', 'facebook.com', 'fb.com', 'fb.me',
                'tiktok.com', 'twitter.com', 'linkedin.com',
                'youtube.com', 'whatsapp.com', 'wa.me',
                'telegram.me', 't.me', 'pinterest.com',
                'google.com', 'goo.gl', 'maps.google.com',
                'booking.com', 'agendor.com', 'calendly.com',
                'sympla.com.br', 'eventbrite.com'
            ]
            
            # Procura por link de website
            website_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
            
            if website_elements:
                for elem in website_elements:
                    href = elem.get_attribute('href')
                    aria_label = elem.get_attribute('aria-label')
                    
                    if href and 'http' in href:
                        # Verifica se é rede social
                        is_social_media = False
                        for rede in redes_sociais:
                            if rede in href.lower():
                                is_social_media = True
                                break
                        
                        # Se NÃO é rede social = é site próprio
                        if not is_social_media:
                            website_url = aria_label.replace('Website: ', '').strip() if aria_label else href
                            return True, website_url
            
            # Verifica links de agendamento (também não contam como site próprio)
            # Mas não vamos considerar como "tem site"
            
            return False, ""
            
        except Exception as e:
            return False, ""
    
    def _collect_businesses(self):
        """Coleta APENAS empresas SEM site e COM WhatsApp"""
        print("\n📊 Coletando APENAS empresas SEM SITE e COM WHATSAPP...")
        print("🔍 Verificação rigorosa ativada\n")
        
        try:
            # Scroll para carregar mais resultados
            self._scroll_results()
            
            # Pega APENAS os links de empresas no painel de resultados (não elementos duplicados)
            print("🔎 Buscando links de empresas...")
            
            # Seletor mais específico para pegar apenas resultados reais
            time.sleep(2)
            results_feed = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            business_links = results_feed.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')
            
            if not business_links:
                print("⚠️ Nenhuma empresa encontrada")
                return
            
            # Remove duplicados pela URL antes de processar
            unique_hrefs = set()
            unique_links = []
            for link in business_links:
                href = link.get_attribute('href')
                if href and '/maps/place/' in href and href not in unique_hrefs:
                    unique_hrefs.add(href)
                    unique_links.append(link)
            
            total = min(len(unique_links), CONFIG["MAX_BUSINESSES"])
            print(f"📍 Encontradas {len(unique_links)} empresas únicas. Processando até {total}...\n")
            
            leads_encontrados = 0
            processadas = 0
            
            for idx in range(total):
                try:
                    # Re-busca os links a cada iteração (para evitar stale elements)
                    results_feed = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
                    business_links = results_feed.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')
                    
                    # Pega apenas links únicos novamente
                    unique_hrefs_new = set()
                    unique_links_new = []
                    for link in business_links:
                        href = link.get_attribute('href')
                        if href and '/maps/place/' in href and href not in unique_hrefs_new:
                            unique_hrefs_new.add(href)
                            unique_links_new.append(link)
                    
                    if idx >= len(unique_links_new):
                        break
                    
                    processadas += 1
                    print(f"[{processadas}/{total}] Processando empresa...")
                    
                    # Clica no negócio
                    try:
                        unique_links_new[idx].click()
                        time.sleep(3)
                    except:
                        continue
                    
                    # Extrai o nome primeiro
                    try:
                        name_element = self.driver.find_element(By.CSS_SELECTOR, 'h1')
                        nome = name_element.text.strip()
                    except:
                        print("  ⚠️ Nome não encontrado, pulando...")
                        continue
                    
                    # Verifica duplicado
                    if nome in self.empresas_processadas:
                        print(f"  ⏭️  Duplicado ignorado: {nome}")
                        continue
                    
                    self.empresas_processadas.add(nome)
                    
                    # Verifica se tem website PRÓPRIO (não redes sociais)
                    tem_site, url_site = self._has_website()
                    
                    if tem_site:
                        print(f"  ❌ TEM SITE: {nome}")
                        print(f"     Site: {url_site}")
                        continue
                    
                    # Se não tem site, extrai todas as informações
                    business_data = self._extract_business_info()
                    
                    if business_data:
                        # Verifica se tem WhatsApp
                        if business_data.get('whatsapp'):
                            self.businesses.append(business_data)
                            leads_encontrados += 1
                            print(f"  ✅ LEAD #{leads_encontrados}: {business_data['nome']}")
                            print(f"     📱 WhatsApp: {business_data['whatsapp']}")
                            print(f"     🔗 Link: {business_data['whatsapp_link']}")
                        else:
                            print(f"  ⏭️  SEM WHATSAPP: {nome}")
                    
                    time.sleep(CONFIG["DELAY_BETWEEN_BUSINESSES"])
                    
                except Exception as e:
                    print(f"  ⚠️ Erro ao processar empresa: {str(e)}")
                    continue
            
            print(f"\n🎯 Total de leads qualificados: {leads_encontrados}")
                    
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
            
            # WhatsApp
            whatsapp_numero = self._extract_whatsapp(business_data.get('telefone', ''))
            business_data['whatsapp'] = whatsapp_numero
            business_data['whatsapp_link'] = f"https://wa.me/{whatsapp_numero}" if whatsapp_numero else ""
            
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
            
            # Adiciona metadados
            business_data['nicho'] = self.nicho
            business_data['cidade'] = self.cidade
            business_data['data_coleta'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            business_data['contatado'] = 'Não'
            business_data['respondeu'] = 'Não'
            business_data['observacoes'] = ''
            
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
        """Salva os leads qualificados em Excel"""
        if not self.businesses:
            print("⚠️ Nenhum lead qualificado para salvar!")
            return
        
        os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cidade_limpa = self.cidade.replace(",", "").replace(" ", "_")
            filename = f"{CONFIG['OUTPUT_DIR']}/leads_{self.nicho}_{cidade_limpa}_{timestamp}.xlsx"
        
        df = pd.DataFrame(self.businesses)
        
        # Reordena as colunas
        columns = [
            'nome', 'telefone', 'whatsapp', 'whatsapp_link', 'endereco', 
            'avaliacao', 'num_avaliacoes', 'nicho', 'cidade', 
            'contatado', 'respondeu', 'observacoes', 'data_coleta'
        ]
        df = df[[col for col in columns if col in df.columns]]
        
        # Salva no Excel
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n📊 Arquivo salvo: {filename}")
        print(f"🎯 Total de leads: {len(self.businesses)}")
        print(f"\n💡 Dica: Clique nos links da coluna 'whatsapp_link' para enviar mensagem!")
        
        return filename


def main():
    print("=" * 60)
    print("🎯 GOOGLE MAPS LEAD SCRAPER - VERSÃO MELHORADA")
    print("   (APENAS empresas SEM site + COM WhatsApp)")
    print("=" * 60)
    
    nicho = input("\n📌 Digite o nicho (ex: estética): ").strip()
    cidade = input("📍 Digite a cidade e estado (ex: Curitiba, PR): ").strip()
    
    if not nicho or not cidade:
        print("❌ Nicho e cidade são obrigatórios!")
        return
    
    print(f"\n🚀 Iniciando busca por '{nicho}' em '{cidade}'...")
    print("🔍 Verificação rigorosa: APENAS empresas SEM site")
    print("⏳ Isso pode levar alguns minutos...\n")
    
    scraper = GoogleMapsScraperMelhorado(nicho, cidade)
    
    try:
        scraper.scrape()
        
        if scraper.businesses:
            scraper.save_to_excel()
            print("\n✅ Processo concluído com sucesso!")
        else:
            print("\n⚠️ Nenhum lead qualificado encontrado.")
            print("   (Todas as empresas já têm site ou não têm WhatsApp)")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")


if __name__ == "__main__":
    main()
