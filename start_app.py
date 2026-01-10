"""
Servidor Multi-usuário com Fila e Isolamento de Sessão
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
# MAX_CONCURRENT_SEARCHES = 2 é seguro.
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
                # Verifica cancelamento antes de começar
                if state.get('stop_requested'):
                     print(f"🛑 [ID: {self.session_id}] Cancelado antes de iniciar.")
                     state['status'] = 'cancelled'
                     return

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
                
                # Injeta a verificação de parada
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
                pass


# --- ENDPOINTS (RESTAURADOS) ---

@app.route('/')
def home():
    return send_from_directory('webapp', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('webapp', path)

@app.route('/api/start-search', methods=['POST'])
def start_search():
    try:
        data = request.json
        nicho = data.get('nicho')
        cidade = data.get('cidade')
        max_leads = int(data.get('max_leads', 10))
        user_id = data.get('user_id') # User ID do Supabase
        
        # Filtros Opcionais
        filters = {
            'site': data.get('filter_site', 'todos'),
            'whats': data.get('filter_whats', 'todos')
        }

        if not nicho or not cidade or not user_id:
            return jsonify({'error': 'Parâmetros inválidos'}), 400

        # Verifica se já existe busca rodando para este user
        if user_id in active_searches and active_searches[user_id]['status'] in ['running', 'queued']:
             # Se tiver rodando, retorna session existente ou erro
             # (Opcional: permitir cancelar anterior implicitamente)
             pass

        # Inicializa estado
        active_searches[user_id] = {
            'status': 'initializing',
            'leads': [],
            'leads_found': 0,
            'total': max_leads,
            'current': f"Inicializando {nicho}...",
            'completed': False,
            'stop_requested': False,
            'started_at': None
        }

        # Inicia Worker em Background
        worker = SearchWorker(user_id, nicho, cidade, max_leads, filters)
        worker.start()

        return jsonify({'success': True, 'session_id': user_id, 'status': 'queued'})

    except Exception as e:
        print(f"Erro ao iniciar: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-status', methods=['GET'])
def search_status():
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in active_searches:
        return jsonify({'status': 'not_found', 'leads': [], 'leads_found': 0})
        
    state = active_searches[session_id]
    
    # Retorna resumo
    return jsonify({
        'status': state.get('status', 'unknown'),
        'leads': state.get('leads', [])[-20:], # Retorna apenas ultimos 20 para economizar banda (frontend deve acumular)
        'leads_found': state.get('leads_found', 0),
        'current': state.get('current', ''),
        'completed': state.get('completed', False),
        'error': state.get('error'),
        # Info de Fila
        'position': 1 if state.get('status') == 'queued' else 0 # Simplificado
    })

@app.route('/api/cancel-search', methods=['POST'])
def cancel_search():
    try:
        data = request.json or {}
        session_id = data.get('user_id') or request.args.get('user_id')
        
        if not session_id or session_id not in active_searches:
            return jsonify({'error': 'Sessão não encontrada'}), 404
            
        active_searches[session_id]['stop_requested'] = True
        print(f"🛑 Solicitado cancelamento para: {session_id}")
        
        return jsonify({'success': True, 'message': 'Parando busca...'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-status', methods=['POST'])
def reset_status():
    global active_searches
    active_searches = {}
    try:
        os.system("pkill chrome")
        os.system("pkill chromium")
    except: pass
    return jsonify({'success': True, 'message': 'Sistema resetado'})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Server is running', 'active_searches': len(active_searches)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
