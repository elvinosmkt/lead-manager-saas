// ========== ENVIO EM MASSA WHATSAPP ==========

let massaSendState = {
    active: false,
    currentIndex: 0,
    leads: [],
    delay: 5000, // 5 segundos entre cada
    processed: 0,
    totalCount: 0
};

function startMassaSend() {
    const selectedLeads = getSelectedLeads();

    if (selectedLeads.length === 0) {
        showNotification('⚠️ Selecione pelo menos um lead!', 'error');
        return;
    }

    // Mostra confirmação
    const confirmHTML = `
        <div style="padding: 30px; text-align: center;">
            <div style="font-size: 64px; margin-bottom: 20px;">🚀</div>
            <h2 style="margin-bottom: 20px;">Envio em Massa</h2>
            <p style="margin-bottom: 20px; line-height: 1.6; color: #6b7280;">
                Preparado para enviar mensagens para <strong>${selectedLeads.length} leads</strong>?
            </p>
            <div style="background: #fef3c7; padding: 15px; border-radius: 12px; margin: 20px 0;">
                <p style="color: #d97706; font-weight: 600; margin-bottom: 10px;">⚠️ Como Funciona:</p>
                <ol style="text-align: left; color: #92400e; line-height: 1.8;">
                    <li>Abrirá uma aba do WhatsApp Web por vez</li>
                    <li>A mensagem já estará escrita</li>
                    <li>Você aperta <strong>Enter</strong> para enviar</li>
                    <li>Aguarda ${massaSendState.delay / 1000}s e abre o próximo</li>
                    <li>Você pode pausar a qualquer momento</li>
                </ol>
            </div>
            <div style="margin: 20px 0;">
                <label style="display: block; margin-bottom: 10px; font-weight: 600;">⏱️ Delay entre envios:</label>
                <select id="massa-delay" style="padding: 10px; border-radius: 8px; border: 2px solid #e5e7eb; font-size: 14px;">
                    <option value="3000">3 segundos (rápido)</option>
                    <option value="5000" selected>5 segundos (recomendado)</option>
                    <option value="10000">10 segundos (seguro)</option>
                    <option value="15000">15 segundos (muito seguro)</option>
                </select>
            </div>
            <div style="margin-top: 30px; display: flex; gap: 10px; justify-content: center;">
                <button onclick="confirmMassaSend()" style="
                    background: linear-gradient(135deg, #10b981, #059669);
                    color: white;
                    padding: 14px 28px;
                    border: none;
                    border-radius: 8px;
                    font-weight: 700;
                    cursor: pointer;
                    font-size: 15px;
                ">
                    🚀 Iniciar Envio
                </button>
                <button onclick="closeMassaModal()" style="
                    background: #e5e7eb;
                    color: #1f2937;
                    padding: 14px 28px;
                    border: none;
                    border-radius: 8px;
                    font-weight: 700;
                    cursor: pointer;
                    font-size: 15px;
                ">
                    Cancelar
                </button>
            </div>
        </div>
    `;

    showCustomModal(confirmHTML, 'massa-confirm-modal');
}

function confirmMassaSend() {
    const delay = parseInt(document.getElementById('massa-delay').value);
    massaSendState.delay = delay;
    massaSendState.leads = getSelectedLeads();
    massaSendState.currentIndex = 0;
    massaSendState.active = true;
    massaSendState.processed = 0;
    massaSendState.totalCount = massaSendState.leads.length;

    closeMassaModal();
    showMassaProgress();
    processNextLead();
}

function processNextLead() {
    if (!massaSendState.active || massaSendState.currentIndex >= massaSendState.leads.length) {
        finishMassaSend();
        return;
    }

    const lead = massaSendState.leads[massaSendState.currentIndex];

    // Atualiza progresso
    updateMassaProgress(lead);

    // Abre WhatsApp
    const whatsappLink = getWhatsAppLinkWithMessage(lead);
    window.open(whatsappLink, '_blank');

    // Marca como contatado
    markAsContacted(lead.id);

    massaSendState.processed++;
    massaSendState.currentIndex++;

    // Agenda próximo
    if (massaSendState.currentIndex < massaSendState.leads.length) {
        setTimeout(processNextLead, massaSendState.delay);
    } else {
        finishMassaSend();
    }
}

function showMassaProgress() {
    const progressHTML = `
        <div style="padding: 30px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="margin-bottom: 10px;">🚀 Envio em Massa Ativo</h2>
                <p style="color: #6b7280;">Enviando mensagens...</p>
            </div>
            
            <div id="massa-current-lead" style="background: #f3f4f6; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <p style="font-weight: 600; margin-bottom: 10px;">📤 Enviando para:</p>
                <p id="massa-lead-name" style="font-size: 18px; color: #1f2937;">-</p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span style="font-weight: 600;">Progresso:</span>
                    <span id="massa-counter" style="color: #10b981; font-weight: 700;">0 / 0</span>
                </div>
                <div style="width: 100%; height: 12px; background: #e5e7eb; border-radius: 6px; overflow: hidden;">
                    <div id="massa-progress-bar" style="height: 100%; background: linear-gradient(90deg, #10b981, #059669); width: 0%; transition: width 0.3s ease;"></div>
                </div>
            </div>
            
            <div id="massa-next-info" style="text-align: center; color: #6b7280; margin-bottom: 20px; font-size: 14px;">
                ⏱️ Próximo em <span id="massa-countdown">5</span>s...
            </div>
            
            <div style="text-align: center;">
                <button onclick="pauseMassaSend()" style="
                    background: #ef4444;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 8px;
                    font-weight: 700;
                    cursor: pointer;
                    font-size: 14px;
                ">
                    ⏹️ Pausar Envio
                </button>
            </div>
        </div>
    `;

    showCustomModal(progressHTML, 'massa-progress-modal');
}

function updateMassaProgress(lead) {
    document.getElementById('massa-lead-name').textContent = lead.nome;
    document.getElementById('massa-counter').textContent = `${massaSendState.processed + 1} / ${massaSendState.totalCount}`;

    const progress = ((massaSendState.processed + 1) / massaSendState.totalCount) * 100;
    document.getElementById('massa-progress-bar').style.width = progress + '%';

    // Atualiza countdown
    let timeLeft = massaSendState.delay / 1000;
    const countdownEl = document.getElementById('massa-countdown');

    const countdownInterval = setInterval(() => {
        timeLeft--;
        if (countdownEl) {
            countdownEl.textContent = timeLeft;
        }
        if (timeLeft <= 0) {
            clearInterval(countdownInterval);
        }
    }, 1000);
}

function pauseMassaSend() {
    massaSendState.active = false;
    closeMassaModal();
    showNotification(`⏹️ Envio pausado. ${massaSendState.processed} de ${massaSendState.totalCount} enviados.`);
}

function finishMassaSend() {
    massaSendState.active = false;
    closeMassaModal();

    // Desmarca todos
    document.querySelectorAll('.lead-checkbox').forEach(cb => cb.checked = false);
    updateSelectionCount();

    showNotification(`🎉 Envio concluído! ${massaSendState.processed} mensagens enviadas.`);

    // Atualiza visualização
    renderCurrentTab();
}

// ========== SELEÇÃO DE LEADS ==========

function getSelectedLeads() {
    const checkboxes = document.querySelectorAll('.lead-checkbox:checked');
    const selectedIds = Array.from(checkboxes).map(cb => parseInt(cb.dataset.leadId));
    return leads.filter(lead => selectedIds.includes(lead.id) && lead.whatsapp);
}

function toggleSelectAll() {
    const selectAllChecked = document.getElementById('select-all-leads').checked;
    document.querySelectorAll('.lead-checkbox').forEach(cb => {
        cb.checked = selectAllChecked;
    });
    updateSelectionCount();
}

function updateSelectionCount() {
    const selectedCount = document.querySelectorAll('.lead-checkbox:checked').length;
    const countEl = document.getElementById('selected-count');

    if (countEl) {
        countEl.textContent = selectedCount;

        const massaBtn = document.getElementById('btn-massa-send');
        if (massaBtn) {
            massaBtn.disabled = selectedCount === 0;
            massaBtn.style.opacity = selectedCount === 0 ? '0.5' : '1';
        }
    }
}

// ========== MODAIS CUSTOMIZADOS ==========

function showCustomModal(html, id) {
    const modal = document.createElement('div');
    modal.id = id;
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        backdrop-filter: blur(5px);
    `;

    const content = document.createElement('div');
    content.style.cssText = `
        background: white;
        border-radius: 20px;
        max-width: 600px;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    `;
    content.innerHTML = html;

    modal.appendChild(content);
    document.body.appendChild(modal);
}

function closeMassaModal() {
    const modals = ['massa-confirm-modal', 'massa-progress-modal'];
    modals.forEach(id => {
        const modal = document.getElementById(id);
        if (modal) modal.remove();
    });
}

// Exporta funções globalmente
window.startMassaSend = startMassaSend;
window.confirmMassaSend = confirmMassaSend;
window.pauseMassaSend = pauseMassaSend;
window.toggleSelectAll = toggleSelectAll;
window.updateSelectionCount = updateSelectionCount;
window.closeMassaModal = closeMassaModal;
