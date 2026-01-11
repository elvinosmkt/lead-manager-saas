import requests
import os
import json

ASAAS_API_URL = "https://api.asaas.com/v3"  # Use "https://sandbox.asaas.com/v3" para testes se quiser
ASAAS_API_KEY = os.environ.get("ASAAS_API_KEY", "$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjUxN2ViODFiLTU4YWEtNDExYS05OTM3LTJmZWI1YzI1ODVjYTo6JGFhY2hfY2MwMzRiODctZmJiNy00YWFkLTk5NTctZWZkMTk2NGE5N2I2")

def create_pix_payment(customer_data, value, description, external_ref):
    """
    Cria uma cobrança PIX no Asaas.
    customer_data: {name, cpf, email}
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "access_token": ASAAS_API_KEY
        }

        # 1. Criar ou recuperar cliente no Asaas
        # (Para simplificar, vamos criar a cobrança direta passando dados do cliente, 
        # mas o ideal é buscar se já existe pelo email/cpf)
        
        payload = {
            "customer": {
                "name": customer_data['name'],
                "cpfCnpj": customer_data.get('cpf', '00000000000'), # CPF genérico se não tiver
                "email": customer_data['email']
            },
            "billingType": "PIX",
            "value": float(value),
            "dueDate": "2026-12-31", # Data futura ou hoje
            "description": description,
            "externalReference": external_ref,
            "postalService": False
        }
        
        # O Asaas precisa do ID do cliente, então primeiro buscamos ou criamos
        # Passo 1: Buscar cliente
        cust_res = requests.get(
            f"{ASAAS_API_URL}/customers?email={customer_data['email']}", 
            headers=headers
        )
        cust_data = cust_res.json()
        
        customer_id = None
        if cust_data.get('data'):
            customer_id = cust_data['data'][0]['id']
        else:
            # Cria cliente
            new_cust = requests.post(
                f"{ASAAS_API_URL}/customers",
                headers=headers,
                json=payload['customer']
            )
            customer_id = new_cust.json().get('id')
            
        if not customer_id:
            raise Exception("Falha ao criar cliente no Asaas")
            
        # Passo 2: Criar Cobrança
        payment_payload = {
            "customer": customer_id,
            "billingType": "PIX",
            "value": float(value),
            "dueDate": "2026-12-31", # Ajustar para data atual
            "description": description,
            "externalReference": external_ref
        }
        
        pay_res = requests.post(
            f"{ASAAS_API_URL}/payments", 
            headers=headers, 
            json=payment_payload
        )
        payment = pay_res.json()
        
        if 'id' not in payment:
            print(f"Erro Asaas Payment: {payment}")
            raise Exception("Erro ao gerar pagamento")
            
        # Passo 3: Pegar QR Code e Copia-Cola
        qr_res = requests.get(
            f"{ASAAS_API_URL}/payments/{payment['id']}/pixQrCode",
            headers=headers
        )
        qr_data = qr_res.json()
        
        return {
            "payment_id": payment['id'],
            "qr_code_url": qr_data.get('encodedImage'), # Base64 image
            "copy_paste": qr_data.get('payload'),
            "expires_at": qr_data.get('expirationDate')
        }

    except Exception as e:
        print(f"❌ Erro Asaas: {e}")
        return None
