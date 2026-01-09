// Lead Manager - Visual Melhorado com Abas
let leads = [];
let currentTab = 'todos';
let currentFilters = { search: '', cidade: '', nicho: '' };

// Inicialização
document.addEventListener('DOMContentLoaded', async () => {
    // 1. Verifica login
    const user = await LeadAPI.getUser();
    if (!user) {
        window.location.href = 'login.html';
        return;
    }

    // 2. Carrega leads
    showNotification('🔄 Carregando leads da nuvem...', 'info');
    leads = await LeadAPI.getAll();

    // Se vazio, tenta migrar do localStorage antigo
    if (leads.length === 0) {
        const migrated = await LeadAPI.syncFromLocal();
        if (migrated) {
            showNotification('✅ Leads migrados para a nuvem!');
            leads = await LeadAPI.getAll();
        }
    }

    updateAllStats();
    populateFilters();
    renderCurrentTab();
});

// Substitui saveLeadsToStorage por função vazia pois salvamos individualmente agora
function saveLeadsToStorage() {
    // console.log('Saved to storage (deprecated)');
}

// Recarrega do banco
async function reloadLeads() {
    leads = await LeadAPI.getAll();
    updateAllStats();
    populateFilters();
    renderCurrentTab();
}

// Upload de Arquivo
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
        try {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
            const jsonData = XLSX.utils.sheet_to_json(firstSheet);

            const newLeads = jsonData.map((row, index) => ({
                id: Date.now() + index,
                nome: row.nome || '',
                telefone: row.telefone || '',
                whatsapp: row.whatsapp || '',
                whatsapp_link: row.whatsapp_link || `https://wa.me/${row.whatsapp}`,
                endereco: row.endereco || '',
                avaliacao: row.avaliacao || '',
                nicho: row.nicho || '',
                cidade: row.cidade || '',
                tem_site: row.tem_site === 'Sim' || row.tem_site === true,
                website: row.website || '',
                contatado: row.contatado || 'Não',
                respondeu: row.respondeu || 'Não',
                observacoes: row.observacoes || '',
                data_coleta: row.data_coleta || new Date().toISOString()
            }));

            const existingNames = new Set(leads.map(l => l.nome.toLowerCase()));
            const uniqueNewLeads = newLeads.filter(lead =>
                !existingNames.has(lead.nome.toLowerCase())
            );

            leads = [...leads, ...uniqueNewLeads];

            // Salva no Supabase
            if (uniqueNewLeads.length > 0) {
                showNotification('☁️ Enviando leads para nuvem...');
                await LeadAPI.saveBatch(uniqueNewLeads);
                await reloadLeads(); // Recarrega com IDs corretos
            } else {
                saveLeadsToStorage();
            }

            showNotification(`✅ ${uniqueNewLeads.length} leads importados!`);

            updateAllStats();
            populateFilters();
            renderCurrentTab();

            event.target.value = '';
        } catch (error) {
            showNotification('❌ Erro ao importar: ' + error.message, 'error');
        }
    };
    reader.readAsArrayBuffer(file);
}

// Estatísticas
function updateAllStats() {
    const total = leads.length;
    const semSite = leads.filter(l => !l.tem_site).length;
    const comWhatsapp = leads.filter(l => l.whatsapp).length;
    const qualificados = leads.filter(l => !l.tem_site && l.whatsapp).length;
    const contatados = leads.filter(l => l.contatado === 'Sim').length;

    document.getElementById('total-leads').textContent = total;
    document.getElementById('sem-site').textContent = semSite;
    document.getElementById('com-whatsapp').textContent = comWhatsapp;
    document.getElementById('leads-qualificados').textContent = qualificados;

    // Atualiza contadores das abas
    document.getElementById('tab-todos-count').textContent = total;
    document.getElementById('tab-sem-site-count').textContent = semSite;
    document.getElementById('tab-com-whatsapp-count').textContent = comWhatsapp;
    document.getElementById('tab-qualificados-count').textContent = qualificados;
    document.getElementById('tab-contatados-count').textContent = contatados;
}

// Filtros
function populateFilters() {
    const cidades = [...new Set(leads.map(l => l.cidade).filter(Boolean))].sort();
    const nichos = [...new Set(leads.map(l => l.nicho).filter(Boolean))].sort();
    const segmentos = [...new Set(leads.map(l => l.segmento).filter(Boolean))].sort();

    const cidadeSelect = document.getElementById('filter-cidade');
    if (cidadeSelect) {
        cidadeSelect.innerHTML = '<option value="">🏙️ Todas as Cidades</option>' +
            cidades.map(c => `<option value="${c}">${c}</option>`).join('');
    }

    const nichoSelect = document.getElementById('filter-nicho');
    if (nichoSelect) {
        nichoSelect.innerHTML = '<option value="">🎯 Todos os Nichos</option>' +
            nichos.map(n => `<option value="${n}">${n}</option>`).join('');
    }

    const segmentoSelect = document.getElementById('filter-segmento');
    if (segmentoSelect) {
        segmentoSelect.innerHTML = '<option value="">🏷️ Todos os Segmentos</option>' +
            segmentos.map(s => `<option value="${s}">${s}</option>`).join('');
    }
}

// Tabs
function switchTab(tab) {
    currentTab = tab;

    // Atualiza visual das abas
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');

    renderCurrentTab();
}

function filterInTab() {
    currentFilters.cidade = document.getElementById('filter-cidade').value;
    currentFilters.nicho = document.getElementById('filter-nicho').value;
    renderCurrentTab();
}

function searchInTab() {
    currentFilters.search = document.getElementById('search-input').value.toLowerCase();
    renderCurrentTab();
}

function renderCurrentTab() {
    let filteredLeads = leads.filter(lead => {
        // Filtro por aba
        if (currentTab === 'sem-site' && lead.tem_site) return false;
        if (currentTab === 'com-whatsapp' && !lead.whatsapp) return false;
        if (currentTab === 'qualificados' && (lead.tem_site || !lead.whatsapp)) return false;
        if (currentTab === 'contatados' && lead.contatado !== 'Sim') return false;

        // Filtros básicos
        if (currentFilters.cidade && lead.cidade !== currentFilters.cidade) return false;
        if (currentFilters.nicho && lead.nicho !== currentFilters.nicho) return false;

        if (currentFilters.search) {
            const search = currentFilters.search;
            const matchesSearch = lead.nome.toLowerCase().includes(search) ||
                (lead.telefone && lead.telefone.includes(search)) ||
                (lead.endereco && lead.endereco.toLowerCase().includes(search));
            if (!matchesSearch) return false;
        }

        return true;
    });

    // Aplica filtros avançados se existirem
    if (typeof applyFilterToLeads === 'function') {
        filteredLeads = applyFilterToLeads(filteredLeads);
    }

    renderLeads(filteredLeads);
}

function renderLeads(leadsToRender) {
    const container = document.getElementById('leads-container');

    if (leadsToRender.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📊</div>
                <h3>Nenhum lead encontrado</h3>
                <p>Tente ajustar os filtros ou importe novos leads</p>
            </div>
        `;
        return;
    }

    container.innerHTML = leadsToRender.map(lead => createCompactCard(lead)).join('');
}

function createCompactCard(lead) {
    const badges = [];
    if (!lead.tem_site) badges.push('<span class="badge badge-sem-site">🎯 Sem Site</span>');
    if (lead.telefone && !lead.whatsapp) badges.push('<span class="badge badge-telefone">📞 Telefone</span>');
    if (lead.whatsapp) badges.push('<span class="badge badge-com-whatsapp">💬 WhatsApp</span>');
    if (!lead.tem_site && lead.whatsapp) badges.push('<span class="badge badge-qualificado">⭐ Qualificado</span>');
    if (lead.contatado === 'Sim') badges.push('<span class="badge badge-contatado">✅ Contatado</span>');

    // Gera link WhatsApp com mensagem do template
    const whatsappLink = lead.whatsapp_link ? getWhatsAppLinkWithMessage(lead) : '';

    // Checkbox para seleção (somente se tiver WhatsApp)
    const checkbox = lead.whatsapp ? `
        <input type="checkbox" 
               class="lead-checkbox" 
               data-lead-id="${lead.id}" 
               onclick="event.stopPropagation(); updateSelectionCount()"
               style="width: 20px; height: 20px; cursor: pointer; margin-right: 10px;">
    ` : '';

    return `
        <div class="lead-card-compact" onclick="toggleCard(this, ${lead.id})">
            <div class="lead-card-header">
                <div style="display: flex; align-items: start; gap: 10px; flex: 1;">
                    ${checkbox}
                    <div style="flex: 1;">
                        <div class="lead-name">${lead.nome}</div>
                        <div class="lead-badges">${badges.join('')}</div>
                    </div>
                </div>
            </div>
            
            <div class="lead-info-compact">
                ${lead.telefone ? `<div>📞 <strong>${lead.telefone}</strong></div>` : ''}
                ${lead.endereco ? `<div>📍 ${lead.endereco.substring(0, 50)}${lead.endereco.length > 50 ? '...' : ''}</div>` : ''}
                ${lead.avaliacao ? `<div>⭐ <strong>${lead.avaliacao}</strong> ${lead.num_avaliacoes || ''}</div>` : ''}
                ${lead.segmento ? `<div>🏷️ ${lead.segmento}</div>` : ''}
            </div>
            
            <div class="lead-details-expanded">
                <div class="details-grid">
                    ${lead.nicho ? `<div class="detail-item"><span class="detail-label">Nicho:</span><span>${lead.nicho}</span></div>` : ''}
                    ${lead.cidade ? `<div class="detail-item"><span class="detail-label">Cidade:</span><span>${lead.cidade}</span></div>` : ''}
                    ${lead.segmento ? `<div class="detail-item"><span class="detail-label">Segmento:</span><span>${lead.segmento}</span></div>` : ''}
                    ${lead.website ? `<div class="detail-item"><span class="detail-label">Website:</span><span>${lead.website}</span></div>` : ''}
                    ${lead.data_coleta ? `<div class="detail-item"><span class="detail-label">Coletado:</span><span>${new Date(lead.data_coleta).toLocaleDateString('pt-BR')}</span></div>` : ''}
                </div>
                
                ${lead.observacoes ? `<div class="observacoes-box">📝 ${lead.observacoes}</div>` : ''}
                
                <div class="lead-actions-compact">
                    ${lead.google_maps_link ? `<a href="${lead.google_maps_link}" target="_blank" class="btn-maps-compact" onclick="event.stopPropagation()">
                        🗺️ Ver no Maps
                    </a>` : ''}
                    ${whatsappLink ? `<a href="${whatsappLink}" target="_blank" class="btn-whatsapp-compact" onclick="event.stopPropagation(); markAsContacted(${lead.id})">
                        💬 Enviar WhatsApp
                    </a>` : ''}
                    <button class="btn-edit-compact" onclick="event.stopPropagation(); openEditModal(${lead.id})">✏️ Editar</button>
                    <button class="btn-delete-compact" onclick="event.stopPropagation(); deleteLead(${lead.id})">🗑️ Deletar</button>
                </div>
            </div>
        </div>
    `;
}

// ========== TEMPLATES WHATSAPP ==========

function getWhatsAppLinkWithMessage(lead) {
    const activeTemplate = localStorage.getItem('activeTemplate') || 'template-1';
    let message = localStorage.getItem(activeTemplate) || getDefaultTemplate(activeTemplate);

    // Substitui variáveis
    message = message
        .replace(/{nome}/g, lead.nome)
        .replace(/{nicho}/g, lead.nicho || 'seu negócio')
        .replace(/{cidade}/g, lead.cidade || 'sua cidade');

    const encodedMessage = encodeURIComponent(message);
    return `${lead.whatsapp_link}?text=${encodedMessage}`;
}

function getDefaultTemplate(templateId) {
    const defaults = {
        'template-1': `Olá! 👋\n\nVi que você tem um negócio de {nicho} em {cidade}.\n\nGostaria de conversar sobre como posso ajudar a criar um site profissional para você!`,
        'template-2': `Oi! 🎯\n\nEstou oferecendo criação de sites profissionais para empresas de {nicho}.\n\nPosso te mandar um orçamento sem compromisso?`,
        'template-3': `Olá {nome}!\n\n[Sua mensagem personalizada aqui]`
    };
    return defaults[templateId] || defaults['template-1'];
}

function openTemplates() {
    // Carrega templates salvos
    document.getElementById('template-1').value = localStorage.getItem('template-1') || getDefaultTemplate('template-1');
    document.getElementById('template-2').value = localStorage.getItem('template-2') || getDefaultTemplate('template-2');
    document.getElementById('template-3').value = localStorage.getItem('template-3') || getDefaultTemplate('template-3');
    document.getElementById('active-template').value = localStorage.getItem('activeTemplate') || 'template-1';

    document.getElementById('templates-modal').classList.add('active');
}

function closeTemplates() {
    document.getElementById('templates-modal').classList.remove('active');
}

function saveTemplates() {
    localStorage.setItem('template-1', document.getElementById('template-1').value);
    localStorage.setItem('template-2', document.getElementById('template-2').value);
    localStorage.setItem('template-3', document.getElementById('template-3').value);
    localStorage.setItem('activeTemplate', document.getElementById('active-template').value);

    showNotification('💾 Templates salvos com sucesso!');
    closeTemplates();
}

function markAsContacted(leadId) {
    const lead = leads.find(l => l.id === leadId);
    if (lead && lead.contatado !== 'Sim') {
        lead.contatado = 'Sim';
        LeadAPI.save(lead); // Salva na nuvem
        updateAllStats();
    }
}

// ========== MELHORIAS DE UX ==========

function toggleSearchSection() {
    const content = document.getElementById('search-form-content');
    const btn = event.target;

    if (content.style.display === 'none') {
        content.style.display = 'block';
        btn.textContent = '▼';
    } else {
        content.style.display = 'none';
        btn.textContent = '▶';
    }
}

function clearFilters() {
    document.getElementById('filter-cidade').value = '';
    document.getElementById('filter-nicho').value = '';
    document.getElementById('search-input').value = '';
    currentFilters = { search: '', cidade: '', nicho: '' };
    renderCurrentTab();
    showNotification('🔄 Filtros limpos!');
}

function exportAllLeads() {
    if (leads.length === 0) {
        showNotification('❌ Nenhum lead para exportar!', 'error');
        return;
    }

    const ws = XLSX.utils.json_to_sheet(leads);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Todos os Leads");

    const timestamp = new Date().toISOString().split('T')[0];
    XLSX.writeFile(wb, `todos_leads_${timestamp}.xlsx`);

    showNotification('💾 Todos os leads exportados!');
}

function toggleCard(card, leadId) {
    card.classList.toggle('expanded');
}

// Modal
function openEditModal(leadId) {
    const lead = leads.find(l => l.id === leadId);
    if (!lead) return;

    document.getElementById('edit-id').value = lead.id;
    document.getElementById('edit-nome').value = lead.nome;
    document.getElementById('edit-contatado').value = lead.contatado;
    document.getElementById('edit-respondeu').value = lead.respondeu;
    document.getElementById('edit-observacoes').value = lead.observacoes || '';

    document.getElementById('edit-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('edit-modal').classList.remove('active');
}

async function saveEdit() {
    const leadId = parseInt(document.getElementById('edit-id').value);
    const lead = leads.find(l => l.id === leadId);

    if (lead) {
        lead.contatado = document.getElementById('edit-contatado').value;
        lead.respondeu = document.getElementById('edit-respondeu').value;
        lead.observacoes = document.getElementById('edit-observacoes').value;

        // Salva na nuvem
        showNotification('☁️ Salvando alterações...');
        await LeadAPI.save(lead);

        updateAllStats();
        renderCurrentTab();
        closeModal();

        showNotification('✅ Lead atualizado!');
    }
}

async function deleteLead(leadId) {
    if (!confirm('Deletar este lead?')) return;

    // Remove localmente primeiro para UI rápida
    leads = leads.filter(l => l.id !== leadId);
    updateAllStats();
    populateFilters();
    renderCurrentTab();

    // Deleta na nuvem
    await LeadAPI.delete(leadId);

    showNotification('🗑️ Lead deletado!');
}

function exportCurrentTab() {
    if (leads.length === 0) {
        showNotification('❌ Nenhum lead para exportar!', 'error');
        return;
    }

    const ws = XLSX.utils.json_to_sheet(leads);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Leads");

    const timestamp = new Date().toISOString().split('T')[0];
    XLSX.writeFile(wb, `leads_${currentTab}_${timestamp}.xlsx`);

    showNotification('💾 Exportado com sucesso!');
}

// Busca de Leads via API
let searchInterval = null;
const API_URL = 'http://localhost:5001/api';

async function startSearch() {
    const nicho = document.getElementById('search-nicho').value.trim();
    const cidade = document.getElementById('search-cidade').value.trim();
    const maxLeads = document.getElementById('search-max-leads').value;

    if (!nicho || !cidade) {
        showNotification('❌ Preencha nicho e cidade!', 'error');
        return;
    }

    try {
        const btnStart = document.getElementById('btn-start-search');
        const btnCancel = document.getElementById('btn-cancel-search');
        btnStart.disabled = true;
        btnStart.textContent = '⏳ Iniciando...';

        const response = await fetch(`${API_URL}/start-search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nicho, cidade, max_leads: maxLeads })
        });

        if (!response.ok) throw new Error('Erro ao iniciar busca');

        document.getElementById('search-progress').style.display = 'block';
        btnStart.style.display = 'none';
        btnCancel.style.display = 'inline-flex';

        startStatusPolling();
        showNotification(`🚀 Busca iniciada: ${nicho} em ${cidade}`);

    } catch (error) {
        if (error.message.includes('Failed to fetch')) {
            showNotification('⚠️ Servidor não está rodando! Execute: python3 start_app.py', 'error');
        } else {
            showNotification(`❌ Erro: ${error.message}`, 'error');
        }

        const btnStart = document.getElementById('btn-start-search');
        btnStart.disabled = false;
        btnStart.textContent = '🚀 Iniciar Busca';
    }
}

function startStatusPolling() {
    if (searchInterval) clearInterval(searchInterval);

    searchInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_URL}/search-status`);
            const status = await response.json();

            updateSearchProgress(status);

            if (status.completed) {
                clearInterval(searchInterval);
                await handleSearchComplete();
            }

            if (status.error) {
                clearInterval(searchInterval);
                showNotification(`❌ Erro: ${status.error}`, 'error');
                resetSearchUI();
            }
        } catch (error) {
            console.error('Erro ao verificar status:', error);
        }
    }, 2000);
}

function updateSearchProgress(status) {
    const progressText = document.getElementById('progress-text');
    const progressFill = document.getElementById('progress-fill');

    if (status.running) {
        progressText.textContent = `Buscando... ${status.leads_found} leads encontrados`;
        progressFill.style.width = '100%';
    } else if (status.completed) {
        progressText.textContent = `✅ Concluído! ${status.leads_found} leads`;
        progressFill.style.width = '100%';
        progressFill.style.background = 'linear-gradient(90deg, #10b981, #059669)';
    }
}

async function handleSearchComplete() {
    try {
        const response = await fetch(`${API_URL}/get-leads`);
        const data = await response.json();

        if (data.success && data.leads.length > 0) {
            const existingNames = new Set(leads.map(l => l.nome.toLowerCase()));
            const newLeads = data.leads
                .filter(lead => !existingNames.has(lead.nome.toLowerCase()))
                .map((lead, index) => ({ ...lead, id: Date.now() + index }));

            leads = [...leads, ...newLeads];
            saveLeadsToStorage();
            updateAllStats();
            populateFilters();
            renderCurrentTab();

            showNotification(`🎉 ${newLeads.length} novos leads importados!`);
        } else {
            showNotification('⚠️ Nenhum lead novo encontrado', 'error');
        }
    } catch (error) {
        showNotification('❌ Erro ao importar leads', 'error');
    } finally {
        resetSearchUI();
    }
}

function resetSearchUI() {
    const btnStart = document.getElementById('btn-start-search');
    const btnCancel = document.getElementById('btn-cancel-search');
    const searchProgress = document.getElementById('search-progress');

    btnStart.style.display = 'inline-flex';
    btnStart.disabled = false;
    btnStart.textContent = '🚀 Iniciar Busca';
    btnCancel.style.display = 'none';

    setTimeout(() => {
        searchProgress.style.display = 'none';
        document.getElementById('progress-fill').style.width = '0%';
    }, 3000);
}

async function cancelSearch() {
    try {
        await fetch(`${API_URL}/cancel-search`, { method: 'POST' });
        clearInterval(searchInterval);
        showNotification('🛑 Busca cancelada');
        resetSearchUI();
    } catch (error) {
        console.error('Erro ao cancelar:', error);
    }
}

// Notificações
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : '#ef4444'};
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 10000;
        font-weight: 600;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);

window.onclick = function (event) {
    const modal = document.getElementById('edit-modal');
    if (event.target === modal) closeModal();
}

// ========== FUNÇÕES DE MASSA AÇÕES ==========

function exportSelected() {
    const selectedLeads = getSelectedLeads();
    if (selectedLeads.length === 0) {
        showNotification('⚠️ Nenhum lead selecionado!', 'error');
        return;
    }

    const ws = XLSX.utils.json_to_sheet(selectedLeads);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Leads Selecionados");

    const timestamp = new Date().toISOString().split('T')[0];
    XLSX.writeFile(wb, `leads_selecionados_${timestamp}.xlsx`);

    showNotification(`💾 ${selectedLeads.length} leads exportados!`);
}

function deleteSelected() {
    const selectedLeads = getSelectedLeads();
    if (selectedLeads.length === 0) {
        showNotification('⚠️ Nenhum lead selecionado!', 'error');
        return;
    }

    if (!confirm(`Deletar ${selectedLeads.length} leads selecionados?`)) return;

    const selectedIds = selectedLeads.map(l => l.id);
    leads = leads.filter(l => !selectedIds.includes(l.id));

    saveLeadsToStorage();
    updateAllStats();
    populateFilters();
    renderCurrentTab();
    updateSelectionCount();

    showNotification(`🗑️ ${selectedLeads.length} leads deletados!`);
}

// Sobrescreve renderLeads para mostrar/ocultar barra de ações
const originalRenderCurrentTab = renderCurrentTab;
renderCurrentTab = function () {
    originalRenderCurrentTab();

    // Mostra barra se houver leads com WhatsApp
    const leadsComWhatsApp = getCurrentTabLeads().filter(l => l.whatsapp);
    const bar = document.getElementById('massa-actions-bar');
    if (bar) {
        bar.style.display = leadsComWhatsApp.length > 0 ? 'block' : 'none';
    }
};

function getCurrentTabLeads() {
    return leads.filter(lead => {
        if (currentTab === 'sem-site' && lead.tem_site) return false;
        if (currentTab === 'com-whatsapp' && !lead.whatsapp) return false;
        if (currentTab === 'qualificados' && (lead.tem_site || !lead.whatsapp)) return false;
        if (currentTab === 'contatados' && lead.contatado !== 'Sim') return false;

        if (currentFilters.cidade && lead.cidade !== currentFilters.cidade) return false;
        if (currentFilters.nicho && lead.nicho !== currentFilters.nicho) return false;

        if (currentFilters.search) {
            const search = currentFilters.search;
            return lead.nome.toLowerCase().includes(search) ||
                (lead.telefone && lead.telefone.includes(search)) ||
                (lead.endereco && lead.endereco.toLowerCase().includes(search));
        }

        return true;
    });
}

window.exportSelected = exportSelected;
window.deleteSelected = deleteSelected;
