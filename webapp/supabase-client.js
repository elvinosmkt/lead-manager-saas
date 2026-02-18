
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
