// ========== SISTEMA DE DEBUG ==========

function debugFilters() {
    console.log('=== DEBUG FILTROS ===');
    console.log('Total de leads:', leads.length);

    const contatados = leads.filter(l => l.contatado === 'Sim');
    const naoContatados = leads.filter(l => l.contatado !== 'Sim');

    console.log('Contactados:', contatados.length);
    console.log('Não Contactados:', naoContatados.length);

    console.log('\nFiltros avançados ativos:');
    console.log('- Contactado:', advancedFilters.contatado);
    console.log('- Respondeu:', advancedFilters.respondeu);
    console.log('- Tem Site:', advancedFilters.temSite);
    console.log('- Tem WhatsApp:', advancedFilters.temWhatsApp);
    console.log('- Tags:', advancedFilters.tags);

    console.log('\nExemplos de leads:');
    console.log('Primeiro lead:', leads[0]);
    console.log('Lead contatado exemplo:', contatados[0]);
    console.log('Lead não contatado exemplo:', naoContatados[0]);

    return {
        total: leads.length,
        contatados: contatados.length,
        naoContatados: naoContatados.length,
        filtros: advancedFilters
    };
}

function showDebugPanel() {
    const stats = debugFilters();

    const debugHTML = `
        <div style="padding: 30px;">
            <h2 style="margin-bottom: 20px;">🔧 Debug - Sistema de Filtros</h2>
            
            <div style="background: #f3f4f6; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="margin-bottom: 15px;">📊 Estatísticas dos Leads</h3>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                    <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; font-weight: 800; color: #6366f1;">${stats.total}</div>
                        <div style="font-size: 14px; color: #6b7280;">Total de Leads</div>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; font-weight: 800; color: #10b981;">${stats.contatados}</div>
                        <div style="font-size: 14px; color: #6b7280;">✅ Contactados</div>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 32px; font-weight: 800; color: #ef4444;">${stats.naoContatados}</div>
                        <div style="font-size: 14px; color: #6b7280;">🔴 Não Contactados</div>
                    </div>
                </div>
            </div>
            
            <div style="background: #fef3c7; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="margin-bottom: 15px;">⚙️ Filtros Ativos</h3>
                <pre style="background: white; padding: 15px; border-radius: 8px; overflow-x: auto;">${JSON.stringify(stats.filtros, null, 2)}</pre>
            </div>
            
            <div style="background: #dbeafe; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="margin-bottom: 15px;">🧪 Teste de Filtro</h3>
                <button onclick="testFilter('nao')" style="background: #ef4444; color: white; padding: 12px 24px; border: none; border-radius: 8px; margin-right: 10px; cursor: pointer; font-weight: 700;">
                    Filtrar Não Contactados
                </button>
                <button onclick="testFilter('sim')" style="background: #10b981; color: white; padding: 12px 24px; border: none; border-radius: 8px; margin-right: 10px; cursor: pointer; font-weight: 700;">
                    Filtrar Contactados
                </button>
                <button onclick="testFilter('reset')" style="background: #6b7280; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-weight: 700;">
                    Reset
                </button>
            </div>
            
            <div style="background: #f0fdf4; padding: 20px; border-radius: 12px;">
                <h3 style="margin-bottom: 15px;">📋 Console Log</h3>
                <p style="color: #065f46;">Verifique o console do navegador (F12) para mais detalhes</p>
                <button onclick="debugFilters()" style="background: #10b981; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-weight: 700; margin-top: 10px;">
                    🔍 Executar Debug no Console
                </button>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <button onclick="closeDebugPanel()" style="background: #e5e7eb; color: #1f2937; padding: 12px 24px; border: none; border-radius: 8px; font-weight: 700; cursor: pointer;">
                    Fechar
                </button>
            </div>
        </div>
    `;

    showCustomModal(debugHTML, 'debug-panel');
}

function testFilter(type) {
    if (type === 'reset') {
        clearAdvancedFilters();
        return;
    }

    // Limpa filtros primeiro
    advancedFilters = {
        contatado: type,
        respondeu: 'todos',
        temSite: 'todos',
        temWhatsApp: 'todos',
        temTelefone: 'todos',
        tags: []
    };

    // Atualiza o select
    const select = document.querySelector('.advanced-filter-select');
    if (select) select.value = type;

    // Aplica
    applyAdvancedFilters();

    console.log(`Filtro "${type}" aplicado. Verifique a lista.`);
    showNotification(`✅ Filtro aplicado: ${type === 'nao' ? 'Não Contactados' : 'Contactados'}`);
}

function closeDebugPanel() {
    const modal = document.getElementById('debug-panel');
    if (modal) modal.remove();
}

// Adiciona botão debug no header
function addDebugButton() {
    const header = document.querySelector('.header-actions');
    if (header && !document.getElementById('btn-debug')) {
        const btn = document.createElement('button');
        btn.id = 'btn-debug';
        btn.className = 'btn-debug';
        btn.textContent = '🔧 Debug';
        btn.onclick = showDebugPanel;
        header.insertBefore(btn, header.firstChild);
    }
}

// Inicializa debug
document.addEventListener('DOMContentLoaded', addDebugButton);

// Exporta funções
window.debugFilters = debugFilters;
window.showDebugPanel = showDebugPanel;
window.testFilter = testFilter;
window.closeDebugPanel = closeDebugPanel;
