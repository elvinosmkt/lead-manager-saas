
import os
from supabase import create_client, Client

# Configuração
url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")

if not url or not key:
    print("⚠️ [SECURITY] SUPABASE_URL e SUPABASE_KEY devem ser configuradas como variáveis de ambiente!")
    print("   Defina: SUPABASE_URL=https://xxx.supabase.co SUPABASE_KEY=sua_service_role_key")

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
        # Lista de colunas seguras baseadas no schema real do Supabase
        SAFE_COLUMNS = [
            'user_id', 'nome', 'telefone', 'whatsapp', 'whatsapp_link',
            'website', 'avaliacao', 'num_avaliacoes', 'segmento', 
            'endereco', 'cidade', 'nicho', 
            'tem_site', 'google_maps_link',
            'contatado', 'respondeu', 'observacoes',
            'data_coleta', 'tags'
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

def check_user_credits(user_id):
    """Verifica se o usuário tem créditos disponíveis"""
    try:
        # Se for string de teste ou None, permite (modo dev)
        if not user_id or len(user_id) < 10: 
            return True, 9999
            
        res = supabase.table("users").select("credits_used, credits_limit, plan").eq("id", user_id).single().execute()
        user = res.data
        
        if not user:
            return False, 0
            
        used = user.get('credits_used', 0)
        limit = user.get('credits_limit', 0)
        
        # Se for plano 'agency' ou 'elite' (exemplo), talvez ilimitado?
        # Para agora, segue a regra estrita
        if used >= limit:
            return False, 0
            
        return True, limit - used
    except Exception as e:
        print(f"⚠️ Erro ao checar créditos: {e}")
        return True, 10 # Fallback para não bloquear em erro

def deduct_user_credits(user_id, amount=1):
    """Deduz créditos do usuário usando RPC para garantir atomicidade"""
    try:
        if not user_id or len(user_id) < 10: return
        
        # Chama a função RPC deduct_credits criada no banco
        # Isso substitui o read-modify-write inseguro por uma transação atômica no banco
        res = supabase.rpc("deduct_credits", {
            "p_user_id": user_id,
            "p_amount": amount
        }).execute()
        
        if res.data:
            print(f"✅ [CREDITS] {amount} crédito(s) deduzido(s) para {user_id}")
        else:
            print(f"⚠️ [CREDITS] Falha ao deduzir créditos (Saldo Insuficiente?) para {user_id}")
            
    except Exception as e:
        print(f"❌ Erro ao deduzir créditos via RPC: {e}")

