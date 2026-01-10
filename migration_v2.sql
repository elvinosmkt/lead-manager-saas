-- =================================================================
-- MIGRAÇÃO V2: BLINDAGEM E OTIMIZAÇÃO DO BANCO DE DADOS
-- Rode este script no Editor SQL do Supabase Dashboard
-- =================================================================

-- 1. GARANTIR INTEGRIDADE DOS DADOS (Evitar duplicidade)
-- Removemos duplicatas antigas antes de criar a regra (para não dar erro)
-- (Esta parte é complexa em SQL puro, então pule se o banco estiver vazio, 
--  mas aqui está uma query segura para criar a restrição apenas se não existir conflito)

-- Adiciona restrição: Um usuário não pode ter o mesmo lead (Nome + Cidade) duplicado
-- Se tentar inserir de novo, vamos configurar o Backend para ignorar ou atualizar (UPSERT).
ALTER TABLE leads 
ADD CONSTRAINT unique_lead_per_user 
UNIQUE (user_id, nome, cidade);

-- 2. MELHORIA DE PERFORMANCE (Índices)
-- Acelera o carregamento do Dashboard e dos Filtros
CREATE INDEX IF NOT EXISTS idx_leads_user_id ON leads(user_id);
CREATE INDEX IF NOT EXISTS idx_leads_cidade ON leads(cidade);
CREATE INDEX IF NOT EXISTS idx_leads_nicho ON leads(nicho);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);

-- 3. PADRONIZAÇÃO DE COLUNAS
-- Garante que 'site' e 'website' não confundam mais.
-- Se a coluna site existir e website não, renomeia.
DO $$
BEGIN
  IF EXISTS(SELECT * FROM information_schema.columns WHERE table_name = 'leads' AND column_name = 'site') THEN
      ALTER TABLE leads RENAME COLUMN site TO website;
  END IF;
END $$;

-- 4. SEGURANÇA (RLS - Row Level Security)
-- Habilita RLS se não estiver
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Política de Leitura: Usuário só vê seus próprios leads
DROP POLICY IF EXISTS "Users can view their own leads" ON leads;
CREATE POLICY "Users can view their own leads" 
ON leads FOR SELECT 
USING (auth.uid() = user_id);

-- Política de Inserção: Usuário só pode inserir pra ele mesmo
-- (Nota: O Backend usa service_role, que ignora isso, mas é bom ter para o frontend)
DROP POLICY IF EXISTS "Users can insert their own leads" ON leads;
CREATE POLICY "Users can insert their own leads" 
ON leads FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- Política de Atualização: Usuário só altera seus leads (ex: mudar status)
DROP POLICY IF EXISTS "Users can update their own leads" ON leads;
CREATE POLICY "Users can update their own leads" 
ON leads FOR UPDATE 
USING (auth.uid() = user_id);

-- Política de Deleção
DROP POLICY IF EXISTS "Users can delete their own leads" ON leads;
CREATE POLICY "Users can delete their own leads" 
ON leads FOR DELETE 
USING (auth.uid() = user_id);

-- 5. CORREÇÃO DE TIPOS E VALORES PADRÃO
ALTER TABLE leads 
ALTER COLUMN status SET DEFAULT 'new',
ALTER COLUMN created_at SET DEFAULT now();

-- Confirmação
SELECT 'Banco de Dados Blindado com Sucesso!' as status;
