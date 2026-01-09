// ========== SISTEMA DE REVISÃO E DUPLICADOS ==========

function reviewLeads() {
    const phoneMap = new Map();
    const duplicates = [];
    
    leads.forEach(lead => {
        if (lead.telefone) {
            const cleanPhone = lead.telefone.replace(/\D/g, '');
            if (phoneMap.has(cleanPhone)) {
                phoneMap.get(cleanPhone).push(lead);
            } else {
                phoneMap.set(cleanPhone, [lead]);
            }
        }
    });
    
    phoneMap.forEach((group, phone) => {
        if (group.length > 1) {
            duplicates.push({ phone, leads: group });
        }
    });
    
    showReviewModal(duplicates);
}

function showReviewModal(duplicates) {
    const totalDuplicados = duplicates.reduce((sum, group) => sum + group.leads.length, 0);
    
    const duplicatesList = duplicates.length > 0 ? duplicates.map(group => {
        return `<div style="background: #f9fafb; border: 2px solid #e5e7eb; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <strong>${group.leads[0].telefone || group.phone}</strong>
                <span style="background: #ef4444; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">${group.leads.length} duplicados</span>
            </div>
            <div>${group.leads.map((lead, idx) => {
                const deletebtn = idx > 0 ? `<button onclick="deleteLead(${lead.id}); reviewLeads();" style="background: #ef4444; color: white; padding: 6px 12px; border: none; border-radius: 6px; cursor: pointer;">Remover</button>` : `<span style="color: #10b981;">Manter</span>`;
                return `<div style="background: white; padding: 10px; margin: 5px 0; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                    <div><strong>${idx === 0 ? '✅ ' : ''}${lead.nome}</strong><br><small>${lead.endereco || ''}</small></div>
                    ${deletebtn}
                </div>`;
            }).join('')}</div>
        </div>`;
    }).join('') : '';
    
    const modalHTML = `<div style="padding: 30px; max-height: 90vh; overflow-y: auto;">
        <h2 style="text-align: center; margin-bottom: 20px;">🔍 Revisão de Leads</h2>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap:15px; margin-bottom: 30px;">
            <div style="background: linear-gradient(135deg, #6366f1, #4f46e5); padding: 20px; border-radius: 12px; color: white; text-align: center;">
                <div style="font-size: 32px; font-weight: 800;">${leads.length}</div>
                <div style="font-size: 14px;">Total</div>
            </div>
            <div style="background: linear-gradient(135deg, #ef4444, #dc2626); padding: 20px; border-radius: 12px; color: white; text-align: center;">
                <div style="font-size: 32px; font-weight: 800;">${duplicates.length}</div>
                <div style="font-size: 14px;">Grupos Duplicados</div>
            </div>
            <div style="background: linear-gradient(135deg, #f59e0b, #d97706); padding: 20px; border-radius: 12px; color: white; text-align: center;">
                <div style="font-size: 32px; font-weight: 800;">${totalDuplicados}</div>
                <div style="font-size: 14px;">Leads Duplicados</div>
            </div>
            <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 20px; border-radius: 12px; color: white; text-align: center;">
                <div style="font-size: 32px; font-weight: 800;">${leads.length - duplicates.length}</div>
                <div style="font-size: 14px;">Únicos</div>
            </div>
        </div>
        ${duplicates.length > 0 ? `
            <div style="background: #fef2f2; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: #ef4444;">⚠️ Duplicados Detectados</strong>
                        <p style="color: #7f1d1d; margin-top: 5px;">${duplicates.length} números duplicados</p>
                    </div>
                    <button onclick="autoMergeDuplicates()" style="background: #ef4444; color: white; padding: 12px 24px; border: none; border-radius: 8px; font-weight: 700; cursor: pointer;">
                        🔧 Limpar Automático
                    </button>
                </div>
            </div>
            <div style="max-height: 400px; overflow-y: auto;">${duplicatesList}</div>
        ` : `
            <div style="text-align: center; padding: 40px; color: #10b981;">
                <div style="font-size: 64px;">✅</div>
                <h3>Nenhum Duplicado!</h3>
                <p>Todos os leads têm números únicos.</p>
            </div>
        `}
        <div style="text-align: center; margin-top: 30px;">
            <button onclick="closeReviewModal()" style="background: #e5e7eb; color: #1f2937; padding: 12px 24px; border: none; border-radius: 8px; font-weight: 700; cursor: pointer;">Fechar</button>
        </div>
    </div>`;
    
    showCustomModal(modalHTML, 'review-modal');
}

function autoMergeDuplicates() {
    if (!confirm('Limpar duplicados automaticamente?\n\nIsto vai manter o PRIMEIRO lead de cada grupo e deletar os demais.\n\nContinuar?')) return;
    
    const phoneMap = new Map();
    const toDelete = [];
    
    leads.forEach(lead => {
        if (lead.telefone) {
            const cleanPhone = lead.telefone.replace(/\D/g, '');
            if (phoneMap.has(cleanPhone)) {
                toDelete.push(lead.id);
            } else {
                phoneMap.set(cleanPhone, lead);
            }
        }
    });
    
    if (toDelete.length === 0) {
        showNotification('✅ Nenhum duplicado para remover!');
        return;
    }
    
    leads = leads.filter(l => !toDelete.includes(l.id));
    saveLeadsToStorage();
    updateAllStats();
    populateFilters();
    renderCurrentTab();
    
    closeReviewModal();
    showNotification(`🔧 ${toDelete.length} duplicados removidos!`);
}

function closeReviewModal() {
    const modal = document.getElementById('review-modal');
    if (modal) modal.remove();
}

window.reviewLeads = reviewLeads;
window.autoMergeDuplicates = autoMergeDuplicates;
window.closeReviewModal = closeReviewModal;
