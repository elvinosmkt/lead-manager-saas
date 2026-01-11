# 🎯 PLANO COMPLETO - Checkout Funcional com Asaas

## 📋 SITUAÇÃO ATUAL (Problemas Identificados)

- [ ] ❌ Botão PIX travado (não redireciona)
- [ ] ❌ Cartão de crédito não funciona
- [ ] ❌ Validação de CPF inválido não alerta
- [ ] ❌ Integração Asaas retornando erro de CPF inválido
- [ ] ❌ Fluxo de pagamento incompleto

---

## 🔧 FASE 1: VALIDAÇÕES FRONTEND (Checkout.html)

### ✅ Validações de Formulário
- [ ] **1.1** Validar CPF matemático (dígitos verificadores)
- [ ] **1.2** Validar formato de telefone brasileiro
- [ ] **1.3** Validar data de nascimento (maior de 18 anos para compras)
- [ ] **1.4** Validar senha forte (mínimo 8 caracteres)
- [ ] **1.5** Mostrar feedbacks visuais em tempo real nos campos
- [ ] **1.6** Desabilitar botão "Finalizar" até todos os campos serem válidos

### ✅ UX do Formulário
- [ ] **1.7** Adicionar indicador de progresso visual
- [ ] **1.8** Adicionar loading no botão ao processar
- [ ] **1.9** Adicionar mensagens de erro específicas por campo
- [ ] **1.10** Garantir que máscaras funcionem corretamente

---

## 🔐 FASE 2: INTEGRAÇÃO SUPABASE AUTH

### ✅ Criação de Conta
- [ ] **2.1** Testar signup com dados reais
- [ ] **2.2** Garantir que user_metadata salva corretamente (name, cpf, phone, birth_date)
- [ ] **2.3** Implementar tratamento de email já cadastrado
- [ ] **2.4** Implementar auto-login após signup bem-sucedido
- [ ] **2.5** Criar registro em `public.users` via trigger (já existe)

### ✅ Verificação de Sessão
- [ ] **2.6** Garantir que sessão persiste ao redirecionar para pix.html
- [ ] **2.7** Implementar refresh de token se necessário
- [ ] **2.8** Adicionar fallback se usuário não estiver logado no pix.html

---

## 💳 FASE 3: INTEGRAÇÃO ASAAS - PIX

### ✅ Backend (payment_service.py)
- [ ] **3.1** Remover CPF hardcoded de fallback
- [ ] **3.2** Validar CPF no backend antes de enviar para Asaas
- [ ] **3.3** Implementar busca/criação de cliente Asaas corretamente
- [ ] **3.4** Garantir que dueDate seja data futura válida (hoje + 1 dia)
- [ ] **3.5** Tratar erros da API Asaas com mensagens específicas
- [ ] **3.6** Implementar retry lógica para casos de timeout

### ✅ Backend (start_app.py)
- [ ] **3.7** Validar dados recebidos do frontend
- [ ] **3.8** Criar subscription "pending_payment" corretamente
- [ ] **3.9** Logar todas as tentativas e erros
- [ ] **3.10** Retornar erro descritivo para o frontend

### ✅ Frontend (pix.html)
- [ ] **3.11** Ler user_metadata corretamente
- [ ] **3.12** Enviar CPF limpo (apenas números) para API
- [ ] **3.13** Mostrar loader enquanto gera PIX
- [ ] **3.14** Mostrar QR Code e código copia-cola dinamicamente
- [ ] **3.15** Tratar erros da API e exibir mensagem clara
- [ ] **3.16** Implementar polling para verificar status do pagamento

---

## 💳 FASE 4: INTEGRAÇÃO ASAAS - CARTÃO DE CRÉDITO

### ✅ Análise
- [ ] **4.1** Verificar se Asaas suporta cartão na conta atual
- [ ] **4.2** Obter credenciais de tokenização de cartão
- [ ] **4.3** Verificar limites e taxas

### ✅ Implementação
- [ ] **4.4** Integrar biblioteca de tokenização segura de cartão
- [ ] **4.5** Criar endpoint `/api/create-card-payment`
- [ ] **4.6** Implementar validação de cartão no frontend
- [ ] **4.7** Processar pagamento com token seguro
- [ ] **4.8** Tratar retornos de aprovação/negação

**DECISÃO:** Por enquanto, focar apenas em PIX (mais simples e direto). Cartão pode ser Fase 2.

---

## 🔔 FASE 5: WEBHOOKS ASAAS

### ✅ Configuração
- [ ] **5.1** Registrar URL do webhook no painel Asaas
- [ ] **5.2** Usar URL pública do Railway (https://...)
- [ ] **5.3** Implementar validação de assinatura do webhook (se disponível)

### ✅ Processamento
- [ ] **5.4** Processar evento `PAYMENT_RECEIVED`
- [ ] **5.5** Processar evento `PAYMENT_CONFIRMED`
- [ ] **5.6** Atualizar status da subscription
- [ ] **5.7** Ativar plano do usuário (update em `public.users`)
- [ ] **5.8** Resetar `credits_used` e definir `credits_limit`
- [ ] **5.9** Enviar email de confirmação (opcional)
- [ ] **5.10** Logar todos os webhooks recebidos

---

## 🧪 FASE 6: TESTES E VALIDAÇÃO

### ✅ Testes Unitários
- [ ] **6.1** Testar validação de CPF com casos válidos e inválidos
- [ ] **6.2** Testar criação de cliente Asaas
- [ ] **6.3** Testar geração de PIX
- [ ] **6.4** Testar processamento de webhook

### ✅ Testes de Integração
- [ ] **6.5** Teste completo: Cadastro → PIX → Pagamento → Ativação
- [ ] **6.6** Teste com CPF real e válido
- [ ] **6.7** Teste com email duplicado
- [ ] **6.8** Teste de PIX expirado
- [ ] **6.9** Teste de webhook em ambiente de produção

### ✅ Testes de UX
- [ ] **6.10** Navegar pelo fluxo completo no mobile
- [ ] **6.11** Verificar responsividade
- [ ] **6.12** Validar textos e mensagens de erro
- [ ] **6.13** Performance (tempo de carregamento)

---

## 🚀 FASE 7: DEPLOY E MONITORAMENTO

### ✅ Deploy
- [ ] **7.1** Commit e push do código corrigido
- [ ] **7.2** Deploy frontend (Vercel)
- [ ] **7.3** Deploy backend (Railway)
- [ ] **7.4** Verificar variáveis de ambiente (ASAAS_API_KEY)
- [ ] **7.5** Testar em produção

### ✅ Monitoramento
- [ ] **7.6** Configurar logs estruturados
- [ ] **7.7** Alertas para erros críticos
- [ ] **7.8** Dashboard de pagamentos
- [ ] **7.9** Backup de dados de transações

---

## 📝 ORDEM DE EXECUÇÃO RECOMENDADA

### 🔥 CRÍTICO (Fazer AGORA)
1. ✅ **Validação de CPF** (1.1) - Bloqueia todo o fluxo
2. ✅ **Corrigir payment_service.py** (3.1, 3.2, 3.3, 3.4) - API Asaas falhando
3. ✅ **Testar criação de PIX real** (6.6) - Validar integração
4. ✅ **Configurar Webhook** (5.1, 5.2) - Ativação automática

### 🟡 IMPORTANTE (Fazer HOJE)
5. ✅ Melhorar UX do checkout (1.7, 1.8, 1.9)
6. ✅ Processar webhooks corretamente (5.4, 5.5, 5.6, 5.7, 5.8)
7. ✅ Teste end-to-end completo (6.5)

### 🟢 MELHORIAS (Próximos Dias)
8. ✅ Implementar polling de status (3.16)
9. ✅ Email de confirmação (5.9)
10. ✅ Cartão de crédito (Fase 4 completa) - Se for necessário

---

## 🛠️ FERRAMENTAS E RECURSOS

### Validadores
- **CPF Validator JS**: https://gist.github.com/joaohcrangel/8bd48bcc40b9db63bef7201143303937
- **Asaas API Docs**: https://docs.asaas.com/
- **Asaas Sandbox**: https://sandbox.asaas.com/

### Testes
- **CPF Válido para Teste**: 123.456.789-09 (gerador online válido)
- **Asaas Test Mode**: Ativar no painel para testes sem cobranças reais

---

## 🎯 PRÓXIMOS PASSOS IMEDIATOS

Vou começar implementando os itens CRÍTICOS na seguinte ordem:

1. **Adicionar validação de CPF real no checkout**
2. **Corrigir payment_service.py para aceitar CPF do metadata**
3. **Testar criação de PIX com dados reais**
4. **Configurar webhook no painel Asaas**
5. **Testar fluxo completo**

---

**Status**: 🔴 Em Progresso
**Última Atualização**: 2026-01-11 11:25
