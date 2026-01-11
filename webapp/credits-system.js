// Módulo para Gerenciar UI de Créditos
window.CreditsSystem = {
    init: async function () {
        console.log('🔄 Inicializando sistema de créditos...');
        this.updateBadge();

        // Atualiza a cada 30s
        setInterval(() => this.updateBadge(), 30000);

        // Listen for internal events if any
        window.addEventListener('lead-saved', () => {
            setTimeout(() => this.updateBadge(), 2000); // Wait a bit for server update
        });
    },

    updateBadge: async function () {
        const display = document.getElementById('creditsDisplay');
        if (!display) return;

        try {
            const data = await window.LeadAPI.checkCredits();

            if (data) {
                const { credits_used, credits_limit, plan } = data;
                const remaining = (credits_limit || 0) - (credits_used || 0);

                // Formata números (1.5k)
                const format = (n) => n > 999 ? (n / 1000).toFixed(1) + 'k' : n;

                display.innerHTML = `<span style="color: ${remaining < 10 ? '#EF4444' : '#fff'}">${format(remaining)}</span> <span style="opacity:0.5; font-size: 0.8em">/ ${format(credits_limit)}</span>`;

                // Update Plan Badge if exists
                const planBadge = document.getElementById('planBadge');
                if (planBadge && plan) planBadge.textContent = plan.toUpperCase();

                // Check Lockout
                if (remaining <= 0) {
                    this.showLockoutModal();
                }
            } else {
                // Se falhar (ex: usuario nao logado ou erro), deixa padrão ou mostra erro
                // display.textContent = 'PRO'; 
            }
        } catch (e) {
            console.warn('Erro ao atualizar badge de créditos:', e);
        }
    },

    showLockoutModal: function () {
        // Implementar modal de bloqueio depois
        console.log('⚠️ Limite de créditos atingido!');
        // const btn = document.getElementById('btnStartSearch');
        // if(btn) {
        //     btn.disabled = true;
        //     btn.innerHTML = '<i class="fas fa-lock"></i> Sem Créditos';
        // }
    }
};

// Auto-init
document.addEventListener('DOMContentLoaded', () => {
    // Delay slightly to ensure Supabase client is ready
    setTimeout(() => window.CreditsSystem.init(), 1000);
});
