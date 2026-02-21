import os
import requests
import json
import threading
import time
import random
from datetime import datetime

# Gerenciador Simples de Fila em Memória (Em produção o ideal é Redis/Banco, mas atende a 1 script local)
webhook_queue = []
queue_lock = threading.Lock()
daily_count = 0
last_scan_date = datetime.now().strftime("%Y-%m-%d")

# CONFIGURAÇÕES DE SEGURANÇA
MAX_DAILY_LEADS = 30 # Nunca enviar mais de 30 abordagens frias por dia
MIN_DELAY_MINUTES = 12
MAX_DELAY_MINUTES = 25

def process_queue_worker():
    """
    Worker em background que processa a fila de webhooks lentamente,
    simulando um humano digitando para evitar banimento no WhatsApp.
    """
    global webhook_queue, daily_count, last_scan_date
    
    # URL do webhook do n8n (pode ser configurada no .env)
    webhook_url = os.environ.get("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/novo-lead")
    if not webhook_url or webhook_url == "desativado":
        return

    while True:
        # Verifica virada de dia para resetar o limite
        current_date = datetime.now().strftime("%Y-%m-%d")
        if current_date != last_scan_date:
            last_scan_date = current_date
            daily_count = 0
            
        lead_to_process = None
        
        with queue_lock:
            if len(webhook_queue) > 0 and daily_count < MAX_DAILY_LEADS:
                lead_to_process = webhook_queue.pop(0)
                daily_count += 1
                
        if lead_to_process:
            try:
                # 1. Envia o Webhook pro n8n
                print(f"[🤖 AGENTE IA] Enviando Lead '{lead_to_process.get('nome')}' para o n8n ({daily_count}/{MAX_DAILY_LEADS} hoje)")
                payload = {
                    "event": "novo_lead_sem_site",
                    "lead": lead_to_process
                }
                headers = {"Content-Type": "application/json"}
                response = requests.post(webhook_url, json=payload, headers=headers, timeout=5)
                
                # 2. Sorteia o delay para a próxima mensagem da fila (Humano typing emulator)
                # Sorteamos entre 12 a 25 minutos. Se for o último da fila, não precisa demorar.
                with queue_lock:
                    has_more = len(webhook_queue) > 0
                
                if has_more:
                    delay_seconds = random.randint(MIN_DELAY_MINUTES * 60, MAX_DELAY_MINUTES * 60)
                    print(f"🔄 Esperando {delay_seconds//60} minutos para disfarçar antiban antes do próximo envio...")
                    time.sleep(delay_seconds)
                else:
                    time.sleep(5)
                    
            except Exception as e:
                # Falhou envio, recolocamos no final da fila (opcional)
                with queue_lock:
                    daily_count -= 1 # Devolve credito do dia
                time.sleep(30)
        else:
            # Fila vazia ou limite atingido, dorme 1 minuto e checa de novo
            time.sleep(60)

# Inicia o Loop do Worker no momento em que alguém importa este arquivo
worker_thread = threading.Thread(target=process_queue_worker)
worker_thread.daemon = True
worker_thread.start()

def send_n8n_webhook(lead_data):
    """
    Função chamada pelo start_app_otimizado.py
    Ao invés de atirar direto, ele enche a fila segura.
    """
    global webhook_queue
    
    # Validação Básica: Só poe na fila se tiver WhatsApp
    if not lead_data.get('whatsapp'):
        return
        
    # Limita o tamanho máximo da fila para não estourar RAM 
    with queue_lock:
        if len(webhook_queue) < 1000:
            # Verifica se já não ta na fila
            if not any(l.get('nome') == lead_data.get('nome') for l in webhook_queue):
                webhook_queue.append(lead_data)
                q_size = len(webhook_queue)
                print(f"📦 Lead '{lead_data.get('nome')}' entrou na Fila de Abordagem do Agente. (Posição {q_size})")
