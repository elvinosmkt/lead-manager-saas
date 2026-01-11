
import os
from supabase import create_client, Client

# Configuração
url: str = os.environ.get("SUPABASE_URL", "https://wpgrollhyfoszmlotfyg.supabase.co")
key: str = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndwZ3JvbGxoeWZvc3ptbG90ZnlnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzY0NzA2OSwiZXhwIjoyMDgzMjIzMDY5fQ.gWboCPWDqFLpyuT5dgx74slhgsvwkyXPWYZ3qspspZE")

supabase: Client = create_client(url, key)

def save_lead_to_cloud(lead_data, user_id=None):
    try:
        # 1. Prepara Payload
        payload = lead_data.copy()
        
        if user_id:
            payload['user_id'] = user_id
            
        # 2. Normaliza Campos (Mappings)
        if 'site' in payload and 'website' not in payload:
            payload['website'] = payload.pop('site')
            
        # 3. Sanitização (Remove campos que não existem no banco para evitar erro)
        # Lista de colunas seguras baseadas no Create Table comum
        SAFE_COLUMNS = [
            'user_id', 'nome', 'telefone', 'whatsapp', 'website', 
            'avaliacao', 'endereco', 'cidade', 'nicho', 'status',
            'google_maps_link', 'created_at', 'id' 
        ]
        
        # Remove chaves extras (ex: 'tem_site', 'whatsapp_link' dinâmico)
        keys_to_remove = [k for k in payload.keys() if k not in SAFE_COLUMNS]
        for k in keys_to_remove:
            # print(f"⚠️ Removendo campo não-mapeado '{k}' para evitar erro de banco.")
            payload.pop(k)
            
        # 4. Tenta UPSERT (Atualiza se existir, Insere se novo)
        try:
            data = supabase.table("leads").upsert(
                payload, 
                on_conflict="user_id, nome, cidade"
            ).execute()
            print(f"💾 [DB] Lead Salvo: {payload.get('nome')}")
            return True
            
        except Exception as e_upsert:
            # Se der erro no Upsert (ex: coluna google_maps_link nao existe), tentamos limpar mais
            err_msg = str(e_upsert)
            
            if "column" in err_msg and "does not exist" in err_msg:
                # Extrai nome da coluna e tenta remover
                print(f"⚠️ Erro de Schema (Coluna Inexistente): {err_msg}")
                # Tentativa de Retry Radical: Remove campos suspeitos 'google_maps_link'
                if 'google_maps_link' in payload:
                    payload.pop('google_maps_link')
                    print("🔄 Retentando sem 'google_maps_link'...")
                    supabase.table("leads").upsert(payload, on_conflict="user_id, nome, cidade").execute()
                    print(f"💾 [DB] Lead Salvo (Recuperado): {payload.get('nome')}")
                    return True
            else:
                raise e_upsert

    except Exception as e:
        print(f"❌ FALHA GRAVE AO SALVAR NO BANCO: {e}")
        return False
