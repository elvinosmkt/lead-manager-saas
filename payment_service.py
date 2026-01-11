import requests
import os
import json
from datetime import datetime, timedelta

ASAAS_API_URL = "https://api.asaas.com/v3"
ASAAS_API_KEY = os.environ.get("ASAAS_API_KEY", "$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjUxN2ViODFiLTU4YWEtNDExYS05OTM3LTJmZWI1YzI1ODVjYTo6JGFhY2hfY2MwMzRiODctZmJiNy00YWFkLTk5NTctZWZkMTk2NGE5N2I2")

def validate_cpf(cpf):
    """Valida CPF usando algoritmo matemático"""
    cpf = ''.join(filter(str.isdigit, str(cpf)))
    
    if len(cpf) != 11:
        return False
    
    # Elimina CPFs conhecidos inválidos
    if cpf == cpf[0] * 11:
        return False
    
    # Valida primeiro dígito
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = 11 - (soma % 11)
    if resto >= 10:
        resto = 0
    if resto != int(cpf[9]):
        return False
    
    # Valida segundo dígito
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = 11 - (soma % 11)
    if resto >= 10:
        resto = 0
    if resto != int(cpf[10]):
        return False
    
    return True

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
        
        # Valida CPF antes de enviar
        cpf = customer_data.get('cpf', '').replace('.', '').replace('-', '')
        if not cpf or not validate_cpf(cpf):
            raise Exception(f"CPF inválido ou não fornecido: {cpf}")

        # Data de vencimento: amanhã
        due_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        # 1. Buscar ou criar cliente no Asaas
        cust_res = requests.get(
            f"{ASAAS_API_URL}/customers?email={customer_data['email']}", 
            headers=headers
        )
        cust_data = cust_res.json()
        
        customer_id = None
        if cust_data.get('data') and len(cust_data['data']) > 0:
            customer_id = cust_data['data'][0]['id']
            print(f"✅ Cliente existente: {customer_id}")
        else:
            # Cria novo cliente
            new_cust_payload = {
                "name": customer_data['name'],
                "cpfCnpj": cpf,
                "email": customer_data['email']
            }
            new_cust = requests.post(
                f"{ASAAS_API_URL}/customers",
                headers=headers,
                json=new_cust_payload
            )
            new_cust_data = new_cust.json()
            
            if 'id' in new_cust_data:
                customer_id = new_cust_data['id']
                print(f"✅ Novo cliente criado: {customer_id}")
            else:
                print(f"❌ Erro ao criar cliente: {new_cust_data}")
                raise Exception(f"Falha ao criar cliente: {new_cust_data.get('errors', new_cust_data)}")
            
        if not customer_id:
            raise Exception("Falha ao obter ID do cliente no Asaas")
            
        # 2. Criar Cobrança PIX
        payment_payload = {
            "customer": customer_id,
            "billingType": "PIX",
            "value": float(value),
            "dueDate": due_date,
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
            print(f"❌ Erro Asaas Payment: {payment}")
            raise Exception(f"Erro ao gerar pagamento: {payment.get('errors', payment)}")
            
        print(f"✅ Cobrança criada: {payment['id']}")
            
        # 3. Pegar QR Code e Copia-Cola
        qr_res = requests.get(
            f"{ASAAS_API_URL}/payments/{payment['id']}/pixQrCode",
            headers=headers
        )
        qr_data = qr_res.json()
        
        return {
            "payment_id": payment['id'],
            "qr_code_url": qr_data.get('encodedImage'),  # Base64 image
            "copy_paste": qr_data.get('payload'),
            "expires_at": qr_data.get('expirationDate')
        }

    except Exception as e:
        print(f"❌ Erro Asaas: {e}")
        return None
