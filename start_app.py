
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
from datetime import datetime, timedelta

# Path Setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_definitivo import GoogleMapsScraperDefinitivo
from config import CONFIG
from config import CONFIG
from db_config import save_lead_to_cloud, check_user_credits, deduct_user_credits, supabase
from payment_service import create_pix_payment

app = Flask(__name__, static_folder='webapp', static_url_path='')
CORS(app, origins=[
    "https://leads.blendagency.com.br",
    "https://leadmanager-lp.vercel.app",
    "http://localhost:3000",
    "http://localhost:5001",
    "http://127.0.0.1:3000",
    "*"  # Fallback para desenvolvimento
], supports_credentials=True)

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

                    # Deduz Crédito
                    deduct_user_credits(self.session_id, 1)
                    has_now, _ = check_user_credits(self.session_id)
                    
                    if not has_now:
                        print("⚠️ Créditos acabaram. Parando busca.")
                        active_searches[self.session_id]['stop_requested'] = True
                        state['error'] = 'Limite de créditos atingido.'

                scraper = GoogleMapsScraperDefinitivo(self.nicho, self.cidade, self.max_leads, self.filters)
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

        # 3. VERIFICA CRÉDITOS
        has_credits, remaining = check_user_credits(user_id)
        if not has_credits:
             return jsonify({
                 'error': 'CRÉDITOS ESCOTADOS', 
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

@app.route('/api/create-pix', methods=['POST'])
def api_create_pix():
    try:
        data = request.json
        # data = { user_id, email, name, cpf, plan, price, billing_cycle }
        
        description = f"Assinatura LeadManager - Plano {data.get('plan')} ({data.get('billing_cycle')})"
        external_ref = f"{data.get('user_id')}_{int(time.time())}"
        
        result = create_pix_payment(
            data, 
            data.get('price'), 
            description, 
            external_ref
        )
        
        if result:
            # Salva intenção de assinatura no Supabase
            # (Código ideal usaria INSERT no Supabase aqui)
            try:
                supabase.table("subscriptions").insert({
                    "user_id": data.get('user_id'),
                    "plan": data.get('plan'),
                    "billing_cycle": data.get('billing_cycle'),
                    "price": data.get('price'),
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
        
        # Consulta no Asaas
        import requests
        ASAAS_API_KEY = os.environ.get("ASAAS_API_KEY", "$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjUxN2ViODFiLTU4YWEtNDExYS05OTM3LTJmZWI1YzI1ODVjYTo6JGFhY2hfY2MwMzRiODctZmJiNy00YWFkLTk5NTctZWZkMTk2NGE5N2I2")
        
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
def api_create_card_subscription():
    """Cria assinatura recorrente com cartão de crédito no Asaas"""
    try:
        data = request.json
        # data = { user_id, email, name, cpf, plan, price, billing_cycle, card }
        # card = { holderName, number, expiryMonth, expiryYear, ccv }
        
        import requests
        ASAAS_API_KEY = os.environ.get("ASAAS_API_KEY", "$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjUxN2ViODFiLTU4YWEtNDExYS05OTM3LTJmZWI1YzI1ODVjYTo6JGFhY2hfY2MwMzRiODctZmJiNy00YWFkLTk5NTctZWZkMTk2NGE5N2I2")
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
        billing_cycle = data.get('billing_cycle', 'mensal')
        cycle_map = {
            'mensal': 'MONTHLY',
            'trimestral': 'QUARTERLY',
            'anual': 'YEARLY'
        }
        asaas_cycle = cycle_map.get(billing_cycle, 'MONTHLY')
        
        # 3. Criar assinatura com cartão
        card_data = data.get('card', {})
        
        subscription_payload = {
            "customer": customer_id,
            "billingType": "CREDIT_CARD",
            "value": float(data.get('price', 299)),
            "nextDueDate": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "cycle": asaas_cycle,
            "description": f"Assinatura LeadManager - Plano {data.get('plan')} ({billing_cycle})",
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
            
            # Salva no Supabase
            try:
                supabase.table("subscriptions").insert({
                    "user_id": data.get('user_id'),
                    "plan": data.get('plan'),
                    "billing_cycle": billing_cycle,
                    "price": data.get('price'),
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
                
                # Se for trimestral, multiplica por 3?
                if sub.get('billing_cycle') == 'trimestral':
                    new_credits *= 3
                
                supabase.table("users").update({
                    "plan": plan,
                    "credits_limit": new_credits,
                    "credits_used": 0 # Reseta usados? Ou soma acumulativo?
                    # Se for acumulativo, faria: credits_limit = current_limit + new_credits
                }).eq("id", sub['user_id']).execute()
                
                print(f"✅ Assinatura ativada para User {sub['user_id']}")
                
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
