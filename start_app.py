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
    def __init__(self, session_id, nicho, cidade, max_leads):
        super().__init__()
        self.session_id = session_id
        self.nicho = nicho
        self.cidade = cidade
        self.max_leads = max_leads
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
                
                # Callback customizado para salvar e atualizar estado em tempo real
                def on_lead_found(lead):
                    # Salva no estado local para o frontend pegar
                    state['leads'].append(lead)
                    state['leads_found'] += 1
                    # Tenta salvar no Supabase
                    threading.Thread(target=save_lead_to_cloud, args=(lead,)).start()

                # Inicia Scraper
                scraper = GoogleMapsScraperDefinitivo(self.nicho, self.cidade)
                # Injetamos o callback na classe (vou ajustar o scraper depois para suportar melhor isso, 
                # mas por agora, o scraper salva no array dele e depois pegamos)
                
                # Executa
                leads = scraper.scrape()
                
                # Atualiza final
                state['leads'] = leads # Garante lista completa
                state['leads_found'] = len(leads)
                state['completed'] = True
                state['status'] = 'completed'
                state['progress'] = 100
                print(f"✅ [ID: {self.session_id}] Busca concluída: {len(leads)} leads")
                
            except Exception as e:
                print(f"❌ [ID: {self.session_id}] Erro: {e}")
                state['error'] = str(e)
                state['status'] = 'error'
                state['completed'] = True

# --- ENDPOINTS ---

@app.route('/')
def index():
    return send_from_directory('webapp', 'index.html')

@app.route('/api/start-search', methods=['POST'])
def start_search():
    data = request.json
    # Usa ID do usuário ou gera um temporário
    session_id = data.get('user_id') or str(uuid.uuid4())
    
    # Se já tem busca rodando para esse ID, verifica se terminou
    if session_id in active_searches:
        prev_search = active_searches[session_id]
        if not prev_search.get('completed', False) and prev_search.get('status') != 'error':
             return jsonify({
                 'success': True, 
                 'message': 'Recuperando busca existente',
                 'session_id': session_id,
                 'status': prev_search['status']
             })

    nicho = data.get('nicho', '').strip()
    cidade = data.get('cidade', '').strip()
    try:
        max_leads = int(data.get('max_leads', 50))
    except:
        max_leads = 50

    if not nicho or not cidade:
        return jsonify({'error': 'Nicho e cidade obrigatórios'}), 400

    # Inicializa estado
    active_searches[session_id] = {
        'nicho': nicho,
        'cidade': cidade,
        'status': 'initializing',
        'progress': 0,
        'leads_found': 0,
        'leads': [],
        'error': None,
        'completed': False,
        'created_at': datetime.now()
    }

    # Inicia Worker
    worker = SearchWorker(session_id, nicho, cidade, max_leads)
    worker.start()

    return jsonify({
        'success': True,
        'message': 'Na fila de processamento',
        'session_id': session_id
    })

@app.route('/api/search-status', methods=['GET'])
def get_status():
    # Frontend deve enviar user_id ou session_id na query string ?session_id=...
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in active_searches:
        return jsonify({'running': False, 'status': 'not_found', 'leads': []})
    
    state = active_searches[session_id]
    
    # Se status for queued, retorna running=True para o frontend não parar
    is_running = state['status'] in ['queued', 'running', 'initializing']
    
    return jsonify({
        'running': is_running,
        'completed': state['completed'],
        'status': state['status'], # queued, running, completed, error
        'progress': state['progress'],
        'leads_found': state['leads_found'],
        'leads': state['leads'],
        'error': state['error'],
        'nicho': state['nicho'],
        'cidade': state['cidade']
    })

@app.route('/api/cancel-search', methods=['POST'])
def cancel_search():
    # Placeholder simplificado
    return jsonify({'success': True})

@app.route('/api/reset-status', methods=['POST'])
def reset_status():
    # Limpa apenas buscas antigas (garbage collection manual)
    global active_searches
    active_searches = {}
    return jsonify({'success': True, 'message': 'Sistema resetado'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
