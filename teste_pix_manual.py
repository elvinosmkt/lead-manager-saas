#!/usr/bin/env python3
"""
Script para testar PIX e gerar QR Code para verificação manual
"""

import requests
import os
from datetime import datetime, timedelta
import base64

ASAAS_API_KEY = os.environ.get("ASAAS_API_KEY", "")
ASAAS_API_URL = "https://api.asaas.com/v3"

def test_pix_completo():
    headers = {
        "Content-Type": "application/json",
        "access_token": ASAAS_API_KEY
    }
    
    # Usar cliente existente ou criar novo
    email = f"teste_pix_{int(datetime.now().timestamp())}@test.com"
    cpf = "12345678909"
    
    # 1. Criar cliente
    print("1. Criando cliente...")
    cust_res = requests.post(
        f"{ASAAS_API_URL}/customers",
        headers=headers,
        json={
            "name": "Teste PIX Manual",
            "email": email,
            "cpfCnpj": cpf
        }
    )
    customer_id = cust_res.json().get('id')
    print(f"   Cliente: {customer_id}")
    
    # 2. Criar cobrança
    print("2. Criando cobrança PIX...")
    due_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    pay_res = requests.post(
        f"{ASAAS_API_URL}/payments",
        headers=headers,
        json={
            "customer": customer_id,
            "billingType": "PIX",
            "value": 10.00,  # R$ 10,00 para teste (mínimo Asaas pode ser maior)
            "dueDate": due_date,
            "description": "Teste PIX Manual"
        }
    )
    
    print(f"   Status HTTP: {pay_res.status_code}")
    print(f"   Resposta: {pay_res.text}")
    
    payment = pay_res.json()
    payment_id = payment.get('id')
    
    if not payment_id:
        print(f"   ❌ ERRO: Não foi possível criar pagamento!")
        print(f"   Resposta completa: {payment}")
        return None
    
    print(f"   Payment: {payment_id}")
    print(f"   Status: {payment.get('status')}")
    
    # 3. Gerar QR Code
    print("3. Obtendo QR Code...")
    qr_res = requests.get(
        f"{ASAAS_API_URL}/payments/{payment_id}/pixQrCode",
        headers=headers
    )
    
    print(f"   Status HTTP QR: {qr_res.status_code}")
    
    if qr_res.status_code != 200:
        print(f"   ❌ Erro ao obter QR Code: {qr_res.text}")
        return None
    
    qr_data = qr_res.json()
    
    print("\n" + "="*60)
    print("📋 CÓDIGO COPIA E COLA PIX (COMPLETO):")
    print("="*60)
    print(qr_data.get('payload'))
    print("="*60)
    
    print(f"\n⏰ Expira em: {qr_data.get('expirationDate')}")
    
    # 4. Salvar imagem do QR Code para verificação
    encoded_image = qr_data.get('encodedImage')
    if encoded_image:
        # Salvar como arquivo PNG
        with open('teste_qrcode.png', 'wb') as f:
            f.write(base64.b64decode(encoded_image))
        print("\n✅ QR Code salvo em: teste_qrcode.png")
        print("   Abra este arquivo para escanear e testar!")
    
    print("\n" + "="*60)
    print("INSTRUÇÕES PARA TESTAR:")
    print("="*60)
    print("1. Copie o código acima (todo ele)")
    print("2. Abra seu app de banco")
    print("3. Vá em PIX > Pagar com código")
    print("4. Cole o código")
    print("5. Deve aparecer: R$ 10,00 para ASAAS PAGAMENTOS")
    print("="*60)
    
    return qr_data

if __name__ == "__main__":
    test_pix_completo()

