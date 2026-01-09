// ========== VISUALIZAÇÃO EM TABELA ==========

let viewMode = 'cards'; // 'cards' ou 'table'

function toggleViewMode() {
    viewMode = viewMode === 'cards' ? 'table' : 'cards';
    localStorage.setItem('viewMode', viewMode);
    updateViewModeButton();
    renderCurrentTab();
}

function updateViewModeButton() {
    const btn = document.getElementById('btn-toggle-view');
    if (btn) {
        if (viewMode === 'table') {
            btn.innerHTML = '📋 Modo Cards';
            btn.classList.add('active-table');
        } else {
            btn.innerHTML = '📊 Modo Tabela';
            btn.classList.remove('active-table');
        }
    }
}

function renderTableView(filteredLeads) {
    if (filteredLeads.length === 0) {
        return `<div class="empty-state">
            <div class="empty-icon">📊</div>
            <h3>Nenhum lead nesta categoria</h3>
            <p>Tente ajustar os filtros ou buscar novos leads</p>
        </div>`;
    }

    return `
        <div class="table-container">
            <table class="leads-table">
                <thead>
                    <tr>
                        <th><input type="checkbox" id="select-all-table" onclick="toggleSelectAllTable()"></th>
                        <th onclick="sortTable('nome')">Nome 🔽</th>
                        <th onclick="sortTable('telefone')">Telefone 🔽</th>
                        <th onclick="sortTable('cidade')">Cidade 🔽</th>
                        <th onclick="sortTable('segmento')">Segmento 🔽</th>
                        <th>Status</th>
                        <th>Tags</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    ${filteredLeads.map(lead => `
                        <tr class="lead-row ${lead.contatado === 'Sim' ? 'contacted' : ''}" data-lead-id="${lead.id}">
                            <td>
                                ${lead.whatsapp ? `<input type="checkbox" class="lead-checkbox" data-lead-id="${lead.id}" onclick="updateSelectionCount()">` : ''}
                            </td>
                            <td class="lead-name-cell">
                                <strong>${lead.nome}</strong>
                                ${lead.avaliacao ? `<div class="rating-small">⭐ ${lead.avaliacao}</div>` : ''}
                            </td>
                            <td>
                                ${lead.telefone ? `<a href="tel:${lead.telefone}" class="phone-link">${lead.telefone}</a>` : '-'}
                            </td>
                            <td>${lead.cidade || '-'}</td>
                            <td>${lead.segmento || lead.nicho || '-'}</td>
                            <td>
                                <div class="status-badges">
                                    ${!lead.tem_site ? '<span class="badge-mini badge-sem-site">🚫</span>' : ''}
                                    ${lead.whatsapp ? '<span class="badge-mini badge-whatsapp">💬</span>' : ''}
                                    ${lead.contatado === 'Sim' ? '<span class="badge-mini badge-contatado">✅</span>' : ''}
                                </div>
                            </td>
                            <td>
                                <div class="tags-cell">
                                    ${renderLeadTags(lead)}
                                    <button class="btn-add-tag" onclick="openTagModal(${lead.id})" title="Adicionar tag">+</button>
                                </div>
                            </td>
                            <td>
                                <div class="action-buttons-table">
                                    ${lead.google_maps_link ? `<a href="${lead.google_maps_link}" target="_blank" class="btn-icon" title="Ver no Maps">🗺️</a>` : ''}
                                    ${lead.whatsapp_link ? `<a href="${getWhatsAppLinkWithMessage(lead)}" target="_blank" class="btn-icon" title="WhatsApp" onclick="markAsContacted(${lead.id})">💬</a>` : ''}
                                    <button class="btn-icon" onclick="openEditModal(${lead.id})" title="Editar">✏️</button>
                                    <button class="btn-icon btn-delete" onclick="deleteLead(${lead.id})" title="Deletar">🗑️</button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function toggleSelectAllTable() {
    const selectAll = document.getElementById('select-all-table');
    const checkboxes = document.querySelectorAll('.leads-table .lead-checkbox');
    checkboxes.forEach(cb => cb.checked = selectAll.checked);
    updateSelectionCount();
}

let tableSortColumn = null;
let tableSortAsc = true;

function sortTable(column) {
    if (tableSortColumn === column) {
        tableSortAsc = !tableSortAsc;
    } else {
        tableSortColumn = column;
        tableSortAsc = true;
    }

    renderCurrentTab();
}

// ========== SISTEMA DE TAGS ==========

function renderLeadTags(lead) {
    if (!lead.tags || lead.tags.length === 0) return '';

    return lead.tags.map(tag => {
        const tagColor = getTagColor(tag);
        return `<span class="tag-pill" style="background: ${tagColor};" onclick="filterByTag('${tag}')">${tag}</span>`;
    }).join('');
}

function getTagColor(tag) {
    const colors = {
        'Quente': '#ef4444',
        'Frio': '#3b82f6',
        'Negociando': '#f59e0b',
        'Convertido': '#10b981',
        'Sem Interesse': '#6b7280',
        'Callback': '#8b5cf6',
        'VIP': '#ec4899',
        'Prioridade': '#dc2626'
    };
    return colors[tag] || '#6366f1';
}

function openTagModal(leadId) {
    const lead = leads.find(l => l.id === leadId);
    if (!lead) return;

    const existingTags = lead.tags || [];
    const allTags = ['Quente', 'Frio', 'Negociando', 'Convertido', 'Sem Interesse', 'Callback', 'VIP', 'Prioridade'];

    const modalHTML = `
        <div style="padding: 30px;">
            <h2 style="margin-bottom: 20px;">🏷️ Gerenciar Tags</h2>
            <p style="margin-bottom: 20px;"><strong>${lead.nome}</strong></p>
            
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 10px; font-weight: 600;">Tags Disponíveis:</label>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    ${allTags.map(tag => {
        const isActive = existingTags.includes(tag);
        const color = getTagColor(tag);
        return `<button 
                            class="tag-option ${isActive ? 'active' : ''}" 
                            data-tag="${tag}"
                            onclick="toggleTag(${leadId}, '${tag}')"
                            style="background: ${isActive ? color : '#e5e7eb'}; color: ${isActive ? 'white' : '#1f2937'}; padding: 8px 16px; border: none; border-radius: 20px; cursor: pointer; font-weight: 600;">
                            ${isActive ? '✓ ' : ''}${tag}
                        </button>`;
    }).join('')}
                </div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 10px; font-weight: 600;">Ou crie uma nova:</label>
                <div style="display: flex; gap: 10px;">
                    <input type="text" id="new-tag-input" placeholder="Nome da tag..." style="flex: 1; padding: 10px; border: 2px solid #e5e7eb; border-radius: 8px;">
                    <button onclick="addCustomTag(${leadId})" style="background: #6366f1; color: white; padding: 10px 20px; border: none; border-radius: 8px; font-weight: 700; cursor: pointer;">
                        Adicionar
                    </button>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <button onclick="closeTagModal()" style="background: #e5e7eb; color: #1f2937; padding: 12px 24px; border: none; border-radius: 8px; font-weight: 700; cursor: pointer;">
                    Fechar
                </button>
            </div>
        </div>
    `;

    showCustomModal(modalHTML, 'tag-modal');
}

function toggleTag(leadId, tag) {
    const lead = leads.find(l => l.id === leadId);
    if (!lead) return;

    if (!lead.tags) lead.tags = [];

    const index = lead.tags.indexOf(tag);
    if (index > -1) {
        lead.tags.splice(index, 1);
    } else {
        lead.tags.push(tag);
    }

    saveLeadsToStorage();
    openTagModal(leadId); // Recarrega modal
    renderCurrentTab();
}

function addCustomTag(leadId) {
    const input = document.getElementById('new-tag-input');
    const tagName = input.value.trim();

    if (!tagName) {
        showNotification('Digite um nome para a tag!', 'error');
        return;
    }

    const lead = leads.find(l => l.id === leadId);
    if (!lead) return;

    if (!lead.tags) lead.tags = [];

    if (!lead.tags.includes(tagName)) {
        lead.tags.push(tagName);
        saveLeadsToStorage();
        openTagModal(leadId);
        renderCurrentTab();
        showNotification(`Tag "${tagName}" adicionada!`);
    }
}

function filterByTag(tag) {
    currentFilters.tag = tag;
    renderCurrentTab();
    showNotification(`Filtrando por tag: ${tag}`);
}

function closeTagModal() {
    const modal = document.getElementById('tag-modal');
    if (modal) modal.remove();
}

// ========== INTEGRAÇÃO ==========

// Sobrescreve renderLeads para suportar tabela
const originalRenderLeads = window.renderLeads || function () { };

window.renderLeads = function (filteredLeads) {
    // Carrega modo salvo
    const savedMode = localStorage.getItem('viewMode');
    if (savedMode) viewMode = savedMode;

    updateViewModeButton();

    // Ordena se necessário
    if (tableSortColumn && viewMode === 'table') {
        filteredLeads.sort((a, b) => {
            const aVal = a[tableSortColumn] || '';
            const bVal = b[tableSortColumn] || '';
            const comparison = aVal.toString().localeCompare(bVal.toString());
            return tableSortAsc ? comparison : -comparison;
        });
    }

    const container = document.getElementById('leads-container');
    if (viewMode === 'table') {
        container.innerHTML = renderTableView(filteredLeads);
        container.classList.add('table-mode');
        container.classList.remove('leads-grid');
    } else {
        container.innerHTML = filteredLeads.map(lead => createCompactCard(lead)).join('');
        container.classList.remove('table-mode');
        container.classList.add('leads-grid');
    }
};

// Exporta funções
window.toggleViewMode = toggleViewMode;
window.toggleTag = toggleTag;
window.addCustomTag = addCustomTag;
window.openTagModal = openTagModal;
window.closeTagModal = closeTagModal;
window.filterByTag = filterByTag;
window.sortTable = sortTable;
window.toggleSelectAllTable = toggleSelectAllTable;
