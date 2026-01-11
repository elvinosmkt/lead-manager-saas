-- 1. Modificar tabela USERS (adicionar campos de plano)
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS credits_used INT DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS credits_limit INT DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_start TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_end TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS asaas_customer_id TEXT;

-- 2. Criar tabela de ASSINATURAS
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan TEXT NOT NULL,
    billing_cycle TEXT, -- 'mensal', 'trimestral'
    price DECIMAL(10,2),
    status TEXT DEFAULT 'active', -- 'active', 'canceled', 'expired'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    provider TEXT DEFAULT 'asaas', -- 'stripe', 'asaas', 'manual'
    provider_subscription_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Criar tabela de TRANSAÇÕES DE CRÉDITO
CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    amount INT NOT NULL,
    type TEXT NOT NULL, -- 'used', 'refund', 'purchase', 'renewal', 'bonus'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Criar tabela de ADMINS
CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'admin', -- 'admin', 'super_admin'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Criar tabela de LOGS
CREATE TABLE IF NOT EXISTS activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID REFERENCES admins(id),
    action TEXT NOT NULL,
    target_type TEXT, -- 'user', 'subscription'
    target_id UUID,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Políticas de Segurança (RLS) - Opcional, mas recomendado
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;

-- Política: Usuário vê apenas seus dados
CREATE POLICY "Users can view own subscriptions" ON subscriptions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can view own credits" ON credit_transactions FOR SELECT USING (auth.uid() = user_id);

-- 7. Criar Admin Inicial (senha: admin123 - alterar depois!)
-- Hash para 'admin123' (exemplo simples, ideal usar bcrypt no backend)
INSERT INTO admins (email, password_hash, name, role)
VALUES ('admin@leadmanager.com', 'scrypt:32768:8:1$md5hash_placeholder_change_me', 'Admin', 'super_admin')
ON CONFLICT (email) DO NOTHING;
