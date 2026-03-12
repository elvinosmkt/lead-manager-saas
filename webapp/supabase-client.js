
// Configuração do Supabase
const SUPABASE_URL = 'https://wpgrollhyfoszmlotfyg.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndwZ3JvbGxoeWZvc3ptbG90ZnlnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc2NDcwNjksImV4cCI6MjA4MzIyMzA2OX0.NQNWmwHxSMtcAUfMee3848r8OccACXhuuZjhvNnw3bM';

// Inicializa o cliente
const supabaseInstance = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

console.log('✅ Supabase conectado!');

// Funções de API para Leads
const LeadAPI = {
    // Listar todos os leads DO USUÁRIO LOGADO
    async getAll() {
        const user = await this.getUser();
        if (!user) {
            console.warn('Usuário não autenticado para buscar leads');
            return [];
        }

        const { data, error } = await supabaseInstance
            .from('leads')
            .select('*')
            .eq('user_id', user.id)
            .order('data_coleta', { ascending: false });

        if (error) {
            console.error('Erro ao buscar leads:', error);
            return [];
        }

        return (data || []).map(lead => {
            // Garante compatibilidade visual com o Dashboard.html
            if (lead.respondeu === 'Sim') lead.status = 'respondeu';
            else if (lead.contatado === 'Sim') lead.status = 'contacted';
            else lead.status = 'new';

            return lead;
        });
    },

    // Salvar/Atualizar lead
    async save(lead) {
        const user = await this.getUser();
        if (!user) {
            console.error('Usuário não autenticado para salvar lead');
            return { error: 'Não autenticado' };
        }

        // Higienização para proteger contra campos não existentes no banco
        const allowedFields = ['id', 'nome', 'telefone', 'whatsapp', 'whatsapp_link', 'endereco', 'avaliacao', 'num_avaliacoes', 'segmento', 'nicho', 'cidade', 'tem_site', 'website', 'google_maps_link', 'contatado', 'respondeu', 'observacoes', 'data_coleta', 'tags', 'status'];
        const cleanLeadData = {};
        for (let key of allowedFields) {
            if (lead[key] !== undefined) {
                cleanLeadData[key] = lead[key];
            }
        }

        // Remove ID local se existir para deixar o banco gerar (ou para update)
        const { id, ...leadData } = cleanLeadData;
        leadData.user_id = user.id; // Garante associação ao usuário

        // Mapeia 'status' do frontend para campos do banco
        if (leadData.status === 'contacted' || leadData.status === 'contatado') {
            leadData.contatado = 'Sim';
        }
        if (leadData.status === 'respondeu') {
            leadData.respondeu = 'Sim';
            leadData.contatado = 'Sim';
        }
        if (leadData.status === 'new' || leadData.status === 'discarded') {
            leadData.contatado = 'Não';
            leadData.respondeu = 'Não';
        }
        delete leadData.status;

        // Se tem ID verdadeiro (number ou uuid vindo do banco), fazemos o update
        if (id && String(id).length < 20) { // garante que não é timestamp
            console.log(`Atualizando lead com id ${id}...`);
            const { data, error } = await supabaseInstance
                .from('leads')
                .update(leadData)
                .eq('id', id)
                .eq('user_id', user.id) // Garante que só atualiza leads próprios
                .select();

            if (error) console.error("Erro no update do lead:", error);
            else console.log("Lead atualizado com sucesso:", data);

            return { data, error };
        }

        // Sem ID válido: tenta encontrar pelo nome e atualizar
        if (lead.nome) {
            const { data: existing } = await supabaseInstance
                .from('leads')
                .select('id')
                .eq('nome', lead.nome)
                .eq('user_id', user.id)
                .limit(1)
                .maybeSingle();

            if (existing) {
                console.log(`Lead "${lead.nome}" já existe no banco (id=${existing.id}), atualizando...`);
                // Atualiza o ID no objeto local para futuros saves
                lead.id = existing.id;
                const { data, error } = await supabaseInstance
                    .from('leads')
                    .update(leadData)
                    .eq('id', existing.id)
                    .eq('user_id', user.id)
                    .select();

                if (error) console.error("Erro no update do lead existente:", error);
                else console.log("Lead existente atualizado:", data);

                return { data, error };
            }
        }

        // Senão, é insert de fato
        console.log(`Inserindo novo lead...`);
        const { data, error } = await supabaseInstance
            .from('leads')
            .insert([leadData])
            .select();

        // Atualiza ID local se inseriu com sucesso
        if (data && data[0]) {
            lead.id = data[0].id;
        }

        return { data, error };
    },

    // Salvar múltiplos leads (para importação)
    async saveBatch(leads) {
        const user = await this.getUser();
        if (!user) {
            console.error('Usuário não autenticado para salvar leads');
            return { error: 'Não autenticado' };
        }

        // Higienização para evitar erros por colunas ausentes
        const allowedFields = ['nome', 'telefone', 'whatsapp', 'whatsapp_link', 'endereco', 'avaliacao', 'num_avaliacoes', 'segmento', 'nicho', 'cidade', 'tem_site', 'website', 'google_maps_link', 'contatado', 'respondeu', 'observacoes', 'data_coleta', 'tags', 'status'];

        // Limpa IDs temporários e adiciona user_id
        const cleanLeads = leads.map(l => {
            const cleanLead = {};
            for (let key of allowedFields) {
                if (l[key] !== undefined) {
                    cleanLead[key] = l[key];
                }
            }
            if (cleanLead.status === 'contacted' || cleanLead.status === 'contatado') {
                cleanLead.contatado = 'Sim';
            }
            if (cleanLead.status === 'respondeu') {
                cleanLead.respondeu = 'Sim';
                cleanLead.contatado = 'Sim';
            }
            if (cleanLead.status === 'new' || cleanLead.status === 'discarded') {
                cleanLead.contatado = 'Não';
                cleanLead.respondeu = 'Não';
            }
            delete cleanLead.status;

            cleanLead.user_id = user.id;
            return cleanLead;
        });

        const { data, error } = await supabaseInstance
            .from('leads')
            .insert(cleanLeads)
            .select();

        return { data, error };
    },

    // Deletar lead
    async delete(id) {
        const { error } = await supabaseInstance
            .from('leads')
            .delete()
            .eq('id', id);
        return { error };
    },

    // Sincronizar LocalStorage para Supabase (Migração)
    async syncFromLocal() {
        const localData = localStorage.getItem('leads');
        if (localData) {
            const leads = JSON.parse(localData);
            if (leads.length > 0) {
                console.log(`🔄 Migrando ${leads.length} leads locais para nuvem...`);
                // Envia em lotes de 50
                for (let i = 0; i < leads.length; i += 50) {
                    const batch = leads.slice(i, i + 50);
                    await this.saveBatch(batch);
                }
                console.log('✅ Migração concluída!');
                localStorage.removeItem('leads'); // Limpa local após migrar
                return true;
            }
        }
        return false;
    },

    // --- AUTHENTICATION ---
    async login(email, password) {
        const { data, error } = await supabaseInstance.auth.signInWithPassword({
            email,
            password
        });
        return { data, error };
    },

    async signUp(email, password) {
        const { data, error } = await supabaseInstance.auth.signUp({
            email,
            password
        });
        return { data, error };
    },

    async logout() {
        const { error } = await supabaseInstance.auth.signOut();
        return { error };
    },

    async getUser() {
        const { data: { user } } = await supabaseInstance.auth.getUser();
        return user;
    },

    // --- CREDITS & BILLING ---
    async checkCredits() {
        const user = await this.getUser();
        if (!user) return null;

        const { data, error } = await supabaseInstance
            .from('users')
            .select('credits_used, credits_limit, plan')
            .eq('id', user.id)
            .single();

        if (error) {
            console.error('Erro ao checar créditos:', error);
            return null;
        }
        return data;
    },

    async getSubscription() {
        const user = await this.getUser();
        if (!user) return null;

        const { data, error } = await supabaseInstance
            .from('subscriptions')
            .select('*')
            .eq('user_id', user.id)
            .eq('status', 'active')
            .order('created_at', { ascending: false })
            .limit(1)
            .single();

        return data;
    }
};

// Exporta globalmente
window.LeadAPI = LeadAPI;
window.supabaseClient = supabaseInstance;
