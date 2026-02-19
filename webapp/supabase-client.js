
// Mock do Supabase Client para usar API local
const LeadAPI = {
    // --- AUTHENTICATION ---
    async login(email, password) {
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await response.json();

            if (response.ok) {
                // Salva sessão simulada
                localStorage.setItem('lead_manager_user', JSON.stringify(data.user));
                return { data: { user: data.user, session: true }, error: null };
            }
            return { data: null, error: { message: data.error || 'Erro ao logar' } };
        } catch (e) {
            return { data: null, error: { message: 'Erro de conexão: ' + e.message } };
        }
    },

    async signUp(email, password) {
        // Implementar cadastro local se necessário
        return { data: null, error: { message: 'Cadastro deve ser feito pelo administrador.' } };
    },

    async logout() {
        await fetch('/api/logout', { method: 'POST' });
        localStorage.removeItem('lead_manager_user');
        return { error: null };
    },

    async getUser() {
        try {
            const response = await fetch('/api/user-info');
            if (response.ok) {
                const user = await response.json();
                return user;
            }
        } catch (e) { console.error(e); }
        return null;
    },

    // --- LEADS & DATA ---
    async checkCredits() {
        const user = await this.getUser();
        if (user) {
            return {
                credits_used: 0, // Backend manages total credits
                credits_limit: user.credits
            };
        }
        return null;
    },

    async getAll() {
        try {
            const res = await fetch('/api/leads');
            if (res.ok) return await res.json();
        } catch (e) {
            console.error('Erro ao buscar leads:', e);
        }
        return [];
    },

    async save(lead) {
        return this.saveBatch([lead]);
    },

    async saveBatch(leads) {
        try {
            await fetch('/api/save-leads', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ leads })
            });
            return { error: null };
        } catch (e) {
            return { error: e };
        }
    },

    async delete(leadId) {
        // Implementar delete no backend se necessário
        // Por enquanto, apenas retorna sucesso (UI remove localmente)
        return { error: null };
    },

    async syncFromLocal() {
        // Migração simples de localStorage para DB
        try {
            const local = localStorage.getItem('lead_manager_leads');
            if (local) {
                const leads = JSON.parse(local);
                if (leads.length > 0) {
                    await this.saveBatch(leads);
                    localStorage.removeItem('lead_manager_leads'); // Limpa após migrar
                    return true;
                }
            }
        } catch (e) { console.error(e); }
        return false;
    }
};

// Exporta globalmente para compatibilidade
window.LeadAPI = LeadAPI;
window.supabase = {
    createClient: () => ({
        auth: {
            getUser: async () => ({ data: { user: await LeadAPI.getUser() || null } }),
            signInWithPassword: ({ email, password }) => LeadAPI.login(email, password),
            signOut: () => LeadAPI.logout()
        }
    })
};
