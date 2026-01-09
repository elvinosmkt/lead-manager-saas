"""
Backend Flask para integração do scraper com o webapp
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import json
from scraper_melhorado import GoogleMapsScraperMelhorado
from config import CONFIG

app = Flask(__name__)
CORS(app)

# Estado global da busca
search_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current': '',
    'leads_found': 0,
    'error': None,
    'completed': False,
    'leads': []
}

def run_scraper(nicho, cidade, max_leads):
    """Executa o scraper em background"""
    global search_status
    
    try:
        search_status['running'] = True
        search_status['progress'] = 0
        search_status['error'] = None
        search_status['completed'] = False
        search_status['leads'] = []
        
        # Atualiza configuração
        CONFIG['MAX_BUSINESSES'] = max_leads
        
        # Cria e executa scraper
        scraper = GoogleMapsScraperMelhorado(nicho, cidade)
        
        # Modifica scraper para reportar progresso
        original_collect = scraper._collect_businesses
        
        def collect_with_progress():
            try:
                # Chama método original
                original_collect()
                
                # Atualiza status
                search_status['leads'] = scraper.businesses
                search_status['leads_found'] = len(scraper.businesses)
                search_status['completed'] = True
            except Exception as e:
                search_status['error'] = str(e)
            finally:
                search_status['running'] = False
        
        scraper._collect_businesses = collect_with_progress
        
        # Inicia busca
        scraper.scrape()
        
    except Exception as e:
        search_status['error'] = str(e)
        search_status['running'] = False


@app.route('/api/start-search', methods=['POST'])
def start_search():
    """Inicia uma nova busca"""
    global search_status
    
    if search_status['running']:
        return jsonify({'error': 'Já existe uma busca em andamento'}), 400
    
    data = request.json
    nicho = data.get('nicho', '').strip()
    cidade = data.get('cidade', '').strip()
    max_leads = int(data.get('max_leads', 50))
    
    if not nicho or not cidade:
        return jsonify({'error': 'Nicho e cidade são obrigatórios'}), 400
    
    # Inicia scraper em thread separada
    thread = threading.Thread(target=run_scraper, args=(nicho, cidade, max_leads))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Busca iniciada com sucesso',
        'nicho': nicho,
        'cidade': cidade,
        'max_leads': max_leads
    })


@app.route('/api/search-status', methods=['GET'])
def get_search_status():
    """Retorna o status atual da busca"""
    return jsonify({
        'running': search_status['running'],
        'completed': search_status['completed'],
        'leads_found': search_status['leads_found'],
        'error': search_status['error'],
        'leads': search_status['leads'] if search_status['completed'] else []
    })


@app.route('/api/cancel-search', methods=['POST'])
def cancel_search():
    """Cancela a busca atual"""
    global search_status
    search_status['running'] = False
    return jsonify({'message': 'Busca cancelada'})


if __name__ == '__main__':
    print("🚀 Servidor iniciado em http://localhost:5000")
    print("📊 Aplicativo web: http://localhost:5000/static/index.html")
    app.run(debug=True, port=5000)
