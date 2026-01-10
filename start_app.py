"""
Servidor completo com API e servindo webapp
Execute: python3 start_app.py
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import time
import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_definitivo import GoogleMapsScraperDefinitivo
from config import CONFIG

app = Flask(__name__, static_folder='webapp', static_url_path='')
CORS(app)

# Estado global da busca
search_state = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current_business': '',
    'leads_found': 0,
    'completed': False,
    'error': None,
    'leads': [],
    'nicho': '',
    'cidade': ''
}

def run_scraper_background(nicho, cidade, max_leads):
    """Executa o scraper em background thread"""
    global search_state
    
    try:
        search_state['running'] = True
        search_state['completed'] = False
        search_state['error'] = None
        search_state['leads'] = []
        search_state['progress'] = 0
        search_state['leads_found'] = 0
        search_state['nicho'] = nicho
        search_state['cidade'] = cidade
        
        print(f"\n🚀 Iniciando busca: {nicho} em {cidade}")
        print(f"📊 Máximo de leads: {max_leads}\n")
        
        # Atualiza configuração
        CONFIG['MAX_BUSINESSES'] = max_leads
        
        # Cria scraper DEFINITIVO (ultra-robusto)
        scraper = GoogleMapsScraperDefinitivo(nicho, cidade)
        
        # Executa
        scraper.scrape()
        
        # Atualiza estado
        search_state['leads'] = scraper.businesses
        search_state['leads_found'] = len(scraper.businesses)
        search_state['completed'] = True
        search_state['progress'] = 100
        
        print(f"\n✅ Busca concluída! {len(scraper.businesses)} leads encontrados\n")
        
    except Exception as e:
        search_state['error'] = str(e)
        print(f"\n❌ Erro na busca: {str(e)}\n")
    finally:
        search_state['running'] = False


@app.route('/')
def index():
    """Serve o aplicativo web"""
    return send_from_directory('webapp', 'index.html')


@app.route('/api/start-search', methods=['POST'])
def start_search():
    """Inicia uma nova busca"""
    global search_state
    
    # Se já estiver rodando, reinicia estado se forçar ou retorna erro
    if search_state['running']:
        # Opcional: permitir cancelar busca anterior ou esperar
        # Por enquanto, mantemos o check simples:
        return jsonify({'error': 'Já existe uma busca em andamento'}), 400
    
    try:
        data = request.json
        print(f"📩 Recebido pedido de busca: {data}")
        
        nicho = data.get('nicho', '').strip()
        cidade = data.get('cidade', '').strip()
        
        # Converte max_leads com segurança
        try:
            max_leads = int(data.get('max_leads', 50))
        except:
            max_leads = 50
            
        # Novos filtros (opcionais por enquanto)
        filter_site = data.get('filter_site', 'todos')
        filter_whats = data.get('filter_whats', 'todos')
        
        if not nicho or not cidade:
            print("❌ Erro: Nicho ou cidade vazios")
            return jsonify({'error': 'Nicho e cidade são obrigatórios'}), 400
            
        # Configura filtros globais se necessário (ainda a implementar no scraper, mas aceita na API)
        CONFIG['FILTERS'] = {
            'site': filter_site,
            'whatsapp': filter_whats
        }

        # Inicia thread
        thread = threading.Thread(
            target=run_scraper_background,
            args=(nicho, cidade, max_leads)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Busca iniciada: {nicho} em {cidade}',
            'max_leads': max_leads
        })
    except Exception as e:
        print(f"❌ Erro interno na API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-status', methods=['POST'])
def reset_status():
    """Força o reset do estado da busca"""
    global search_state
    search_state['running'] = False
    search_state['completed'] = False
    search_state['error'] = None
    search_state['progress'] = 0
    return jsonify({'success': True, 'message': 'Status resetado com sucesso'})


@app.route('/api/search-status', methods=['GET'])
def get_status():
    """Retorna o status atual da busca"""
    return jsonify({
        'running': search_state['running'],
        'completed': search_state['completed'],
        'progress': search_state['progress'],
        'leads_found': search_state['leads_found'],
        'leads': search_state['leads'],  # Adicionado para frontend atualizar em tempo real
        'current': search_state['current_business'],
        'error': search_state['error'],
        'nicho': search_state['nicho'],
        'cidade': search_state['cidade']
    })


@app.route('/api/get-leads', methods=['GET'])
def get_leads():
    """Retorna os leads encontrados"""
    if not search_state['completed']:
        return jsonify({'error': 'Busca ainda não completada'}), 400
    
    return jsonify({
        'success': True,
        'leads': search_state['leads'],
        'count': len(search_state['leads'])
    })


@app.route('/api/cancel-search', methods=['POST'])
def cancel_search():
    """Cancela a busca atual"""
    global search_state
    search_state['running'] = False
    return jsonify({'success': True, 'message': 'Busca cancelada'})


if __name__ == '__main__':
    # Pega porta do ambiente (Railway) ou usa 5001 local
    port = int(os.environ.get('PORT', 5001))
    
    print("\n" + "="*60)
    print("🚀 LEAD MANAGER - SERVIDOR INICIADO")
    print("="*60)
    print(f"\n📊 Servidor rodando na porta: {port}")
    print(f"🔌 API disponível em: /api/")
    print(f"⏹️  Pressione Ctrl+C para parar o servidor\n")
    print("="*60 + "\n")
    
    # Inicia o servidor
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
