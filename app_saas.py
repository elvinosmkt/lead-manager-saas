"""
SERVIDOR SAAS - LEAD MANAGER PRO
- Autenticação de usuários
- Sistema de Créditos (5000 leads = R$ 500)
- Scraper Otimizado Integrado
"""
from flask import Flask, request, jsonify, send_from_directory, session, redirect
from flask_cors import CORS
import threading
import time
import os
import hashlib
import json
from datetime import datetime
from functools import wraps

# Importa módulos locais
from database import init_db, get_db
from scraper_otimizado import GoogleMapsScraperOtimizado
from config import CONFIG

# Inicializa DB
if not os.path.exists("lead_manager.db"):
    init_db()

app = Flask(__name__, static_folder='webapp', static_url_path='')
app.secret_key = 'supersearch_secret_key_change_in_production'
CORS(app)

# Estado global das buscas (mapeado por user_id)
# Formato: { user_id: { 'running': bool, ... } }
active_searches = {}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado', 'redirect': '/login.html'}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Dados incompletos'}), 400
        
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ? AND password_hash = ?', 
                      (email, password_hash)).fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_plan'] = user['plan_type']
        return jsonify({
            'success': True, 
            'user': {
                'name': user['name'],
                'email': user['email'],
                'credits': user['credits']
            }
        })
    else:
        return jsonify({'error': 'Email ou senha inválidos'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/user-info', methods=['GET'])
@login_required
def user_info():
    user_id = session['user_id']
    conn = get_db()
    user = conn.execute('SELECT name, email, credits, plan_type FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'name': user['name'],
            'email': user['email'],
            'credits': user['credits'],
            'plan': user['plan_type']
        })
    return jsonify({'error': 'Usuário não encontrado'}), 404

# --- ROTAS DE BUSCA E CRÉDITOS ---

def process_search(user_id, nicho, cidade, max_leads):
    """Executa busca em background e desconta créditos"""
    global active_searches
    
    state = active_searches[user_id]
    credits_used = 0
    
    def on_progress(data):
        state['progress'] = data['progress']
        state['total'] = data['total']
        state['processados'] = data['current']
        
        # Se encontrou um lead novo
        if data.get('latest_lead'):
            lead = data['latest_lead']
            
            # Verifica se já não está na lista (segurança extra)
            is_dup = any(l['nome'] == lead['nome'] for l in state['leads'])
            if not is_dup:
                state['leads'].append(lead)
                state['leads_found'] += 1
                
                # ATUALIZAÇÃO: Desconta crédito em tempo real ou no final?
                # Vamos contar aqui para debitar do banco no final ou em lotes
                # Por simplicidade e performance, descontamos do objeto state agora
                # e commitamos no banco no final da execução
    
    try:
        print(f"🚀 [User {user_id}] Iniciando busca: {nicho} em {cidade}")
        
        # Configura scraper
        CONFIG['MAX_BUSINESSES'] = max_leads
        CONFIG['HEADLESS'] = True
        
        scraper = GoogleMapsScraperOtimizado(nicho, cidade, callback=on_progress)
        scraper.scrape()
        
        # Finalização
        leads_encontrados = len(scraper.businesses)
        if leads_encontrados > 0:
            # Salva leads encontrados
            save_leads_to_db(user_id, scraper.businesses)

            # Desconta créditos do banco
            conn = get_db()
            
            # Verifica saldo atual novamente
            user = conn.execute('SELECT credits FROM users WHERE id = ?', (user_id,)).fetchone()
            current_credits = user['credits']
            
            # Calcula custo real (garante que não fica negativo)
            cost = min(leads_encontrados, current_credits)
            new_credits = current_credits - cost
            
            # Atualiza saldo e histórico
            conn.execute('UPDATE users SET credits = ? WHERE id = ?', (new_credits, user_id))
            conn.execute('''
                INSERT INTO usage_history (user_id, action, amount, details)
                VALUES (?, ?, ?, ?)
            ''', (user_id, 'search_debit', cost, f"Busca: {nicho} em {cidade}"))
            
            conn.commit()
            conn.close()
            print(f"💰 [User {user_id}] Debitados {cost} créditos. Saldo restante: {new_credits}")
        
        state['completed'] = True
        state['credits_spent'] = leads_encontrados # Assumindo 1 crédito por lead
        
    except Exception as e:
        state['error'] = str(e)
        print(f"❌ [User {user_id}] Erro: {e}")
    finally:
        state['running'] = False

@app.route('/api/start-search', methods=['POST'])
@login_required
def start_search():
    user_id = session['user_id']
    data = request.json
    nicho = data.get('nicho')
    cidade = data.get('cidade')
    max_leads = int(data.get('max_leads', 10))
    
    if not nicho or not cidade:
        return jsonify({'error': 'Campos obrigatórios'}), 400

    # Verifica créditos
    conn = get_db()
    user = conn.execute('SELECT credits FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user['credits'] <= 0:
        return jsonify({'error': 'Saldo insuficiente. Recarregue seus créditos.'}), 403
        
    # Limita busca ao saldo disponível
    max_possible = min(max_leads, user['credits'])
    
    # Inicia estado
    active_searches[user_id] = {
        'running': True,
        'completed': False,
        'progress': 0,
        'leads': [],
        'leads_found': 0,
        'error': None,
        'processados': 0,
        'total': 0,
        'max_leads': max_possible
    }
    
    # Thread segura
    thread = threading.Thread(
        target=process_search,
        args=(user_id, nicho, cidade, max_possible)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True, 
        'message': 'Busca iniciada',
        'adjusted_limit': max_possible
    })

@app.route('/api/search-status', methods=['GET'])
@login_required
def search_status():
    user_id = session['user_id']
    state = active_searches.get(user_id)
    
    if not state:
        return jsonify({'running': False, 'completed': False})
    
    return jsonify(state)

# --- ROTAS DE ARQUIVOS ESTÁTICOS ---

@app.route('/')
def index():
    # Check if user is logged in
    if 'user_id' in session:
        return redirect('/dashboard')
    # Serve Landing Page
    return send_from_directory('webapp', 'index.html')

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect('/dashboard')
    return send_from_directory('webapp', 'login.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join('webapp', path)):
        return send_from_directory('webapp', path)
    
    # Fallbacks
    if path == 'dashboard': return send_from_directory('webapp', 'app.html')
    if path == 'login': return send_from_directory('webapp', 'login.html')
    
    return send_from_directory('webapp', 'index.html')


def save_leads_to_db(user_id, leads):
    if not leads: return
    conn = get_db()
    for l in leads:
        try:
            # Verifica duplicidade
            exists = conn.execute(
                'SELECT id FROM saved_leads WHERE user_id = ? AND name = ?', 
                (user_id, l.get('nome'))
            ).fetchone()
            
            if not exists:
                conn.execute('''
                    INSERT INTO saved_leads 
                    (user_id, name, phone, whatsapp, website, nicho, cidade, address, rating, reviews_count, google_maps_link)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, 
                    l.get('nome'), 
                    l.get('telefone'), 
                    l.get('whatsapp'), 
                    l.get('website'), 
                    l.get('nicho'), 
                    l.get('cidade'),
                    l.get('endereco'),
                    l.get('avaliacao'),
                    l.get('num_avaliacoes'),
                    l.get('google_maps_link')
                ))
        except Exception as e:
            print(f"Erro ao salvar lead {l.get('nome')}: {e}")
    conn.commit()
    conn.close()

@app.route('/api/leads', methods=['GET'])
@login_required
def get_leads():
    user_id = session['user_id']
    conn = get_db()
    leads = conn.execute('''
        SELECT 
            name as nome, 
            phone as telefone, 
            whatsapp, 
            website, 
            nicho, 
            cidade, 
            address as endereco, 
            rating as avaliacao, 
            reviews_count as num_avaliacoes, 
            google_maps_link 
        FROM saved_leads WHERE user_id = ? ORDER BY timestamp DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(l) for l in leads])

@app.route('/api/save-leads', methods=['POST'])
@login_required
def api_save_leads():
    try:
        leads = request.json.get('leads', [])
        save_leads_to_db(session['user_id'], leads)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Cria os arquivos HTML se não existirem
    if not os.path.exists('webapp/login.html'):
        print("⚠️ Crie os arquivos HTML para o sistema SaaS!")
        
    print("🚀 PRO LEAD MANAGER SaaS - Rodando na porta 5001")
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
