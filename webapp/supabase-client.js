
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
        return data || [];
    },

    // Salvar/Atualizar lead
    async save(lead) {
        const user = await this.getUser();
        if (!user) {
            console.error('Usuário não autenticado para salvar lead');
            return { error: 'Não autenticado' };
        }

        // Remove ID local se existir para deixar o banco gerar
        const { id, ...leadData } = lead;
        leadData.user_id = user.id; // Garante associação ao usuário

        // Se tem ID, fazemos o update (o Supabase usa UUID que é string)
        if (id) {
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

        // Senão, é insert
        console.log(`Inserindo novo lead...`);
        const { data, error } = await supabaseInstance
            .from('leads')
            .insert([leadData])
            .select();

        return { data, error };
    },

    // Salvar múltiplos leads (para importação)
    async saveBatch(leads) {
        const user = await this.getUser();
        if (!user) {
            console.error('Usuário não autenticado para salvar leads');
            return { error: 'Não autenticado' };
        }

        // Limpa IDs temporários e adiciona user_id
        const cleanLeads = leads.map(l => {
            const { id, ...rest } = l;
            return { ...rest, user_id: user.id };
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
