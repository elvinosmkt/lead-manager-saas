
"""
Servidor Multi-usuário com Fila, Memory Warning e Garbage Collection
"""
import os
import psutil  # Para monitorar memória
import threading
import time
import sys
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from queue import Queue
from datetime import datetime

# Path Setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_definitivo import GoogleMapsScraperDefinitivo
from config import CONFIG
from db_config import save_lead_to_cloud

app = Flask(__name__, static_folder='webapp', static_url_path='')
CORS(app)

# --- CONFIGURAÇÃO DE SEGURANÇA E RECURSOS ---
MAX_CONCURRENT_SEARCHES = 1  # Segurança máxima para plano Free/Hobby (evita OOM)
MAX_RAM_PERCENT = 85.0       # Se passar disso, rejeita novas buscas

semaphore = threading.Semaphore(MAX_CONCURRENT_SEARCHES)
active_searches = {}

def check_system_health():
    """Verifica se o servidor tem recursos para aceitar nova busca"""
    mem = psutil.virtual_memory()
    if mem.percent > MAX_RAM_PERCENT:
        return False, f"Servidor sobrecarregado (RAM: {mem.percent}%). Tente em 1 min."
    return True, "OK"

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
        state = active_searches.get(self.session_id)
        if not state: return

        state['status'] = 'queued'
        print(f"⏳ [ID: {self.session_id}] Na fila...")

        with semaphore:
            # Double check health antes de abrir o Chrome
            is_healthy, msg = check_system_health()
            if not is_healthy:
                print(f"❌ Abortando busca por falta de memória: {msg}")
                state['error'] = "Servidor ocupado (Memória Cheia). Tente novamente."
                state['status'] = 'error'
                state['completed'] = True
                return

            try:
                if state.get('stop_requested'): return

                state['status'] = 'running'
                print(f"🚀 [ID: {self.session_id}] Iniciando Chrome...")

                CONFIG['MAX_BUSINESSES'] = self.max_leads
                CONFIG['FILTERS'] = self.filters

                def on_lead_found(lead):
                    if state.get('stop_requested'): return
                    state['leads'].append(lead)
                    state['leads_found'] += 1
                    # Atualiza info de progresso em tempo real
                    state['current'] = lead.get('nome', 'Processando...')[:40]
                    state['progress'] = min(100, int((state['leads_found'] / self.max_leads) * 100))
                    # Salva no Supabase (Thread separada)
                    threading.Thread(target=save_lead_to_cloud, args=(lead, self.session_id)).start()

                scraper = GoogleMapsScraperDefinitivo(self.nicho, self.cidade)
                scraper.on_lead_found_callback = on_lead_found
                scraper.check_stop = lambda: state.get('stop_requested', False)

                leads = scraper.scrape()

                if not state.get('stop_requested'):
                    state['leads'] = leads
                    state['completed'] = True
                    state['status'] = 'completed'
                else:
                    state['status'] = 'cancelled'

            except Exception as e:
                print(f"❌ Erro Thread: {e}")
                state['error'] = str(e)
                state['status'] = 'error'
                state['completed'] = True
            finally:
                # GARBAGE COLLECTION FORÇADO
                # Garante que o Chrome Driver morreu
                try:
                    if 'scraper' in locals() and scraper.driver:
                        scraper.driver.quit()
                except: pass
                print(f"🏁 [ID: {self.session_id}] Busca finalizada/limpa.")

# --- ENDPOINTS ---

@app.route('/')
def home():
    return send_from_directory('webapp', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('webapp', path)

@app.route('/api/start-search', methods=['POST'])
def start_search():
    try:
        # 1. Health Check
        is_healthy, msg = check_system_health()
        if not is_healthy:
            return jsonify({'error': msg}), 503

        data = request.json
        user_id = data.get('user_id')
        
        if not user_id: return jsonify({'error': 'User ID missing'}), 400

        # 2. Limpa buscas antigas deste usuário (previne lixo)
        if user_id in active_searches:
            # Se estava rodando a muito tempo, mata.
            pass 

        active_searches[user_id] = {
            'status': 'initializing',
            'leads': [],
            'leads_found': 0,
            'completed': False,
            'stop_requested': False,
            'error': None
        }

        worker = SearchWorker(
            user_id, 
            data.get('nicho'), 
            data.get('cidade'), 
            int(data.get('max_leads', 10)),
            {
                'site': data.get('filter_site', 'todos'),
                'whats': data.get('filter_whats', 'todos')
            }
        )
        worker.start()

        return jsonify({'success': True, 'session_id': user_id, 'status': 'queued'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-status', methods=['GET'])
def search_status():
    session_id = request.args.get('session_id')
    
    # Se sessão não existe na memória (crashou ou reiniciou), avisa o frontend
    if not session_id or session_id not in active_searches:
        return jsonify({
            'status': 'error', 
            'error': 'Busca perdida (Servidor reiniciou ou ID inválido). Tente novamente.',
            'leads': [],
            'completed': True
        })
        
    state = active_searches[session_id]
    
    # Lógica de "Keep Alive" ou heartbeat poderia ser adicionada aqui
    
    return jsonify({
        'status': state.get('status'),
        'leads': state.get('leads', [])[-15:],
        'leads_found': state.get('leads_found', 0),
        'current': state.get('current', 'Aguardando...'),
        'progress': state.get('progress', 0),
        'completed': state.get('completed', False),
        'error': state.get('error')
    })

@app.route('/api/cancel-search', methods=['POST'])
def cancel_search():
    data = request.json or {}
    sid = data.get('user_id')
    if sid and sid in active_searches:
        active_searches[sid]['stop_requested'] = True
        return jsonify({'success': True})
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/health')
def health():
    mem = psutil.virtual_memory()
    return jsonify({
        'status': 'ok', 
        'ram_percent': mem.percent, 
        'active_threads': threading.active_count()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    # Threaded=True é essencial para Flask processar requests enquanto worka
    app.run(host='0.0.0.0', port=port, threaded=True)
