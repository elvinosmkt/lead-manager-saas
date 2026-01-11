---
description: Plano de Estabilidade e Performance v2 - Lead Scraper SaaS
---

# 🚀 PLANO DE IMPLEMENTAÇÃO: ESTABILIDADE & PERFORMANCE

**Objetivo:** Eliminar erros de conexão, acelerar a busca de leads, e implementar UI em tempo real com barra de progresso dinâmica.

---

## 📋 DIAGNÓSTICO DOS PROBLEMAS ATUAIS

| Problema | Causa Raiz | Impacto |
|----------|-----------|---------|
| "Failed to fetch" | Servidor Railway dormindo (Cold Start) ou timeout | UX ruim |
| Busca lenta | Selenium navega para CADA lead (3s cada) | 10 leads = 60s |
| Leads não aparecem em tempo real | Polling a cada 2s, mas backend só envia no final | UX morta |
| Barra de progresso travada | Backend não envia `current` atualizado | UX confusa |

---

## 🎯 SOLUÇÃO PROPOSTA (3 FASES)

### FASE 1: ESTABILIDADE (Eliminar Erros) ✅ [CONCLUÍDO]
- [x] Retry automático no `startSearch` (3 tentativas)
- [x] Retry no `polling` (10 tentativas)
- [x] Memory Guard no backend
- [x] Tratamento de sessão perdida

### FASE 2: VELOCIDADE (Busca 5x Mais Rápida)
**Estratégia:** Extrair dados da LISTA de resultados, não entrando em cada link.

#### 2.1. Novo Scraper "Turbo Mode"
```python
# Em vez de:
for link in links:
    driver.get(link)  # 3s cada
    data = extract()

# Fazer:
results = driver.find_elements(By.CSS_SELECTOR, 'div[jsaction*="click"]')
for result in results:
    result.click()  # Abre painel lateral (0.5s)
    data = extract_from_panel()
```

**Benefício:** De 60s para ~15s (10 leads).

#### 2.2. Paralelização Leve
- Usar 2 threads de extração (se memória permitir)
- Processar dados enquanto scroll continua

### FASE 3: TEMPO REAL (UI Viva)
**Implementar:**

#### 3.1. Backend: Streaming de Leads
Modificar `/api/search-status` para retornar:
```json
{
  "status": "running",
  "current": "Pizzaria do João",  // Nome do negócio atual
  "leads_found": 5,
  "total": 10,
  "progress": 50,  // Percentual calculado
  "leads": [/* últimos 5 leads */]
}
```

#### 3.2. Frontend: Barra de Progresso Dinâmica
```javascript
function updateProgressUI(data) {
    // Atualiza texto do negócio atual
    document.getElementById('currentBusiness').innerText = data.current || "Processando...";
    
    // Atualiza contador
    document.getElementById('leadsFoundCount').innerText = data.leads_found;
    
    // Atualiza barra (baseado no progresso real, não estimado)
    document.getElementById('progressBar').style.width = `${data.progress}%`;
}
```

#### 3.3. Renderização Incremental
```javascript
// Ao receber novos leads no polling
data.leads.forEach(newLead => {
    if (!state.leads.some(l => l.nome === newLead.nome)) {
        state.leads.unshift(newLead);
        // Adiciona card com animação
        prependLeadCard(newLead);
    }
});
```

---

## 📅 CRONOGRAMA DE IMPLEMENTAÇÃO

| Etapa | Descrição | Tempo Estimado |
|-------|-----------|----------------|
| 2.1 | Reescrever `scraper_definitivo.py` com método "painel lateral" | 20 min |
| 2.2 | Adicionar campo `current` e `progress` no estado do backend | 10 min |
| 3.1 | Atualizar `start_app.py` para enviar progresso real | 10 min |
| 3.2 | Atualizar `index.html` para renderização incremental com animação | 15 min |
| 3.3 | Testes e Deploy | 10 min |

**Total: ~1 hora**

---

## 🔧 CÓDIGO A MODIFICAR

### Arquivos Afetados:
1. `scraper_definitivo.py` - Lógica de extração turbo
2. `start_app.py` - Callback de lead com `current` e `progress`
3. `webapp/index.html` - UI de progresso e renderização incremental

---

## ✅ CHECKLIST DE VALIDAÇÃO

Após implementação, verificar:
- [ ] Buscar 10 leads demora menos de 30 segundos
- [ ] Barra de progresso avança a cada lead encontrado
- [ ] Leads aparecem na tela conforme são captados (sem esperar o fim)
- [ ] Não ocorre "Failed to fetch" mesmo com servidor dormindo
- [ ] Console não mostra erros de JavaScript
- [ ] Banco de dados recebe todos os leads corretamente

---

## 🚀 PRÓXIMOS PASSOS

1. **Executar Fase 2.1:** Reescrever scraper com método de painel lateral
2. **Testar localmente** (se possível) antes de deploy
3. **Deploy e Monitorar** logs do Railway

---

**Deseja que eu execute este plano agora?**
