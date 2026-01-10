"""
Servidor Multi-usuário com Fila
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import time
import sys
import os
import uuid
from queue import Queue
from datetime import datetime

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_definitivo import GoogleMapsScraperDefinitivo
from config import CONFIG
from db_config import save_lead_to_cloud

app = Flask(__name__, static_folder='webapp', static_url_path='')
CORS(app)

# --- CONFIGURAÇÃO DE CONCORRÊNCIA ---
# No plano Hobby/Starter do Railway, temos ~512MB-1GB RAM.
# Cada Chrome gasta ~300MB. 
# MAX_CONCURRENT_SEARCHES = 2 é seguro. 3 é arriscado mas tentável.
MAX_CONCURRENT_SEARCHES = 2
semaphore = threading.Semaphore(MAX_CONCURRENT_SEARCHES)

# Armazena estado de cada busca por ID
# Formato: { 'session_id': { 'status': 'queued', 'leads': [], ... } }
active_searches = {}

class SearchWorker(threading.Thread):
    def __init__(self, session_id, nicho, cidade, max_leads, filters={}):
        super().__init__()
        self.session_id = session_id
        self.nicho = nicho
        self.cidade = cidade
        self.max_leads = max_leads
        self.filters = filters
        self.daemon = True

    def run(self):
        global active_searches
        state = active_searches[self.session_id]
        
        # Tenta adquirir vaga na execução (Semáforo)
        state['status'] = 'queued'
        print(f"⏳ [ID: {self.session_id}] Na fila de espera...")
        
        with semaphore:
            try:
                state['status'] = 'running'
                state['started_at'] = datetime.now()
                print(f"🚀 [ID: {self.session_id}] Iniciando busca: {self.nicho} - {self.cidade}")
                
                # Configura scraper
                CONFIG['MAX_BUSINESSES'] = self.max_leads
                CONFIG['FILTERS'] = self.filters # Passa filtros recebidos
                
                # Callback customizado para salvar e atualizar estado em tempo real
                def on_lead_found(lead):
                    # VERIFICA SE PEDIU PRA PARAR
                    if state.get('stop_requested'):
                        print(f"🛑 [ID: {self.session_id}] Busca interrompida pelo usuário.")
                        return # Retorna para parar processamento
                        
                    # Salva no estado local para o frontend pegar
                    state['leads'].append(lead)
                    state['leads_found'] += 1
                    # Tenta salvar no Supabase COM O ID DO USUÁRIO
                    threading.Thread(target=save_lead_to_cloud, args=(lead, self.session_id)).start()

                # Inicia Scraper
                scraper = GoogleMapsScraperDefinitivo(self.nicho, self.cidade)
                scraper.on_lead_found_callback = on_lead_found 
                
                # Injeta a verificação de parada dentro do Scraper também (monkey patching simples)
                # O scraper deve verificar scraper.should_stop() se implementado, ou podemos checar no callback
                # Como o callback é chamado a cada lead, se pararmos de consumir, ele termina.
                # Mas para parar o scroll, precisamos de mais controle. 
                # Adicionaremos uma função check_stop no scraper.
                scraper.check_stop = lambda: state.get('stop_requested', False)
                
                # Executa
                leads = scraper.scrape()
                
                # Atualiza final (se não foi cancelado forçado)
                if not state.get('stop_requested'):
                    state['leads'] = leads 
                    state['completed'] = True
                    state['status'] = 'completed'
                    state['progress'] = 100
                else:
                    state['status'] = 'cancelled'
                    state['running'] = False
                
                print(f"✅ [ID: {self.session_id}] Worker Finalizado.")
                
            except Exception as e:
                print(f"❌ [ID: {self.session_id}] Erro: {e}")
                state['error'] = str(e)
                state['status'] = 'error'
                state['completed'] = True
            finally:
                # Libera vaga no semáforo
                pass

# --- ENDPOINTS ---
# ... (código existente) ...

@app.route('/api/cancel-search', methods=['POST'])
def cancel_search():
    try:
        data = request.json or {}
        # Tenta pegar user_id do body ou query param (para compatibilidade)
        session_id = data.get('user_id') or request.args.get('user_id')
        
        if not session_id or session_id not in active_searches:
            return jsonify({'error': 'Sessão não encontrada'}), 404
            
        # Marca flag de parada
        active_searches[session_id]['stop_requested'] = True
        active_searches[session_id]['running'] = False
        
        print(f"🛑 Solicitado cancelamento para: {session_id}")
        return jsonify({'success': True, 'message': 'Parando busca...'})
    except Exception as e:
        print(f"Erro ao cancelar: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-status', methods=['POST'])
def reset_status():
    # Limpa apenas buscas antigas (garbage collection manual)
    global active_searches
    active_searches = {}
    
    # Tenta limpar processos Chrome zumbis (Funciona no Linux/Railway)
    try:
        os.system("pkill chrome")
        os.system("pkill chromium")
        print("🧹 Memória limpa: Processos Chrome removidos.")
    except:
        pass
        
    return jsonify({'success': True, 'message': 'Sistema resetado e memória limpa'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
