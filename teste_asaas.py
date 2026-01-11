import requests
from datetime import datetime, timedelta

# Chave fornecida pelo usuário
ASAAS_API_KEY = "$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjUxN2ViODFiLTU4YWEtNDExYS05OTM3LTJmZWI1YzI1ODVjYTo6JGFhY2hfY2MwMzRiODctZmJiNy00YWFkLTk5NTctZWZkMTk2NGE5N2I2"
ASAAS_API_URL = "https://api.asaas.com/v3"

def teste_criar_pix():
    print("🚀 Iniciando Teste Asaas...")
    
    headers = {
        "Content-Type": "application/json",
        "access_token": ASAAS_API_KEY
    }
    
    # 1. Tentar Buscar um cliente (usando um email de teste)
    email_teste = "teste_dev_vibe@gmail.com"
    print(f"1. Buscando cliente: {email_teste}")
    
    try:
        cust_res = requests.get(
            f"{ASAAS_API_URL}/customers?email={email_teste}", 
            headers=headers
        )
        print(f"   Status Busca: {cust_res.status_code}")
        
        cust_data = cust_res.json()
        customer_id = None
        
        if cust_data.get('data'):
            customer_id = cust_data['data'][0]['id']
            print(f"   Cliente encontrado: {customer_id}")
        else:
            print("   Cliente não encontrado. Tentando criar...")
            # Criar cliente com CPF VÁLIDO (gerado para teste)
            # Obs: Em prod, Asaas valida CPF. 
            # Vou usar um CPF de teste gerado online (válido matematicamente)
            new_customer_payload = {
                "name": "Teste Vibe Dev",
                "email": email_teste,
                "cpfCnpj": "49826868065" # CPF aleatório válido gerado
            }
            res_create = requests.post(
                f"{ASAAS_API_URL}/customers",
                headers=headers,
                json=new_customer_payload
            )
            print(f"   Res Criação: {res_create.text}")
            customer_id = res_create.json().get('id')

        if not customer_id:
            print("❌ Falha crítica: Não foi possível obter ID do cliente.")
            return

        # 2. Criar Cobrança
        print(f"2. Criando Cobrança PIX para {customer_id}...")
        due_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        payment_payload = {
            "customer": customer_id,
            "billingType": "PIX",
            "value": 10.00,
            "dueDate": due_date,
            "description": "Teste Integração Vibe"
        }
        
        pay_res = requests.post(
            f"{ASAAS_API_URL}/payments", 
            headers=headers, 
            json=payment_payload
        )
        print(f"   Status Pagamento: {pay_res.status_code}")
        payment_data = pay_res.json()
        
        if 'id' in payment_data:
            print(f"✅ Pagamento Criado! ID: {payment_data['id']}")
            
            # 3. Pegar QR Code
            qr_res = requests.get(
                f"{ASAAS_API_URL}/payments/{payment_data['id']}/pixQrCode",
                headers=headers
            )
            qr_data = qr_res.json()
            if 'encodedImage' in qr_data:
                print("✅ QR Code obtido com sucesso!")
            else:
                print(f"❌ Erro QR Code: {qr_data}")
        else:
            print(f"❌ Erro ao criar pagamento: {payment_data}")

    except Exception as e:
        print(f"❌ Exceção: {e}")

if __name__ == "__main__":
    teste_criar_pix()
