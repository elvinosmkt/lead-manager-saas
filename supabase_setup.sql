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
