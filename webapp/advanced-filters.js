// ========== FILTROS AVANÇADOS ==========

let advancedFilters = {
    contatado: 'todos', // 'todos', 'sim', 'nao'
    respondeu: 'todos', // 'todos', 'sim', 'nao'
    temSite: 'todos', // 'todos', 'sim', 'nao'
    temWhatsApp: 'todos', // 'todos', 'sim', 'nao'
    temTelefone: 'todos', // 'todos', 'sim', 'nao'
    tags: [] // array de tags selecionadas
};

function toggleAdvancedFilters() {
    const panel = document.getElementById('advanced-filters-panel');
    const btn = document.getElementById('btn-advanced-filters');

    if (panel.style.display === 'none' || !panel.style.display) {
        panel.style.display = 'block';
        btn.classList.add('active');
        btn.innerHTML = '🔽 Filtros Avançados';
    } else {
        panel.style.display = 'none';
        btn.classList.remove('active');
        btn.innerHTML = '🔼 Filtros Avançados';
    }
}

function updateAdvancedFilter(filterName, value) {
    advancedFilters[filterName] = value;
    // Não aplica automaticamente, espera botão
    updateFilterPreview();
}

function toggleTagFilter(tag) {
    const index = advancedFilters.tags.indexOf(tag);
    if (index > -1) {
        advancedFilters.tags.splice(index, 1);
    } else {
        advancedFilters.tags.push(tag);
    }
    updateTagFilterButtons();
    updateFilterPreview();
}

function updateFilterPreview() {
    const activeFilters = [];

    if (advancedFilters.contatado !== 'todos') {
        activeFilters.push(`Contactado: ${advancedFilters.contatado === 'sim' ? 'Sim' : 'Não'}`);
    }
    if (advancedFilters.respondeu !== 'todos') {
        activeFilters.push(`Respondeu: ${advancedFilters.respondeu === 'sim' ? 'Sim' : 'Não'}`);
    }
    if (advancedFilters.temSite !== 'todos') {
        activeFilters.push(`Site: ${advancedFilters.temSite === 'sim' ? 'Sim' : 'Não'}`);
    }
    if (advancedFilters.temWhatsApp !== 'todos') {
        activeFilters.push(`WhatsApp: ${advancedFilters.temWhatsApp === 'sim' ? 'Sim' : 'Não'}`);
    }
    if (advancedFilters.temTelefone !== 'todos') {
        activeFilters.push(`Telefone: ${advancedFilters.temTelefone === 'sim' ? 'Sim' : 'Não'}`);
    }
    if (advancedFilters.tags.length > 0) {
        activeFilters.push(`Tags: ${advancedFilters.tags.join(', ')}`);
    }

    const preview = document.getElementById('filter-preview');
    const applyBtn = document.getElementById('btn-apply-filters');

    if (preview) {
        if (activeFilters.length > 0) {
            preview.innerHTML = `📋 Filtros selecionados: ${activeFilters.join(' | ')}`;
            preview.style.display = 'block';
            if (applyBtn) applyBtn.style.display = 'inline-block';
        } else {
            preview.style.display = 'none';
            if (applyBtn) applyBtn.style.display = 'none';
        }
    }
}

function applyAdvancedFilters() {
    renderCurrentTab();
    updateFilterSummary();
    showNotification('✅ Filtros aplicados!');
}

function updateFilterSummary() {
    const activeFilters = [];

    if (advancedFilters.contatado !== 'todos') {
        activeFilters.push(`Contactado: ${advancedFilters.contatado === 'sim' ? 'Sim' : 'Não'}`);
    }
    if (advancedFilters.respondeu !== 'todos') {
        activeFilters.push(`Respondeu: ${advancedFilters.respondeu === 'sim' ? 'Sim' : 'Não'}`);
    }
    if (advancedFilters.temSite !== 'todos') {
        activeFilters.push(`Site: ${advancedFilters.temSite === 'sim' ? 'Sim' : 'Não'}`);
    }
    if (advancedFilters.temWhatsApp !== 'todos') {
        activeFilters.push(`WhatsApp: ${advancedFilters.temWhatsApp === 'sim' ? 'Sim' : 'Não'}`);
    }
    if (advancedFilters.temTelefone !== 'todos') {
        activeFilters.push(`Telefone: ${advancedFilters.temTelefone === 'sim' ? 'Sim' : 'Não'}`);
    }
    if (advancedFilters.tags.length > 0) {
        activeFilters.push(`Tags: ${advancedFilters.tags.join(', ')}`);
    }

    const summary = document.getElementById('filter-summary');
    if (summary) {
        if (activeFilters.length > 0) {
            summary.innerHTML = `<strong>Filtros ativos:</strong> ${activeFilters.join(' | ')}`;
            summary.style.display = 'block';
        } else {
            summary.style.display = 'none';
        }
    }
}

function clearAdvancedFilters() {
    advancedFilters = {
        contatado: 'todos',
        respondeu: 'todos',
        temSite: 'todos',
        temWhatsApp: 'todos',
        temTelefone: 'todos',
        tags: []
    };

    // Limpa selects
    document.querySelectorAll('.advanced-filter-select').forEach(select => {
        select.value = 'todos';
    });

    // Limpa tags
    updateTagFilterButtons();

    // Limpa preview
    const preview = document.getElementById('filter-preview');
    const applyBtn = document.getElementById('btn-apply-filters');
    const summary = document.getElementById('filter-summary');

    if (preview) preview.style.display = 'none';
    if (applyBtn) applyBtn.style.display = 'none';
    if (summary) summary.style.display = 'none';

    // Aplica (remove filtros)
    applyAdvancedFilters();
    showNotification('🔄 Filtros avançados limpos!');
}

function applyFilterToLeads(leadsToFilter) {
    return leadsToFilter.filter(lead => {
        // Filtro de contatado
        if (advancedFilters.contatado === 'sim' && lead.contatado !== 'Sim') return false;
        if (advancedFilters.contatado === 'nao' && lead.contatado === 'Sim') return false;

        // Filtro de respondeu
        if (advancedFilters.respondeu === 'sim' && lead.respondeu !== 'Sim') return false;
        if (advancedFilters.respondeu === 'nao' && lead.respondeu === 'Sim') return false;

        // Filtro de site
        if (advancedFilters.temSite === 'sim' && !lead.tem_site) return false;
        if (advancedFilters.temSite === 'nao' && lead.tem_site) return false;

        // Filtro de WhatsApp
        if (advancedFilters.temWhatsApp === 'sim' && !lead.whatsapp) return false;
        if (advancedFilters.temWhatsApp === 'nao' && lead.whatsapp) return false;

        // Filtro de telefone
        if (advancedFilters.temTelefone === 'sim' && !lead.telefone) return false;
        if (advancedFilters.temTelefone === 'nao' && lead.telefone) return false;

        // Filtro de tags (deve ter TODAS as tags selecionadas)
        if (advancedFilters.tags.length > 0) {
            if (!lead.tags) return false;
            const hasAllTags = advancedFilters.tags.every(tag => lead.tags.includes(tag));
            if (!hasAllTags) return false;
        }

        return true;
    });
}

function createAdvancedFiltersPanel() {
    const allUniqueTags = [...new Set(leads.flatMap(l => l.tags || []))];

    return `
        <div id="advanced-filters-panel" class="advanced-filters-panel" style="display: none;">
            <div class="filters-grid">
                <div class="filter-group">
                    <label>📞 Status de Contato:</label>
                    <select class="advanced-filter-select" onchange="updateAdvancedFilter('contatado', this.value)">
                        <option value="todos">Todos</option>
                        <option value="nao">🔴 Não Contactados</option>
                        <option value="sim">✅ Já Contactados</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label>💬 Status de Resposta:</label>
                    <select class="advanced-filter-select" onchange="updateAdvancedFilter('respondeu', this.value)">
                        <option value="todos">Todos</option>
                        <option value="nao">⏳ Aguardando Resposta</option>
                        <option value="sim">✅ Já Responderam</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label>🌐 Tem Site:</label>
                    <select class="advanced-filter-select" onchange="updateAdvancedFilter('temSite', this.value)">
                        <option value="todos">Todos</option>
                        <option value="nao">🚫 Sem Site</option>
                        <option value="sim">✅ Com Site</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label>💬 Tem WhatsApp:</label>
                    <select class="advanced-filter-select" onchange="updateAdvancedFilter('temWhatsApp', this.value)">
                        <option value="todos">Todos</option>
                        <option value="sim">✅ Com WhatsApp</option>
                        <option value="nao">❌ Sem WhatsApp</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label>📞 Tem Telefone:</label>
                    <select class="advanced-filter-select" onchange="updateAdvancedFilter('temTelefone', this.value)">
                        <option value="todos">Todos</option>
                        <option value="sim">✅ Com Telefone</option>
                        <option value="nao">❌ Sem Telefone</option>
                    </select>
                </div>
            </div>
            
            ${allUniqueTags.length > 0 ? `
                <div class="filter-tags-section">
                    <label style="display: block; margin-bottom: 10px; font-weight: 600;">🏷️ Filtrar por Tags:</label>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                        ${allUniqueTags.map(tag => `
                            <button class="tag-filter-btn" data-tag="${tag}" onclick="toggleTagFilter('${tag}')" style="
                                background: ${getTagColor(tag)};
                                color: white;
                                border: none;
                                padding: 6px 12px;
                                border-radius: 16px;
                                cursor: pointer;
                                font-size: 12px;
                                font-weight: 600;
                                transition: all 0.2s ease;
                            ">
                                ${tag}
                            </button>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            <!-- Preview e Botões -->
            <div style="margin-top: 20px; padding-top: 20px; border-top: 2px solid #e5e7eb;">
                <div id="filter-preview" class="filter-preview" style="display: none; margin-bottom: 15px;"></div>
                
                <div style="display: flex; gap: 10px; justify-content: center; align-items: center;">
                    <button id="btn-apply-filters" class="btn-apply-filters" onclick="applyAdvancedFilters()" style="display: none;">
                        🎯 Aplicar Filtros
                    </button>
                    <button class="btn-clear-advanced" onclick="clearAdvancedFilters()">
                        🔄 Limpar Filtros Avançados
                    </button>
                </div>
                
                <div id="filter-summary" class="filter-summary-active" style="display: none; margin-top: 15px;"></div>
            </div>
        </div>
    `;
}

// Modifica getCurrentTabLeads para aplicar filtros avançados
const originalGetCurrentTabLeads = window.getCurrentTabLeads;
window.getCurrentTabLeads = function () {
    let filtered = originalGetCurrentTabLeads ? originalGetCurrentTabLeads() : leads;

    // Aplica filtros avançados
    filtered = applyFilterToLeads(filtered);

    return filtered;
};

// Exporta funções
window.toggleAdvancedFilters = toggleAdvancedFilters;
window.updateAdvancedFilter = updateAdvancedFilter;
window.toggleTagFilter = toggleTagFilter;
window.clearAdvancedFilters = clearAdvancedFilters;
window.createAdvancedFiltersPanel = createAdvancedFiltersPanel;
window.applyFilterToLeads = applyFilterToLeads;

// Inicializa o painel de filtros avançados
document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('advanced-filters-container');
    if (container && typeof createAdvancedFiltersPanel === 'function') {
        container.innerHTML = createAdvancedFiltersPanel();
    }
});

// Atualiza o painel quando leads mudarem
function updateAdvancedFiltersPanel() {
    const container = document.getElementById('advanced-filters-container');
    if (container && typeof createAdvancedFiltersPanel === 'function') {
        const wasOpen = document.getElementById('advanced-filters-panel')?.style.display === 'block';
        container.innerHTML = createAdvancedFiltersPanel();
        if (wasOpen) {
            document.getElementById('advanced-filters-panel').style.display = 'block';
        }
        updateTagFilterButtons();
    }
}

window.updateAdvancedFiltersPanel = updateAdvancedFiltersPanel;

function updateTagFilterButtons() {
    const buttons = document.querySelectorAll('.tag-filter-btn');
    buttons.forEach(btn => {
        const tag = btn.dataset.tag;
        if (advancedFilters.tags.includes(tag)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}
