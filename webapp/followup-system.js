// ========== SISTEMA DE FOLLOW-UP INTELIGENTE ==========

// Configurações de follow-up
const FOLLOW_UP_CONFIG = {
    diasPrimeiroFollowUp: 3,  // Após 3 dias sem resposta
    diasSegundoFollowUp: 7,   // Após 7 dias sem resposta
    diasTerceiroFollowUp: 14  // Após 14 dias sem resposta
};

function getLeadsForFollowUp() {
    const now = new Date();
    return leads.filter(lead => {
        if (!lead.contatado_em || lead.respondeu === 'Sim') return false;

        const contatadoEm = new Date(lead.contatado_em);
        const diasDesdeContato = Math.floor((now - contatadoEm) / (1000 * 60 * 60 * 24));

        return diasDesdeContato >= FOLLOW_UP_CONFIG.diasPrimeiroFollowUp;
    });
}

function getDiasSemResposta(lead) {
    if (!lead.contatado_em) return 0;

    const now = new Date();
    const contatadoEm = new Date(lead.contatado_em);
    return Math.floor((now - contatadoEm) / (1000 * 60 * 60 * 24));
}

function getFollowUpLevel(dias) {
    if (dias >= FOLLOW_UP_CONFIG.diasTerceiroFollowUp) return 3;
    if (dias >= FOLLOW_UP_CONFIG.diasSegundoFollowUp) return 2;
    if (dias >= FOLLOW_UP_CONFIG.diasPrimeiroFollowUp) return 1;
    return 0;
}

function getFollowUpMessage(lead, level) {
    const templates = {
        1: `Oi ${lead.nome}! 👋

Enviei uma mensagem alguns dias atrás sobre criação de site.

Conseguiu dar uma olhada? Posso esclarecer alguma dúvida?`,

        2: `Olá ${lead.nome}!

Gostaria muito de poder ajudar sua empresa de ${lead.nicho || 'seu negócio'}.

Tem interesse em conversar sobre ter um site profissional?`,

        3: `${lead.nome}, tudo bem?

Esta é minha última tentativa de contato.

Se tiver interesse em ter um site, é só me chamar! 😊

Obrigado!`
    };

    return templates[level] || templates[1];
}

function openFollowUpDashboard() {
    const leadsFollowUp = getLeadsForFollowUp();
    const aguardandoResposta = leads.filter(l => l.contatado === 'Sim' && l.respondeu === 'Não');
    const responderam = leads.filter(l => l.respondeu === 'Sim');
    const taxaResposta = leads.filter(l => l.contatado === 'Sim').length > 0
        ? Math.round((responderam.length / leads.filter(l => l.contatado === 'Sim').length) * 100)
        : 0;

    // Agrupa por nível de urgência
    const urgente = leadsFollowUp.filter(l => getFollowUpLevel(getDiasSemResposta(l)) >= 3);
    const medio = leadsFollowUp.filter(l => {
        const level = getFollowUpLevel(getDiasSemResposta(l));
        return level === 2;
    });
    const baixo = leadsFollowUp.filter(l => getFollowUpLevel(getDiasSemResposta(l)) === 1);

    const dashboardHTML = `
        <div style="padding: 30px; max-height: 90vh; overflow-y: auto;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="margin-bottom: 10px;">📊 Dashboard de Follow-up</h2>
                <p style="color: #6b7280;">Gerencie seus leads e conversões</p>
            </div>
            
            <!-- Métricas -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px;">
                <div style="background: linear-gradient(135deg, #ef4444, #dc2626); padding: 20px; border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 32px; font-weight: 800;">${leadsFollowUp.length}</div>
                    <div style="font-size: 14px; opacity: 0.9;">Precisam Follow-up</div>
                </div>
                <div style="background: linear-gradient(135deg, #f59e0b, #d97706); padding: 20px; border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 32px; font-weight: 800;">${aguardandoResposta.length}</div>
                    <div style="font-size: 14px; opacity: 0.9;">Aguardando Resposta</div>
                </div>
                <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 20px; border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 32px; font-weight: 800;">${responderam.length}</div>
                    <div style="font-size: 14px; opacity: 0.9;">Responderam</div>
                </div>
                <div style="background: linear-gradient(135deg, #6366f1, #4f46e5); padding: 20px; border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 32px; font-weight: 800;">${taxaResposta}%</div>
                    <div style="font-size: 14px; opacity: 0.9;">Taxa de Resposta</div>
                </div>
            </div>
            
            <!-- Urgências -->
            <div style="margin-bottom: 30px;">
                <h3 style="margin-bottom: 15px;">🚨 Por Urgência</h3>
                
                ${urgente.length > 0 ? `
                    <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="color: #ef4444;">🔴 Urgente (14+ dias)</strong>
                                <p style="color: #7f1d1d; margin-top: 5px; font-size: 14px;">${urgente.length} leads</p>
                            </div>
                            <button onclick="filterAndContactFollowUp(3)" style="
                                background: #ef4444;
                                color: white;
                                padding: 10px 20px;
                                border: none;
                                border-radius: 8px;
                                font-weight: 700;
                                cursor: pointer;
                            ">
                                Recontactar Todos
                            </button>
                        </div>
                    </div>
                ` : ''}
                
                ${medio.length > 0 ? `
                    <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="color: #f59e0b;">🟡 Médio (7-13 dias)</strong>
                                <p style="color: #78350f; margin-top: 5px; font-size: 14px;">${medio.length} leads</p>
                            </div>
                            <button onclick="filterAndContactFollowUp(2)" style="
                                background: #f59e0b;
                                color: white;
                                padding: 10px 20px;
                                border: none;
                                border-radius: 8px;
                                font-weight: 700;
                                cursor: pointer;
                            ">
                                Recontactar Todos
                            </button>
                        </div>
                    </div>
                ` : ''}
                
                ${baixo.length > 0 ? `
                    <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 15px; border-radius: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="color: #10b981;">🟢 Baixo (3-6 dias)</strong>
                                <p style="color: #065f46; margin-top: 5px; font-size: 14px;">${baixo.length} leads</p>
                            </div>
                            <button onclick="filterAndContactFollowUp(1)" style="
                                background: #10b981;
                                color: white;
                                padding: 10px 20px;
                                border: none;
                                border-radius: 8px;
                                font-weight: 700;
                                cursor: pointer;
                            ">
                                Recontactar Todos
                            </button>
                        </div>
                    </div>
                ` : ''}
                
                ${leadsFollowUp.length === 0 ? `
                    <div style="text-align: center; padding: 40px; color: #6b7280;">
                        <div style="font-size: 64px; margin-bottom: 15px;">✅</div>
                        <p style="font-weight: 600;">Nenhum lead precisa de follow-up no momento!</p>
                        <p style="font-size: 14px; margin-top: 10px;">Todos os leads contatados foram respondidos ou ainda estão no prazo.</p>
                    </div>
                ` : ''}
            </div>
            
            <!-- Lista Detalhada -->
            ${leadsFollowUp.length > 0 ? `
                <div style="margin-top: 30px;">
                    <h3 style="margin-bottom: 15px;">📋 Lista Completa</h3>
                    <div style="max-height: 400px; overflow-y: auto;">
                        ${leadsFollowUp.map(lead => {
        const dias = getDiasSemResposta(lead);
        const level = getFollowUpLevel(dias);
        const urgencyColors = {
            1: { bg: '#f0fdf4', text: '#065f46', badge: '#10b981' },
            2: { bg: '#fffbeb', text: '#78350f', badge: '#f59e0b' },
            3: { bg: '#fef2f2', text: '#7f1d1d', badge: '#ef4444' }
        };
        const colors = urgencyColors[level];

        return `
                                <div style="background: ${colors.bg}; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid ${colors.badge};">
                                    <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 10px;">
                                        <div style="flex: 1;">
                                            <strong style="color: ${colors.text}; font-size: 16px;">${lead.nome}</strong>
                                            <p style="color: ${colors.text}; font-size: 14px; margin-top: 5px;">
                                                📞 ${lead.telefone || 'N/A'} | 📍 ${lead.cidade || 'N/A'}
                                            </p>
                                            <p style="color: ${colors.text}; font-size: 13px; margin-top: 5px;">
                                                ⏱️ <strong>${dias} dias</strong> sem resposta
                                            </p>
                                        </div>
                                        <button onclick="sendFollowUpMessage(${lead.id}, ${level})" style="
                                            background: ${colors.badge};
                                            color: white;
                                            padding: 10px 20px;
                                            border: none;
                                            border-radius: 8px;
                                            font-weight: 700;
                                            cursor: pointer;
                                            white-space: nowrap;
                                        ">
                                            💬 Enviar Follow-up
                                        </button>
                                    </div>
                                </div>
                            `;
    }).join('')}
                    </div>
                </div>
            ` : ''}
            
            <div style="margin-top: 30px; text-align: center;">
                <button onclick="closeFollowUpDashboard()" style="
                    background: #e5e7eb;
                    color: #1f2937;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 8px;
                    font-weight: 700;
                    cursor: pointer;
                    font-size: 14px;
                ">
                    Fechar
                </button>
            </div>
        </div>
    `;

    showCustomModal(dashboardHTML, 'followup-dashboard-modal');
}

function sendFollowUpMessage(leadId, level) {
    const lead = leads.find(l => l.id === leadId);
    if (!lead || !lead.whatsapp_link) return;

    const message = getFollowUpMessage(lead, level);
    const encodedMessage = encodeURIComponent(message);
    const whatsappLink = `${lead.whatsapp_link}?text=${encodedMessage}`;

    window.open(whatsappLink, '_blank');

    // Atualiza última tentativa
    lead.ultima_tentativa = new Date().toISOString();
    lead.tentativas_followup = (lead.tentativas_followup || 0) + 1;
    saveLeadsToStorage();

    showNotification(`📤 Follow-up enviado para ${lead.nome}!`);

    // Atualiza dashboard
    setTimeout(() => {
        closeFollowUpDashboard();
        openFollowUpDashboard();
    }, 500);
}

function filterAndContactFollowUp(level) {
    const leadsFollowUp = getLeadsForFollowUp();
    const filtered = leadsFollowUp.filter(lead => {
        const dias = getDiasSemResposta(lead);
        return getFollowUpLevel(dias) === level;
    });

    if (filtered.length === 0) {
        showNotification('Nenhum lead neste nível!', 'error');
        return;
    }

    // Prepara para envio em massa
    massaSendState.leads = filtered;
    massaSendState.currentIndex = 0;
    massaSendState.active = true;
    massaSendState.processed = 0;
    massaSendState.totalCount = filtered.length;
    massaSendState.followUpMode = true;
    massaSendState.followUpLevel = level;

    closeFollowUpDashboard();
    showMassaProgress();
    processNextFollowUp();
}

function processNextFollowUp() {
    if (!massaSendState.active || massaSendState.currentIndex >= massaSendState.leads.length) {
        finishMassaSend();
        massaSendState.followUpMode = false;
        return;
    }

    const lead = massaSendState.leads[massaSendState.currentIndex];

    updateMassaProgress(lead);

    // Envia follow-up
    sendFollowUpMessage(lead.id, massaSendState.followUpLevel);

    massaSendState.processed++;
    massaSendState.currentIndex++;

    if (massaSendState.currentIndex < massaSendState.leads.length) {
        setTimeout(processNextFollowUp, massaSendState.delay);
    } else {
        finishMassaSend();
        massaSendState.followUpMode = false;
    }
}

function closeFollowUpDashboard() {
    const modal = document.getElementById('followup-dashboard-modal');
    if (modal) modal.remove();
}

// Atualiza markAsContacted para registrar data
const originalMarkAsContacted = markAsContacted;
markAsContacted = function (leadId) {
    const lead = leads.find(l => l.id === leadId);
    if (lead && lead.contatado !== 'Sim') {
        lead.contatado = 'Sim';
        lead.contatado_em = new Date().toISOString();
        saveLeadsToStorage();
        updateAllStats();
    }
};

// Exporta funções
window.openFollowUpDashboard = openFollowUpDashboard;
window.sendFollowUpMessage = sendFollowUpMessage;
window.filterAndContactFollowUp = filterAndContactFollowUp;
window.closeFollowUpDashboard = closeFollowUpDashboard;
