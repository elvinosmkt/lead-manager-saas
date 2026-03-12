#!/usr/bin/env python3
"""
Script de Teste Completo - Integração Asaas
Testa criação de cliente e geração de PIX com dados REAIS
"""

import requests
import os
from datetime import datetime, timedelta

# Configuração
ASAAS_API_KEY = os.environ.get("ASAAS_API_KEY", "")
ASAAS_API_URL = "https://api.asaas.com/v3"

# CPF Válido de Teste (gerado online - NÃO é de pessoa real)
CPF_TESTE = "12345678909"  # Este é um CPF matematicamente válido para testes

def validar_cpf(cpf):
    """Valida CPF usando algoritmo oficial"""
    cpf = ''.join(filter(str.isdigit, cpf))
    
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

def teste_asaas_completo():
    """Executa teste completo da integração Asaas"""
    
    print("=" * 60)
    print("🧪 TESTE COMPLETO - INTEGRAÇÃO ASAAS")
    print("=" * 60)
    
    headers = {
        "Content-Type": "application/json",
        "access_token": ASAAS_API_KEY
    }
    
    # Dados de teste
    email_teste = f"teste_auto_{int(datetime.now().timestamp())}@leadmanager.test"
    
    print(f"\n📧 Email de teste: {email_teste}")
    print(f"🆔 CPF de teste: {CPF_TESTE}")
    print(f"✅ CPF válido: {validar_cpf(CPF_TESTE)}\n")
    
    # PASSO 1: Buscar cliente existente
    print("=" * 60)
    print("PASSO 1: Buscando cliente no Asaas...")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{ASAAS_API_URL}/customers?email={email_teste}",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        
        customer_id = None
        if data.get('data') and len(data['data']) > 0:
            customer_id = data['data'][0]['id']
            print(f"✅ Cliente encontrado: {customer_id}")
        else:
            print("ℹ️  Cliente não encontrado. Será criado no próximo passo.")
    
    except Exception as e:
        print(f"❌ Erro ao buscar cliente: {e}")
        return
    
    # PASSO 2: Criar cliente (se não existir)
    if not customer_id:
        print("\n" + "=" * 60)
        print("PASSO 2: Criando novo cliente...")
        print("=" * 60)
        
        customer_payload = {
            "name": "Cliente Teste Auto",
            "email": email_teste,
            "cpfCnpj": CPF_TESTE
        }
        
        try:
            response = requests.post(
                f"{ASAAS_API_URL}/customers",
                headers=headers,
                json=customer_payload
            )
            print(f"Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
            if response.status_code == 200:
                customer_id = response.json().get('id')
                print(f"✅ Cliente criado com sucesso: {customer_id}")
            else:
                print(f"❌ Erro ao criar cliente: {response.json()}")
                return
        
        except Exception as e:
            print(f"❌ Exceção ao criar cliente: {e}")
            return
    
    # PASSO 3: Criar cobrança PIX
    print("\n" + "=" * 60)
    print("PASSO 3: Criando cobrança PIX...")
    print("=" * 60)
    
    due_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    payment_payload = {
        "customer": customer_id,
        "billingType": "PIX",
        "value": 10.00,
        "dueDate": due_date,
        "description": "Teste Automatizado - Plano Pro Mensal"
    }
    
    try:
        response = requests.post(
            f"{ASAAS_API_URL}/payments",
            headers=headers,
            json=payment_payload
        )
        print(f"Status: {response.status_code}")
        payment_data = response.json()
        
        if response.status_code == 200 and 'id' in payment_data:
            payment_id = payment_data['id']
            print(f"✅ Cobrança criada: {payment_id}")
            print(f"   Valor: R$ {payment_data.get('value')}")
            print(f"   Vencimento: {payment_data.get('dueDate')}")
        else:
            print(f"❌ Erro ao criar cobrança: {payment_data}")
            return
    
    except Exception as e:
        print(f"❌ Exceção ao criar cobrança: {e}")
        return
    
    # PASSO 4: Obter QR Code PIX
    print("\n" + "=" * 60)
    print("PASSO 4: Obtendo QR Code PIX...")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{ASAAS_API_URL}/payments/{payment_id}/pixQrCode",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        qr_data = response.json()
        
        if 'encodedImage' in qr_data and 'payload' in qr_data:
            print("✅ QR Code gerado com sucesso!")
            print(f"   Tamanho da imagem (base64): {len(qr_data['encodedImage'])} chars")
            print(f"   Tamanho do payload (copia-cola): {len(qr_data['payload'])} chars")
            print(f"   Expiração: {qr_data.get('expirationDate', 'N/A')}")
            print(f"\n📋 Código Copia-Cola PIX:")
            print(f"   {qr_data['payload'][:50]}...")
        else:
            print(f"❌ Erro ao obter QR Code: {qr_data}")
            return
    
    except Exception as e:
        print(f"❌ Exceção ao obter QR Code: {e}")
        return
    
    # RESUMO
    print("\n" + "=" * 60)
    print("✅ TESTE COMPLETO FINALIZADO COM SUCESSO!")
    print("=" * 60)
    print(f"Cliente ID: {customer_id}")
    print(f"Payment ID: {payment_id}")
    print(f"Valor: R$ 10,00")
    print("\n⚠️  IMPORTANTE:")
    print("   - Este é um pagamento REAL na conta Asaas")
    print("   - Para testar sem cobrar, use o ambiente Sandbox")
    print("   - Para ativar Sandbox: https://sandbox.asaas.com/")
    print("=" * 60)

if __name__ == "__main__":
    teste_asaas_completo()
