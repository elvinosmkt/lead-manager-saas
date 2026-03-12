
"""
Servidor Multi-usuário com Fila, Memory Warning e Garbage Collection
"""
import os
import psutil  # Para monitorar memória
import threading
import time
import sys
import uuid
import jwt
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from queue import Queue
from datetime import datetime, timedelta

# Path Setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_definitivo import GoogleMapsScraperDefinitivo
from config import CONFIG
from db_config import save_lead_to_cloud, check_user_credits, deduct_user_credits, supabase
from payment_service import create_pix_payment

app = Flask(__name__, static_folder='webapp', static_url_path='')
CORS(app, origins=[
    "https://leads.blendagency.com.br",
    "https://leadmanager-lp.vercel.app",
], supports_credentials=True)

# --- TABELA DE PREÇOS SERVER-SIDE (Fonte de verdade) ---
PRICING = {
    'starter': {'mensal': 199, 'trimestral': 299},
    'pro':     {'mensal': 299, 'trimestral': 449},
    'elite':   {'mensal': 459, 'trimestral': 689},
}
UPSELL_PRICE = 149  # Vibe Coding add-on

# --- CONFIGURAÇÃO DE SEGURANÇA E RECURSOS ---
MAX_CONCURRENT_SEARCHES = 1  # Segurança máxima para plano Free/Hobby (evita OOM)
MAX_RAM_PERCENT = 85.0       # Se passar disso, rejeita novas buscas
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
WEBHOOK_TOKEN = os.environ.get("ASAAS_WEBHOOK_TOKEN", "")

semaphore = threading.Semaphore(MAX_CONCURRENT_SEARCHES)
active_searches = {}

def get_server_price(plan, billing_cycle, upsell=False):
    """Retorna o preço REAL do plano. Nunca confiar no frontend."""
    plan_prices = PRICING.get(plan)
    if not plan_prices:
        return None
    price = plan_prices.get(billing_cycle)
    if price is None:
        return None
    if upsell:
        price += UPSELL_PRICE
    return price

def verify_supabase_token(f):
    """Decorator que verifica JWT do Supabase no header Authorization."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token de autenticação ausente'}), 401
        
        token = auth_header.split(' ', 1)[1]
        try:
            if SUPABASE_JWT_SECRET:
                payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=['HS256'], audience='authenticated')
                request.user_id = payload.get('sub')
                request.user_email = payload.get('email')
            else:
                # Fallback: verifica via Supabase API (mais lento)
                from supabase import create_client
                anon_url = os.environ.get('SUPABASE_URL', '')
                anon_key = os.environ.get('SUPABASE_ANON_KEY', '')
                if anon_url and anon_key:
                    temp_client = create_client(anon_url, anon_key)
                    user_resp = temp_client.auth.get_user(token)
                    if user_resp and user_resp.user:
                        request.user_id = user_resp.user.id
                        request.user_email = user_resp.user.email
                    else:
                        return jsonify({'error': 'Token inválido'}), 401
                else:
                    # Se nenhum secret configurado, aceita o user_id do body (legado)
                    request.user_id = None
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado. Faça login novamente.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(*args, **kwargs)
    return decorated

def check_system_health():
    """Verifica se o servidor tem recursos para aceitar nova busca"""
    mem = psutil.virtual_memory()
    if mem.percent > MAX_RAM_PERCENT:
        return False, f"Servidor sobrecarregado (RAM: {mem.percent}%). Tente em 1 min."
    return True, "OK"

class SearchWorker(threading.Thread):
    def __init__(self, session_id, nicho, cidade, max_leads, filters=None):
        super().__init__()
        self.session_id = session_id
        self.nicho = nicho
        self.cidade = cidade
        self.max_leads = max_leads
        self.filters = filters or {}
        self.daemon = True

    def run(self):
        global active_searches
        state = active_searches.get(self.session_id)
        if not state: return

        state['status'] = 'queued'
        print(f"⏳ [ID: {self.session_id[:8]}...] Na fila...")

        with semaphore:
            # Double check health antes de abrir o Chrome
            is_healthy, msg = check_system_health()
            if not is_healthy:
                print(f"❌ Abortando busca por falta de memória: {msg}")
                state['error'] = "Servidor ocupado (Memória Cheia). Tente novamente."
                state['status'] = 'error'
                state['completed'] = True
                state['running'] = False
                return

            scraper = None
            try:
                if state.get('stop_requested'):
                    state['running'] = False
                    return

                state['status'] = 'running'
                state['running'] = True
                print(f"🚀 [ID: {self.session_id[:8]}...] Iniciando Chrome...")

                # NÃO muta CONFIG global — passa max_leads direto ao scraper
                def on_lead_found(lead):
                    if state.get('stop_requested'): return
                    state['leads'].append(lead)
                    state['leads_found'] += 1
                    state['current'] = lead.get('nome', 'Processando...')[:40]
                    state['progress'] = min(100, int((state['leads_found'] / self.max_leads) * 100))
                    
                    # Salva no Supabase (Thread separada para não bloquear)
                    threading.Thread(
                        target=save_lead_to_cloud, 
                        args=(lead, self.session_id),
                        daemon=True
                    ).start()

                    # Deduz Crédito
                    deduct_user_credits(self.session_id, 1)
                    has_now, _ = check_user_credits(self.session_id)
                    
                    if not has_now:
                        print("⚠️ Créditos acabaram. Parando busca.")
                        state['stop_requested'] = True
                        state['error'] = 'Limite de créditos atingido.'

                scraper = GoogleMapsScraperDefinitivo(
                    self.nicho, self.cidade, self.max_leads, self.filters
                )
                scraper.on_lead_found_callback = on_lead_found
                scraper.check_stop = lambda: state.get('stop_requested', False)

                leads = scraper.scrape()

                if not state.get('stop_requested'):
                    state['leads'] = leads
                    state['completed'] = True
                    state['status'] = 'completed'
                else:
                    state['completed'] = True
                    state['status'] = 'cancelled'

            except Exception as e:
                print(f"❌ Erro Thread: {e}")
                import traceback
                traceback.print_exc()
                state['error'] = str(e)
                state['status'] = 'error'
                state['completed'] = True
            finally:
                state['running'] = False
                # Garante que o Chrome Driver morreu
                try:
                    if scraper and scraper.driver:
                        scraper.driver.quit()
                except: pass
                print(f"🏁 [ID: {self.session_id[:8]}...] Busca finalizada/limpa.")

# --- ENDPOINTS ---

@app.route('/')
def home():
    return send_from_directory('webapp', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('webapp', path)

@app.route('/api/start-search', methods=['POST'])
@verify_supabase_token
def start_search():
    try:
        # 1. Health Check
        is_healthy, msg = check_system_health()
        if not is_healthy:
            return jsonify({'error': msg}), 503

        data = request.json
        # Usa user_id do token JWT (seguro), com fallback para body (legado)
        user_id = getattr(request, 'user_id', None) or data.get('user_id')
        
        if not user_id: return jsonify({'error': 'User ID missing'}), 400

        # 2. Limpa buscas anteriores deste usuário
        old = active_searches.get(user_id)
        if old and old.get('running'):
            old['stop_requested'] = True
            print(f"⚠️ Parando busca anterior do user {user_id[:8]}...")

        # 3. VERIFICA CRÉDITOS
        has_credits, remaining = check_user_credits(user_id)
        if not has_credits:
             return jsonify({
                 'error': 'CRÉDITOS ESGOTADOS', 
                 'code': 'no_credits',
                 'message': 'Você atingiu seu limite mensal. Faça upgrade para continuar.'
             }), 402
             
        # Limita a busca ao que resta de créditos
        max_requested = int(data.get('max_leads', 10))
        if max_requested > remaining:
            max_requested = remaining
            print(f"⚠️ Limitando busca a {remaining} créditos restantes.")

        active_searches[user_id] = {
            'status': 'initializing',
            'running': True,
            'leads': [],
            'leads_found': 0,
            'completed': False,
            'stop_requested': False,
            'error': None,
            'progress': 0,
            'current': 'Iniciando motor de busca...'
        }

        worker = SearchWorker(
            user_id, 
            data.get('nicho'), 
            data.get('cidade'), 
            max_requested,
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
        'running': state.get('running', False),
        'leads': state.get('leads', [])[-50:],  # Últimos 50 para o frontend mergear
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

@app.route('/api/create-pix', methods=['POST'])
@verify_supabase_token
def api_create_pix():
    try:
        data = request.json
        plan = data.get('plan', 'pro')
        billing_cycle = data.get('billing_cycle', 'mensal')
        upsell = data.get('upsell', False)
        user_id = getattr(request, 'user_id', None) or data.get('user_id')
        
        # PREÇO CALCULADO NO SERVIDOR — ignora qualquer 'price' do frontend
        server_price = get_server_price(plan, billing_cycle, upsell)
        if server_price is None:
            return jsonify({'error': f'Plano "{plan}" ou ciclo "{billing_cycle}" inválido'}), 400
        
        print(f"💰 [SECURITY] Preço server-side: R${server_price} (plano={plan}, ciclo={billing_cycle}, upsell={upsell})")
        
        description = f"Assinatura LeadManager - Plano {plan} ({billing_cycle})"
        external_ref = f"{user_id}_{int(time.time())}"
        
        result = create_pix_payment(
            data, 
            server_price,  # Preço do servidor, NÃO do frontend
            description, 
            external_ref
        )
        
        if result:
            try:
                supabase.table("subscriptions").insert({
                    "user_id": user_id,
                    "plan": plan,
                    "billing_cycle": billing_cycle,
                    "price": server_price,  # Preço real
                    "status": "pending_payment",
                    "provider": "asaas",
                    "provider_subscription_id": result['payment_id']
                }).execute()
            except Exception as dberr:
                print(f"⚠️ Erro ao salvar subs pendente: {dberr}")

            return jsonify({'success': True, 'payment': result})
            
        return jsonify({'error': 'Erro ao gerar PIX'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/payment-status', methods=['GET'])
def payment_status():
    """Verifica o status de um pagamento no Asaas"""
    try:
        payment_id = request.args.get('payment_id')
        if not payment_id:
            return jsonify({'error': 'payment_id obrigatório'}), 400
        
        import requests
        ASAAS_API_KEY = os.environ.get("ASAAS_API_KEY", "")
        if not ASAAS_API_KEY:
            return jsonify({'error': 'Configuração de pagamento ausente'}), 500
        
        response = requests.get(
            f"https://api.asaas.com/v3/payments/{payment_id}",
            headers={
                "Content-Type": "application/json",
                "access_token": ASAAS_API_KEY
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'status': data.get('status'),
                'value': data.get('value'),
                'paymentDate': data.get('paymentDate')
            })
        else:
            return jsonify({'error': 'Pagamento não encontrado'}), 404
            
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-card-subscription', methods=['POST'])
@verify_supabase_token
def api_create_card_subscription():
    """Cria assinatura recorrente com cartão de crédito no Asaas"""
    try:
        data = request.json
        plan = data.get('plan', 'pro')
        billing_cycle = data.get('billing_cycle', 'mensal')
        upsell = data.get('upsell', False)
        user_id = getattr(request, 'user_id', None) or data.get('user_id')
        
        # PREÇO CALCULADO NO SERVIDOR — ignora 'price' do frontend
        server_price = get_server_price(plan, billing_cycle, upsell)
        if server_price is None:
            return jsonify({'error': f'Plano "{plan}" ou ciclo "{billing_cycle}" inválido'}), 400
        
        print(f"💰 [SECURITY] Cartão server-side: R${server_price} (plano={plan}, ciclo={billing_cycle})")
        
        import requests
        ASAAS_API_KEY = os.environ.get("ASAAS_API_KEY", "")
        if not ASAAS_API_KEY:
            return jsonify({'error': 'Configuração de pagamento ausente'}), 500
        ASAAS_API_URL = "https://api.asaas.com/v3"
        
        headers = {
            "Content-Type": "application/json",
            "access_token": ASAAS_API_KEY
        }
        
        # 1. Buscar ou criar cliente
        cpf = data.get('cpf', '').replace('.', '').replace('-', '')
        email = data.get('email')
        
        cust_res = requests.get(f"{ASAAS_API_URL}/customers?email={email}", headers=headers)
        cust_data = cust_res.json()
        
        customer_id = None
        if cust_data.get('data') and len(cust_data['data']) > 0:
            customer_id = cust_data['data'][0]['id']
        else:
            new_cust = requests.post(
                f"{ASAAS_API_URL}/customers",
                headers=headers,
                json={
                    "name": data.get('name'),
                    "cpfCnpj": cpf,
                    "email": email
                }
            )
            new_cust_data = new_cust.json()
            if 'id' in new_cust_data:
                customer_id = new_cust_data['id']
            else:
                return jsonify({'error': f"Erro ao criar cliente: {new_cust_data}"}), 400
        
        if not customer_id:
            return jsonify({'error': 'Não foi possível criar/encontrar cliente'}), 400
        
        # 2. Determinar ciclo de cobrança
        cycle_map = {
            'mensal': 'MONTHLY',
            'trimestral': 'QUARTERLY',
            'anual': 'YEARLY'
        }
        asaas_cycle = cycle_map.get(billing_cycle, 'MONTHLY')
        
        # 3. Criar assinatura com cartão — usa server_price
        card_data = data.get('card', {})
        
        subscription_payload = {
            "customer": customer_id,
            "billingType": "CREDIT_CARD",
            "value": float(server_price),  # PREÇO DO SERVIDOR
            "nextDueDate": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "cycle": asaas_cycle,
            "description": f"Assinatura LeadManager - Plano {plan} ({billing_cycle})",
            "creditCard": {
                "holderName": card_data.get('holderName'),
                "number": card_data.get('number', '').replace(' ', ''),
                "expiryMonth": card_data.get('expiryMonth'),
                "expiryYear": card_data.get('expiryYear'),
                "ccv": card_data.get('ccv')
            },
            "creditCardHolderInfo": {
                "name": data.get('name'),
                "email": email,
                "cpfCnpj": cpf,
                "postalCode": data.get('postalCode', '00000000'),
                "addressNumber": data.get('addressNumber', '0'),
                "phone": data.get('phone', '').replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
            }
        }
        
        print(f"📧 Criando assinatura para: {email}")
        
        sub_res = requests.post(
            f"{ASAAS_API_URL}/subscriptions",
            headers=headers,
            json=subscription_payload
        )
        
        sub_data = sub_res.json()
        
        if 'id' in sub_data:
            print(f"✅ Assinatura criada: {sub_data['id']}")
            
            # Salva no Supabase com preço real
            try:
                supabase.table("subscriptions").insert({
                    "user_id": user_id,
                    "plan": plan,
                    "billing_cycle": billing_cycle,
                    "price": server_price,  # Preço real do servidor
                    "status": "active",
                    "provider": "asaas",
                    "provider_subscription_id": sub_data['id']
                }).execute()
            except Exception as dberr:
                print(f"⚠️ Erro ao salvar subscription: {dberr}")
            
            return jsonify({
                'success': True,
                'subscription_id': sub_data['id'],
                'status': sub_data.get('status'),
                'next_due_date': sub_data.get('nextDueDate')
            })
        else:
            print(f"❌ Erro Asaas: {sub_data}")
            error_msg = sub_data.get('errors', [{}])[0].get('description', 'Erro ao criar assinatura')
            return jsonify({'error': error_msg, 'details': sub_data}), 400
            
    except Exception as e:
        print(f"❌ Erro create-card-subscription: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/webhook/asaas', methods=['POST'])
def webhook_asaas():
    try:
        # VERIFICAÇÃO DE SEGURANÇA DO WEBHOOK
        # Opção 1: Token no query string (configurável no painel Asaas)
        webhook_token = request.args.get('token', '')
        if WEBHOOK_TOKEN and webhook_token != WEBHOOK_TOKEN:
            print(f"⚠️ [SECURITY] Webhook rejeitado: token inválido")
            return jsonify({'error': 'Unauthorized'}), 403
        
        event = request.json
        print(f"🔔 [Webhook Asaas] Evento: {event.get('event')}")
        
        evt = event.get('event')
        payment_id = event.get('payment', {}).get('id')
        
        if evt == 'PAYMENT_RECEIVED' or evt == 'PAYMENT_CONFIRMED':
            # Busca assinatura pelo ID do pagamento
            res = supabase.table("subscriptions").select("*").eq("provider_subscription_id", payment_id).execute()
            sub = res.data[0] if res.data else None
            
            if sub:
                # Ativa assinatura
                supabase.table("subscriptions").update({
                    "status": "active",
                    "started_at": datetime.now().isoformat()
                }).eq("id", sub['id']).execute()
                
                # Atualiza usuário (Plano e Créditos)
                plan = sub['plan']
                credits_map = {'starter': 500, 'pro': 1500, 'elite': 5000}
                new_credits = credits_map.get(plan, 500)
                
                # Se for trimestral, multiplica por 3
                if sub.get('billing_cycle') == 'trimestral':
                    new_credits *= 3
                
                supabase.table("users").update({
                    "plan": plan,
                    "credits_limit": new_credits,
                    "credits_used": 0
                }).eq("id", sub['user_id']).execute()
                
                print(f"✅ Assinatura ativada para User {sub['user_id']}")
            else:
                print(f"⚠️ [Webhook] Nenhuma subscription encontrada para payment_id={payment_id}")
                
        return jsonify({'received': True})
    except Exception as e:
        print(f"❌ Erro Webhook: {e}")
        return jsonify({'error': str(e)}), 500

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
