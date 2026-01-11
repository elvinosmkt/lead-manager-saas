from supabase import create_client, Client
import random

url = "https://wpgrollhyfoszmlotfyg.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndwZ3JvbGxoeWZvc3ptbG90ZnlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzY0NzA2OSwiZXhwIjoyMDgzMjIzMDY5fQ.gWboCPWDqFLpyuT5dgx74slhgsvwkyXPWYZ3qspspZE"

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
