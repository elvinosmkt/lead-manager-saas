import asyncio
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
import pandas as pd
from config import CONFIG


class GoogleMapsScraper:
    def __init__(self, nicho: str, cidade: str):
        """
        Inicializa o scraper do Google Maps
        
        Args:
            nicho: O nicho do negócio (ex: "estética", "salão de beleza", etc)
            cidade: A cidade para buscar (ex: "São Paulo, SP")
        """
        self.nicho = nicho
        self.cidade = cidade
        self.businesses = []
        
    async def scrape(self):
        """Executa o processo completo de scraping"""
        print("🌐 Iniciando navegador...")
        
        async with async_playwright() as p:
            try:
                # Inicia o navegador com configurações mais robustas
                browser = await p.chromium.launch(
                    headless=CONFIG["HEADLESS"],
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='pt-BR'
                )
                
                page = await context.new_page()
                
                # Remove detecção de webdriver
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                try:
                    # Busca no Google Maps
                    search_query = f"{self.nicho} em {self.cidade}"
                    await self._search_google_maps(page, search_query)
                    
                    # Aguarda os resultados carregarem
                    print("⏳ Aguardando resultados...")
                    await page.wait_for_timeout(5000)
                    
                    # Coleta os dados das empresas
                    await self._collect_businesses(page)
                    
                    print(f"\n✓ Total de empresas coletadas: {len(self.businesses)}")
                    
                except Exception as e:
                    print(f"\n❌ Erro durante o scraping: {str(e)}")
                    raise
                    
                finally:
                    await browser.close()
                    
            except Exception as e:
                print(f"\n❌ Erro ao iniciar navegador: {str(e)}")
                raise
        
        return self.businesses
    
    async def _search_google_maps(self, page: Page, query: str):
        """Realiza a busca no Google Maps"""
        print(f"🔍 Buscando: {query}")
        
        try:
            # Acessa o Google Maps
            await page.goto("https://www.google.com/maps", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Busca pelo nicho e cidade
            print("⌨️  Digitando busca...")
            search_box = await page.wait_for_selector('input#searchboxinput', timeout=10000)
            if search_box:
                await search_box.click()
                await page.wait_for_timeout(500)
                await search_box.fill(query)
                await page.wait_for_timeout(1000)
                await page.keyboard.press('Enter')
                print("✓ Busca enviada!")
                await page.wait_for_timeout(5000)
            else:
                print("❌ Não encontrou a caixa de busca")
                
        except PlaywrightTimeoutError:
            print("⚠️ Timeout ao carregar Google Maps")
            raise
        except Exception as e:
            print(f"❌ Erro na busca: {str(e)}")
            raise
    
    async def _collect_businesses(self, page: Page):
        """Coleta informações das empresas"""
        print("\n📊 Coletando informações das empresas...")
        
        try:
            # Scroll para carregar mais resultados
            await self._scroll_results(page)
            
            # Pega todos os links de empresas
            print("🔎 Buscando links de empresas...")
            business_links = await page.query_selector_all('a[href*="/maps/place/"]')
            
            if not business_links:
                print("⚠️ Nenhuma empresa encontrada nos resultados")
                return
            
            total = min(len(business_links), CONFIG["MAX_BUSINESSES"])
            print(f"📍 Encontradas {len(business_links)} empresas. Processando até {total}...\n")
            
            for idx, link in enumerate(business_links[:total], 1):
                try:
                    print(f"[{idx}/{total}] Processando empresa...")
                    
                    # Clica no negócio com tratamento de erro
                    try:
                        await link.click(timeout=5000)
                        await page.wait_for_timeout(3000)
                    except:
                        print("⚠️ Não foi possível clicar no link, pulando...")
                        continue
                    
                    # Extrai as informações
                    business_data = await self._extract_business_info(page)
                    
                    if business_data:
                        # Verifica se tem WhatsApp e não tem website
                        if business_data.get('whatsapp') and not business_data.get('website'):
                            self.businesses.append(business_data)
                            print(f"✅ Adicionada: {business_data['nome']}")
                        else:
                            if business_data.get('website'):
                                print(f"⏭️  Ignorada (tem website): {business_data.get('nome', 'N/A')}")
                            else:
                                print(f"⏭️  Ignorada (sem WhatsApp): {business_data.get('nome', 'N/A')}")
                    
                    await page.wait_for_timeout(CONFIG["DELAY_BETWEEN_BUSINESSES"] * 1000)
                    
                except Exception as e:
                    print(f"⚠️ Erro ao processar empresa {idx}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"❌ Erro ao coletar empresas: {str(e)}")
            raise
    
    async def _scroll_results(self, page: Page):
        """Faz scroll na lista de resultados para carregar mais empresas"""
        print("📜 Carregando mais resultados...")
        
        try:
            # Localiza o painel de resultados
            results_panel = await page.query_selector('div[role="feed"]')
            
            if results_panel:
                for i in range(3):  # Reduzido para 3 scrolls
                    print(f"  Scroll {i+1}/3...")
                    await page.evaluate('''
                        () => {
                            const element = document.querySelector('div[role="feed"]');
                            if (element) element.scrollTop = element.scrollHeight;
                        }
                    ''')
                    await page.wait_for_timeout(CONFIG["DELAY_BETWEEN_SCROLLS"] * 1000)
                print("✓ Scroll completo")
            else:
                print("⚠️ Painel de resultados não encontrado")
                
        except Exception as e:
            print(f"⚠️ Erro ao fazer scroll: {str(e)}")
    
    async def _extract_business_info(self, page: Page) -> dict:
        """Extrai informações de um negócio específico"""
        try:
            business_data = {}
            
            # Aguarda a página carregar
            await page.wait_for_timeout(2000)
            
            # Nome do negócio
            try:
                name_element = await page.wait_for_selector('h1', timeout=5000)
                if name_element:
                    business_data['nome'] = (await name_element.inner_text()).strip()
            except:
                print("  ⚠️ Nome não encontrado")
                return None
            
            # Endereço
            try:
                address_element = await page.query_selector('button[data-item-id="address"]')
                if address_element:
                    aria_label = await address_element.get_attribute('aria-label')
                    if aria_label:
                        business_data['endereco'] = aria_label.replace('Endereço: ', '').strip()
            except:
                pass
            
            # Telefone
            try:
                phone_element = await page.query_selector('button[data-item-id*="phone"]')
                if phone_element:
                    aria_label = await phone_element.get_attribute('aria-label')
                    if aria_label:
                        business_data['telefone'] = aria_label.replace('Telefone: ', '').replace('Copiar número de telefone', '').strip()
            except:
                pass
            
            # Website
            try:
                website_element = await page.query_selector('a[data-item-id="authority"]')
                if website_element:
                    aria_label = await website_element.get_attribute('aria-label')
                    if aria_label:
                        business_data['website'] = aria_label.replace('Website: ', '').strip()
            except:
                pass
            
            # WhatsApp - verifica no telefone se é WhatsApp
            business_data['whatsapp'] = self._extract_whatsapp(business_data.get('telefone', ''))
            
            # Rating
            try:
                rating_element = await page.query_selector('div.F7nice span[aria-hidden="true"]')
                if rating_element:
                    business_data['avaliacao'] = (await rating_element.inner_text()).strip()
            except:
                pass
            
            # Número de reviews
            try:
                reviews_element = await page.query_selector('div.F7nice span[aria-label*="avaliações"]')
                if not reviews_element:
                    reviews_element = await page.query_selector('div.F7nice span[aria-label*="avaliaç"]')
                if reviews_element:
                    aria_label = await reviews_element.get_attribute('aria-label')
                    if aria_label:
                        business_data['num_avaliacoes'] = aria_label.strip()
            except:
                pass
            
            return business_data
            
        except Exception as e:
            print(f"  ⚠️ Erro ao extrair informações: {str(e)}")
            return None
    
    def _extract_whatsapp(self, phone: str) -> str:
        """
        Extrai e formata número de WhatsApp
        Remove caracteres especiais e verifica se é um número brasileiro válido
        """
        if not phone:
            return ""
        
        # Remove todos os caracteres não numéricos
        clean_phone = re.sub(r'\D', '', phone)
        
        # Verifica se tem pelo menos 10 dígitos (telefone brasileiro)
        if len(clean_phone) >= 10:
            # Formata para WhatsApp (adiciona +55 se não tiver código do país)
            if not clean_phone.startswith('55'):
                clean_phone = '55' + clean_phone
            
            return clean_phone
        
        return ""
    
    def save_to_excel(self, filename: str = None):
        """Salva os dados coletados em um arquivo Excel"""
        if not self.businesses:
            print("⚠️ Nenhuma empresa para salvar!")
            return
        
        # Cria o diretório de saída se não existir
        os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)
        
        # Define o nome do arquivo
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Limpa o nome da cidade para usar no arquivo
            cidade_limpa = self.cidade.replace(",", "").replace(" ", "_")
            filename = f"{CONFIG['OUTPUT_DIR']}/leads_{self.nicho}_{cidade_limpa}_{timestamp}.xlsx"
        
        # Cria o DataFrame
        df = pd.DataFrame(self.businesses)
        
        # Reordena as colunas
        columns = ['nome', 'telefone', 'whatsapp', 'endereco', 'avaliacao', 'num_avaliacoes']
        df = df.reindex(columns=[col for col in columns if col in df.columns], axis=1)
        
        # Salva no Excel
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n📊 Arquivo salvo: {filename}")
        print(f"📈 Total de leads: {len(self.businesses)}")
        
        return filename


async def main():
    """Função principal"""
    print("=" * 60)
    print("🎯 GOOGLE MAPS LEAD SCRAPER")
    print("=" * 60)
    
    # Solicita informações ao usuário
    nicho = input("\n📌 Digite o nicho (ex: estética, salão de beleza): ").strip()
    cidade = input("📍 Digite a cidade e estado (ex: São Paulo, SP): ").strip()
    
    if not nicho or not cidade:
        print("❌ Nicho e cidade são obrigatórios!")
        return
    
    print(f"\n🚀 Iniciando busca por '{nicho}' em '{cidade}'...")
    print("⏳ Isso pode levar alguns minutos...\n")
    
    # Cria o scraper e executa
    scraper = GoogleMapsScraper(nicho, cidade)
    
    try:
        await scraper.scrape()
        
        # Salva os resultados
        if scraper.businesses:
            scraper.save_to_excel()
            print("\n✅ Processo concluído com sucesso!")
        else:
            print("\n⚠️ Nenhuma empresa encontrada com os critérios especificados.")
            print("   (Empresas sem site e com WhatsApp)")
    except Exception as e:
        print(f"\n❌ Erro fatal: {str(e)}")
        print("\nDica: Tente novamente ou ajuste os parâmetros em config.py")


if __name__ == "__main__":
    asyncio.run(main())
