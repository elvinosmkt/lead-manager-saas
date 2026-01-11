-- leads-scraper/supabase_setup.sql

-- 1. Create leads table
CREATE TABLE leads (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    nome TEXT NOT NULL,
    telefone TEXT,
    whatsapp TEXT,
    whatsapp_link TEXT,
    endereco TEXT,
    avaliacao TEXT, -- Changed to TEXT to match existing app data which includes "(X avaliações)"
    num_avaliacoes TEXT,
    segmento TEXT,
    nicho TEXT,
    cidade TEXT,
    tem_site BOOLEAN DEFAULT FALSE,
    website TEXT,
    google_maps_link TEXT,
    contatado TEXT DEFAULT 'Não',
    respondeu TEXT DEFAULT 'Não',
    observacoes TEXT,
    data_coleta TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tags TEXT[] DEFAULT '{}',
    user_id UUID DEFAULT auth.uid() -- Link to authenticated user
);

-- 2. Create templates table
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    user_id UUID DEFAULT auth.uid()
);

-- 3. Create settings table for app configuration
CREATE TABLE settings (
    user_id UUID PRIMARY KEY DEFAULT auth.uid(),
    active_template_id TEXT,
    view_mode TEXT DEFAULT 'cards',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- 5. Create Policies (Users can only see their own data)
CREATE POLICY "Users can only see their own leads" ON leads
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can only see their own templates" ON templates
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can only see their own settings" ON settings
    FOR ALL USING (auth.uid() = user_id);

-- 6. Indexes for better search performance
CREATE INDEX idx_leads_cidade ON leads(cidade);
CREATE INDEX idx_leads_nicho ON leads(nicho);
CREATE INDEX idx_leads_segmento ON leads(segmento);
CREATE INDEX idx_leads_contatado ON leads(contatado);
CREATE INDEX idx_leads_user_id ON leads(user_id);

-- 7. Create users table (para controle de créditos e planos)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    plan TEXT DEFAULT 'starter',
    credits_used INTEGER DEFAULT 0,
    credits_limit INTEGER DEFAULT 500,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. Create subscriptions table (para assinaturas Asaas)
CREATE TABLE IF NOT EXISTS subscriptions (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan TEXT,
    billing_cycle TEXT,
    price DECIMAL(10,2),
    status TEXT DEFAULT 'pending',
    provider TEXT DEFAULT 'asaas',
    provider_subscription_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. Enable RLS on users and subscriptions
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can see own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can see own subscriptions" ON subscriptions
    FOR SELECT USING (auth.uid() = user_id);

-- 10. TRIGGER: Criar usuário automaticamente após signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, plan, credits_used, credits_limit)
    VALUES (
        NEW.id,
        NEW.email,
        'starter',
        0,
        500  -- Créditos iniciais para novos usuários
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 11. Function para adicionar créditos (chamada pelo webhook)
CREATE OR REPLACE FUNCTION public.add_credits(user_uuid UUID, amount INTEGER)
RETURNS VOID AS $$
BEGIN
    UPDATE public.users 
    SET credits_limit = credits_limit + amount
    WHERE id = user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 12. Function para resetar créditos usados (mensal)
CREATE OR REPLACE FUNCTION public.reset_monthly_credits()
RETURNS VOID AS $$
BEGIN
    UPDATE public.users SET credits_used = 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
