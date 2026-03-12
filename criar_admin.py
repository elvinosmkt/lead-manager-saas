from supabase import create_client, Client
import os

url = os.environ.get("SUPABASE_URL", "")
key = os.environ.get("SUPABASE_KEY", "")

if not url or not key:
    print("❌ Defina SUPABASE_URL e SUPABASE_KEY como variáveis de ambiente!")
    exit(1)

supabase: Client = create_client(url, key)

email = input("Digite o email do admin: ")
password = input("Digite a senha do admin (min 6 digitos): ")

try:
    # Cria usuário já com email confirmado
    user = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True
    })
    print(f"\n✅ Usuário {email} criado com sucesso!")
    print("Agora você pode fazer login no site.")
except Exception as e:
    print(f"\n❌ Erro ao criar usuário: {e}")
