
from db_config import save_lead_to_cloud, supabase
import uuid

# ID de teste ou um UUID válido se você souber um
test_user_id = str(uuid.uuid4())

print(f"🔬 Iniciando Diagnóstico de Banco de Dados...")
print(f"👤 Usando User ID Simulado: {test_user_id}")

lead_teste = {
    "nome": "Lead de Teste Diagnostico",
    "telefone": "11999999999",
    "endereco": "Rua Teste, 123",
    "nicho": "Teste",
    "cidade": "Debug City",
    "website": "http://teste.com", # Trocando 'site' por 'website'
    "whatsapp": "11999999999"
}

print("\n1. Tentando salvar lead ORIGINAL...")
# Usa nome único aleatório para não conflitar com testes anteriores
nome_unico = f"Teste Constraint {uuid.uuid4()}"
lead_teste['nome'] = nome_unico

save_lead_to_cloud(lead_teste, user_id=test_user_id)

print("\n2. Tentando salvar O MESMO lead novamente (Duplicata)...")
# Altera levemente um dado que não faz parte da chave única (ex: telefone)
lead_teste['telefone'] = "11888888888" 
save_lead_to_cloud(lead_teste, user_id=test_user_id)

print("\n--- Verificando resultado no Banco ---")
try:
    # Conta quantos leads existem com esse nome e user_id
    response = supabase.table("leads") \
        .select("*", count="exact") \
        .eq("nome", nome_unico) \
        .eq("user_id", test_user_id) \
        .execute()
        
    count = len(response.data)
    print(f"📊 Total de registros encontrados: {count}")
    
    if count == 1:
        print("✅ SUCESSO! A constraint funcionou. Apenas 1 registro existe (o segundo atualizou o primeiro ou foi ignorado).")
        print(f"   Dado atual no banco (Telefone): {response.data[0]['telefone']}")
    elif count > 1:
        print("❌ FALHA! Existem duplicatas. A constraint NÃO foi aplicada corretamente.")
    else:
        print("❌ ESTRANHO! Nenhum registro encontrado.")
        
    # Limpeza
    # supabase.table("leads").delete().eq("nome", nome_unico).execute()
except Exception as e:
    print(f"❌ Erro na verificação: {e}")
