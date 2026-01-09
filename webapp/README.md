# 📊 Lead Manager - Aplicativo Web

Aplicativo web completo para gestão de leads do Google Maps com sistema de follow-up.

## ✨ Funcionalidades

### 📥 Importação de Dados
- Importa planilhas Excel (.xlsx) geradas pelo scraper
- Remove leads duplicados automaticamente
- Suporta múltiplas importações

### 🔍 Filtros Avançados
- **Por Cidade**: Filtra leads por localização
- **Por Nicho**: Filtra por tipo de negócio
- **Por Status**: 
  - Não Contatado
  - Aguardando Resposta
  - Respondeu
- **Busca**: Pesquisa por nome, telefone ou WhatsApp

### 📊 Estatísticas em Tempo Real
- Total de leads
- Não contatados
- Aguardando resposta
- Leads que responderam

### 💬 Integração WhatsApp
- **Link direto** para enviar mensagem (wa.me)
- Clique e vá direto para o WhatsApp Web
- Perfeito para follow-up

### ✏️ Gestão de Leads
- **Editar status**: Marcar como contatado/respondeu
- **Adicionar observações**: Notas personalizadas
- **Deletar leads**: Remover leads não qualificados
- **Exportar dados**: Backup em Excel

### 💾 Dados Persistentes
- Armazena tudo no navegador (localStorage)
- Dados não são perdidos ao fechar
- Funciona offline

---

## 🚀 Como Usar

### 1. Abrir o Aplicativo
```bash
cd webapp
open index.html
```

Ou clique duas vezes no arquivo `index.html`

### 2. Importar Leads
1. Clique em "📁 Importar Planilha"
2. Selecione o arquivo Excel gerado pelo scraper
3. Pronto! Os leads aparecerão automaticamente

### 3. Filtrar e Buscar
- Use os filtros de **Cidade**, **Nicho** e **Status**
- Digite na busca para encontrar leads específicos
- Clique em "🔄 Limpar Filtros" para resetar

### 4. Contactar Leads
1. Na lista, encontre o lead desejado
2. Clique em "💬 Enviar WhatsApp"
3. Abrirá direto no WhatsApp Web
4. Envie sua mensagem!

### 5. Fazer Follow-up
1. Após contactar, clique em "✏️ Editar"
2. Marque "Contatado" como "Sim"
3. Se respondeu, marque "Respondeu" como "Sim"
4. Adicione observações se necessário

### 6. Gerenciar Status
- **Filtre por "Não Contatado"** → Veja quem falta contactar
- **Filtre por "Aguardando Resposta"** → Faça follow-up
- **Filtre por "Respondeu"** → Leads quentes!

---

## 📋 Fluxo de Trabalho Sugerido

### Dia 1: Importação e Primeiro Contato
```
1. Importar planilha
2. Filtrar por "Não Contatado"
3. Ordenar por avaliação (melhores primeiro)
4. Enviar mensagem via WhatsApp  
5. Marcar como "Contatado"
```

### Dia 2-3: Follow-up
```
1. Filtrar por "Aguardando Resposta"
2. Verificar quem respondeu
3. Atualizar status para "Respondeu"
4. Adicionar observações sobre a conversa
```

### Semanal: Novo Follow-up
```
1. Filtrar leads antigos "Aguardando Resposta"
2. Enviar mensagem de seguimento
3. Atualizar observações
```

---

## 💡 Dicas de Uso

### Mensagem Inicial Sugerida:
```
Olá! Vi que você tem [NEGÓCIO] no Google Maps com ótimas avaliações! 🌟

Notei que ainda não tem um site próprio. Ajudo empresas como a sua a ter presença digital profissional e atrair mais clientes online.

Posso enviar alguns exemplos do meu trabalho?
```

### Follow-up (após 2-3 dias):
```
Olá novamente! 👋

Enviei uma mensagem outro dia sobre criar um site para [NEGÓCIO].

Ainda está interessado(a)? Tenho uma promoção especial esta semana!
```

---

## 🎨 Interface

### Dashboard Principal
- **Estatísticas**: 4 cards com números em tempo real
- **Filtros**: Cidade, Nicho e Status
- **Busca**: Pesquisa instantânea
- **Ações**: Importar, Exportar, Limpar

### Card do Lead
Cada lead mostra:
- 📛 Nome da empresa
- 🎯 Nicho
- 🏙️ Cidade
- 📞 Telefone
- 💬 WhatsApp (clicável)
- 📍 Endereço
- ⭐ Avaliação
- 📝 Observações
- 🔵 Status colorido

### Botões de Ação
- **💬 Enviar WhatsApp**: Abre conversa direta
- **✏️ Editar**: Atualiza status/observações
- **🗑️ Deletar**: Remove o lead

---

## 📱 Responsivo

O aplicativo funciona perfeitamente em:
- 💻 Desktop
- 📱 Tablet
- 📱 Celular

---

## 🔒 Segurança e Privacidade

- ✅ Dados armazenados localmente (seu navegador)
- ✅ Nada é enviado para servidores externos
- ✅ Você controla 100% dos seus dados
- ✅ Exportação fácil para backup

---

## ⚙️ Funcionalidades Avançadas

### Exportar Dados
- Clique em "💾 Exportar Dados"
- Baixa arquivo Excel com TODOS os leads
- Inclui todas as atualizações e observações
- Útil para backup

### Limpar Dados
- Clique em "🗑️ Limpar Todos os Dados"
- Remove TUDO do navegador
- Útil para recomeçar do zero
- ⚠️ Ação irreversível!

---

## 🎯 Exemplos de Uso

### Caso 1: Primeiro Dia
```
→ Importei 25 leads de "estética" em "Curitiba"
→ Filtrei por "Não Contatado" (25 leads)
→ Contactei os 10 com melhor avaliação
→ Marquei todos como "Contatado"
→ Adicionei observação: "Mensagem enviada 08/12 às 13h"
```

### Caso 2: Follow-up
```
→ Filtrei por "Aguardando Resposta" (10 leads)
→ 3 responderam!!
→ Marquei como "Respondeu"
→ Adicionei observações: "Interessado! Marcar reunião"
→ Os outros 7: Enviei novo follow-up
```

### Caso 3: análise
```
→ Filtrei por "Respondeu" (3 leads)
→ Exportei para Excel
→ Planejei próximos passos
→ Faturamento garantido! 🎉
```

---

## 🚀 Produtividade

### Antes (sem Lead Manager):
❌ Planilha Excel confusa  
❌ Não sabe quem já contactou  
❌ Perde informações  
❌ Difícil fazer follow-up  

### Depois (com Lead Manager):
✅ Interface visual clara  
✅ Status de cada lead  
✅ Observações organizadas  
✅ Follow-up sistemático  
✅ WhatsApp com 1 clique  

---

## 📊 Estatísticas Típicas

Com uso consistente, espere:
- **Taxa de resposta**: 20-30%
- **Conversão**: 10-15%
- **Tempo economizado**: 70%

---

## 🎉 Você Está Pronto!

Abra o `index.html` e comece a gerenciar seus leads profissionalmente!

**Boa
 prospecção!** 🚀💼
