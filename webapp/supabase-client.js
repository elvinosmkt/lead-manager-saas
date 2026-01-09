// Configuração do Supabase
const SUPABASE_URL = 'https://wpgrollhyfoszmlotfyg.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndwZ3JvbGxoeWZvc3ptbG90ZnlnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc2NDcwNjksImV4cCI6MjA4MzIyMzA2OX0.NQNWmwHxSMtcAUfMee3848r8OccACXhuuZjhvNnw3bM';

// Inicializa o cliente
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

console.log('✅ Supabase conectado!');

// Funções de API para Leads
const LeadAPI = {
    // Listar todos os leads
    async getAll() {
        const { data, error } = await supabase
            .from('leads')
            .select('*')
            .order('data_coleta', { ascending: false });

        if (error) {
            console.error('Erro ao buscar leads:', error);
            return [];
        }
        return data;
    },

    // Salvar/Atualizar lead
    async save(lead) {
        // Remove ID local se existir para deixar o banco gerar
        const { id, ...leadData } = lead;

        // Se tem ID numérico válido, é update
        if (id && typeof id === 'number') {
            const { data, error } = await supabase
                .from('leads')
                .update(leadData)
                .eq('id', id)
                .select();
            return { data, error };
        }

        // Senão, é insert
        const { data, error } = await supabase
            .from('leads')
            .insert([leadData])
            .select();

        return { data, error };
    },

    // Salvar múltiplos leads (para importação)
    async saveBatch(leads) {
        // Limpa IDs temporários
        const cleanLeads = leads.map(l => {
            const { id, ...rest } = l;
            return rest;
        });

        const { data, error } = await supabase
            .from('leads')
            .insert(cleanLeads)
            .select();

        return { data, error };
    },

    // Deletar lead
    async delete(id) {
        const { error } = await supabase
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
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password
        });
        return { data, error };
    },

    async signUp(email, password) {
        const { data, error } = await supabase.auth.signUp({
            email,
            password
        });
        return { data, error };
    },

    async logout() {
        const { error } = await supabase.auth.signOut();
        return { error };
    },

    async getUser() {
        const { data: { user } } = await supabase.auth.getUser();
        return user;
    }
};

// Exporta globalmente
window.LeadAPI = LeadAPI;
window.supabaseClient = supabase;
