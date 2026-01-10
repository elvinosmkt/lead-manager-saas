
import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL", "https://wpgrollhyfoszmlotfyg.supabase.co")
# Usando SERVICE_ROLE para permitir que o scraper (backend) salve dados sem estar logado como usuário
# em um ambiente real, isso ficaria em variaveis de ambiente, mas para facilitar sua vida vou colocar aqui:
key: str = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndwZ3JvbGxoeWZvc3ptbG90ZnlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzY0NzA2OSwiZXhwIjoyMDgzMjIzMDY5fQ.gWboCPWDqFLpyuT5dgx74slhgsvwkyXPWYZ3qspspZE")

supabase: Client = create_client(url, key)

def save_lead_to_cloud(lead_data, user_id=None):
    try:
        # Se tiver user_id, adiciona ao payload
        if user_id:
            lead_data['user_id'] = user_id
            
        # CORREÇÃO DE SCHEMA: Supabase usa 'website', scraper usa 'site'
        if 'site' in lead_data:
            lead_data['website'] = lead_data.pop('site')
        
        # Usa UPSERT para evitar duplicatas (requer unique constraint no banco)
        # ignore_duplicates=True faz com que, se já existir, apenas ignore (mantenha o antigo)
        # Se quiser atualizar dados, use ignore_duplicates=False
        try:
            data = supabase.table("leads").upsert(lead_data, on_conflict="user_id, nome, cidade").execute()
            print(f"💾 Lead processado: {lead_data.get('nome')}")
        except Exception as e:
            # Fallback para insert normal se upsert falhar (ex: falta constraint)
            print(f"⚠️ Upsert falhou (falta constraint?), tentando insert simples: {e}")
            data = supabase.table("leads").insert(lead_data).execute()
            
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar no Supabase: {e}")
        return False
