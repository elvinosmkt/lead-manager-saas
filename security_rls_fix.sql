-- ============================================
-- SECURITY RLS FIX - LeadManager SaaS
-- Execute este script no Supabase SQL Editor
-- ============================================

-- 1. DROP policies antigas (se existirem) para recriar corretamente
DROP POLICY IF EXISTS "Users can only see their own leads" ON leads;
DROP POLICY IF EXISTS "Users can see own profile" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;
DROP POLICY IF EXISTS "Users can see own subscriptions" ON subscriptions;

-- 2. LEADS - Policies granulares
-- SELECT: Usuário só vê seus próprios leads
CREATE POLICY "leads_select_own" ON leads
    FOR SELECT USING (auth.uid() = user_id);

-- INSERT: Usuário só insere leads com seu próprio user_id
CREATE POLICY "leads_insert_own" ON leads
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- UPDATE: Usuário só atualiza seus próprios leads
CREATE POLICY "leads_update_own" ON leads
    FOR UPDATE USING (auth.uid() = user_id);

-- DELETE: Usuário só deleta seus próprios leads
CREATE POLICY "leads_delete_own" ON leads
    FOR DELETE USING (auth.uid() = user_id);

-- 3. USERS - Policies restritivas
-- SELECT: Usuário só vê seu próprio perfil
CREATE POLICY "users_select_own" ON users
    FOR SELECT USING (auth.uid() = id);

-- UPDATE: Usuário só atualiza campos permitidos do próprio perfil
-- (Plano e créditos NÃO devem ser alteráveis pelo usuário)
CREATE POLICY "users_update_own_limited" ON users
    FOR UPDATE USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- INSERT: Apenas via trigger (service_role). Bloquear insert direto.
-- Não criar policy de INSERT = bloqueado por padrão com RLS ativo

-- DELETE: Bloqueado (sem policy = sem acesso)

-- 4. SUBSCRIPTIONS - Somente leitura para o usuário
-- SELECT: Usuário só vê suas próprias assinaturas
CREATE POLICY "subscriptions_select_own" ON subscriptions
    FOR SELECT USING (auth.uid() = user_id);

-- INSERT/UPDATE/DELETE: Bloqueado para anon/authenticated
-- Apenas service_role (backend) pode inserir/atualizar assinaturas

-- 5. TEMPLATES - Policies granulares
DROP POLICY IF EXISTS "Users can only see their own templates" ON templates;

CREATE POLICY "templates_select_own" ON templates
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "templates_insert_own" ON templates
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "templates_update_own" ON templates
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "templates_delete_own" ON templates
    FOR DELETE USING (auth.uid() = user_id);

-- 6. SETTINGS - Policies granulares
DROP POLICY IF EXISTS "Users can only see their own settings" ON settings;

CREATE POLICY "settings_select_own" ON settings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "settings_insert_own" ON settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "settings_update_own" ON settings
    FOR UPDATE USING (auth.uid() = user_id);

-- Verificação final
SELECT tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
