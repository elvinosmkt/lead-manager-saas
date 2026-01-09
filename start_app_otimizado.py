"""
Servidor otimizado com API e webapp
- Usa scraper headless (invisível)
- Atualização em tempo real via WebSocket/SSE
- Filtra apenas leads SEM SITE

Execute: python3 start_app_otimizado.py
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_otimizado import GoogleMapsScraperOtimizado
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
    'cidade': '',
    'processados': 0,
    'rejeitados_com_site': 0
}


def progress_callback(data):
    """Callback chamado pelo scraper para atualizar estado em tempo real"""
    global search_state
    
    search_state['progress'] = data.get('progress', 0)
    search_state['processados'] = data.get('current', 0)
    search_state['total'] = data.get('total', 0)
    search_state['leads_found'] = data.get('leads_found', 0)
    
    # Adiciona novo lead em tempo real
    if data.get('latest_lead'):
        lead = data['latest_lead']
        # Verifica se já não está na lista (por segurança)
        if not any(l.get('nome') == lead.get('nome') for l in search_state['leads']):
            search_state['leads'].append(lead)
        search_state['current_business'] = lead.get('nome', '')


def run_scraper_background(nicho, cidade, max_leads):
    """Executa o scraper otimizado em background"""
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
        search_state['processados'] = 0
        search_state['rejeitados_com_site'] = 0
        
        print(f"\n🚀 Iniciando busca OTIMIZADA")
        print(f"🎯 Nicho: {nicho}")
        print(f"📍 Cidade: {cidade}")
        print(f"📊 Meta: {max_leads} leads SEM SITE")
        print(f"👻 Modo: HEADLESS (invisível)\n")
        
        # Atualiza configuração
        CONFIG['MAX_BUSINESSES'] = max_leads
        
        # Cria scraper OTIMIZADO com callback
        scraper = GoogleMapsScraperOtimizado(
            nicho, 
            cidade,
            callback=progress_callback
        )
        
        # Executa
        scraper.scrape()
        
        # Atualiza estado final
        search_state['leads'] = scraper.businesses
        search_state['leads_found'] = len(scraper.businesses)
        search_state['completed'] = True
        search_state['progress'] = 100
        
        print(f"\n✅ Busca concluída!")
        print(f"🎯 Leads SEM SITE encontrados: {len(scraper.businesses)}")
        print(f"📊 Total processado: {search_state['processados']}\n")
        
    except Exception as e:
        search_state['error'] = str(e)
        print(f"\n❌ Erro na busca: {str(e)}\n")
        import traceback
        traceback.print_exc()
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
    
    if search_state['running']:
        return jsonify({'error': 'Já existe uma busca em andamento'}), 400
    
    data = request.json
    nicho = data.get('nicho', '').strip()
    cidade = data.get('cidade', '').strip()
    max_leads = int(data.get('max_leads', 50))
    
    if not nicho or not cidade:
        return jsonify({'error': 'Nicho e cidade são obrigatórios'}), 400
    
    # Limpa estado anterior
    search_state['leads'] = []
    search_state['progress'] = 0
    search_state['leads_found'] = 0
    search_state['processados'] = 0
    
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
        'max_leads': max_leads,
        'mode': 'headless'
    })


@app.route('/api/search-status', methods=['GET'])
def get_status():
    """Retorna o status atual da busca (polling para tempo real)"""
    return jsonify({
        'running': search_state['running'],
        'completed': search_state['completed'],
        'progress': search_state['progress'],
        'leads_found': search_state['leads_found'],
        'current': search_state['current_business'],
        'error': search_state['error'],
        'nicho': search_state['nicho'],
        'cidade': search_state['cidade'],
        'processados': search_state['processados'],
        'total': search_state['total']
    })


@app.route('/api/get-leads', methods=['GET'])
def get_leads():
    """Retorna os leads encontrados (atualizado em tempo real)"""
    # Retorna mesmo se não completado (para tempo real)
    return jsonify({
        'success': True,
        'leads': search_state['leads'],
        'count': len(search_state['leads']),
        'running': search_state['running'],
        'completed': search_state['completed']
    })


@app.route('/api/cancel-search', methods=['POST'])
def cancel_search():
    """Cancela a busca atual"""
    global search_state
    search_state['running'] = False
    return jsonify({'success': True, 'message': 'Busca cancelada'})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 LEAD MANAGER OTIMIZADO - SERVIDOR INICIADO")
    print("="*60)
    print(f"\n📊 Aplicativo Web: http://localhost:5001")
    print(f"🔌 API disponível em: http://localhost:5001/api/")
    print(f"\n✨ NOVIDADES:")
    print(f"   👻 Modo headless (sem abrir janela)")
    print(f"   ⚡ Atualização em tempo real")
    print(f"   🎯 Filtra APENAS leads sem site")
    print(f"   📊 Validação aprimorada")
    print(f"\n💡 Acesse o navegador e comece a buscar leads!")
    print(f"⏹️  Pressione Ctrl+C para parar o servidor\n")
    print("="*60 + "\n")
    
    # NÃO abre navegador automaticamente (já está aberto)
    
    # Inicia o servidor
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
