# 🎯 Google Maps Lead Scraper - AUTOMAÇÃO COMPLETA

Automação para encontrar empresas no Google Maps, com foco em identificar empresas **sem site** e **com WhatsApp** para oferecer serviços de criação de websites.

## ✅ Status: FUNCIONANDO!

**Teste realizado**: Estética em Curitiba, PR
- ✅ 27 empresas coletadas
- ✅ 1 lead qualificado (sem site + com WhatsApp)
- ✅ Planilha Excel gerada com sucesso

---

## 📦 O que foi criado

### 1. **scraper_selenium.py** (⭐ RECOMENDADO)
Script principal usando Selenium (mais estável):
- Busca empresas no Google Maps
- Filtra empresas **SEM site** e **COM WhatsApp**
- Gera planilha com leads qualificados

### 2. **scraper_completo.py** (📊 ANÁLISE COMPLETA)
Coleta **TODAS** as empresas e marca quais têm/não têm site:
- Útil para ter visão completa do mercado
- Mostra estatísticas detalhadas
- Permite filtros posteriores no Excel

### 3. **scraper.py** (⚠️ Alternativo - Playwright)
Versão com Playwright (pode ter problemas de estabilidade)

---

## 🚀 Como Usar

### Instalação (Uma Vez Apenas)

```bash
cd /Users/alexandrebenitescorrea/.gemini/antigravity/playground/core-plasma/lead-scraper

# Instalar dependências
pip3 install selenium==4.15.2 webdriver-manager==4.0.1 pandas==2.1.4 openpyxl==3.1.2
```

### Uso Modo 1: Apenas Leads Qualificados

```bash
python3 scraper_selenium.py
```

Quando executar, digite:
- **Nicho**: `estética`, `salão de beleza`, `barbearia`, etc
- **Cidade**: `Curitiba, PR`, `São Paulo, SP`, etc

**Resultado**: Planilha com empresas que **NÃO têm site** e **TÊM WhatsApp**

### Uso Modo 2: Todas as Empresas (Análise Completa)

```bash
python3 scraper_completo.py
```

**Resultado**: Planilha com TODAS as empresas + colunas indicando:  
- `tem_site`: Sim/Não
- `tem_whatsapp`: Sim/Não

Você pode filtrar no Excel depois!

---

## 📊 Estrutura da Planilha

### Modo 1 (Leads Qualificados):
| Nome | Telefone | WhatsApp | Endereço | Avaliação | Num Avaliações |
|------|----------|----------|----------|-----------|----------------|
| Studio XYZ | (41) 98765-4321 | 5541987654321 | Rua ABC, 123 | 4.8 | 127 |

### Modo 2 (Todas Empresas):
| Nome | Tem Site | Tem WhatsApp | Telefone | WhatsApp | Endereço | Avaliação |
|------|----------|--------------|----------|----------|----------|-----------|
| Clínica Premium | Sim | Sim | (41) 3333-4444 | 554133334444 | Av. XYZ | 4.9 |
| Studio ABC | Não | Sim | (41) 98765-4321 | 5541987654321 | Rua 123 | 4.7 |

---

## ⚙️ Configurações (config.py)

```python
CONFIG = {
    "DELAY_BETWEEN_SCROLLS": 2,      # Tempo entre scrolls (segundos)
    "DELAY_BETWEEN_BUSINESSES": 1,    # Tempo entre empresas (segundos)
    "MAX_BUSINESSES": 100,            # Máximo de empresas a processar
    "HEADLESS": False,                # False = mostra navegador
}
```

**Dica**: Manter `HEADLESS = False` para ver o que está acontecendo!

---

## 💡 Casos de Uso

### 1. **Prospecção Ativa**
```bash
python3 scraper_selenium.py
# Digite: "estética" em "Curitiba, PR"
# Resultado: Apenas leads sem site (prontos para contato!)
```

### 2. **Análise de Mercado**
```bash
python3 scraper_completo.py
# Digite: "salão de beleza" em "São Paulo, SP"
# Resultado: Todas as empresas + filtros para análise
```

### 3. **Múltiplas Cidades**
Execute várias vezes com cidades diferentes:
- Curitiba, PR
- São Paulo, SP
- Rio de Janeiro, RJ
- Florianópolis, SC

---

## 📝 Exemplo Real de Uso

### Teste Realizado:
```
📌 Nicho: estética
📍 Cidade: Curitiba, PR

Resultado:
✅ 27 empresas coletadas
🔍 1 empresa sem website
💬 27 empresas com WhatsApp
🎯 1 lead qualificado

Arquivo: resultados/todas_empresas_estética_Curitiba_PR_20251208_123833.xlsx
```

---

## 🎯 Próximos Passos Após Gerar a Planilha

1. **Abra o Excel** e ordene por avaliação (maiores primeiro)
2. **Copie os números de WhatsApp**
3. **Crie uma mensagem personalizada**:
   ```
   Olá! Vi que vocês têm um negócio incrível no Google Maps 
   com ótimas avaliações. Notei que vocês ainda não têm um site.
   Ajudo empresas como a sua a ter presença digital e atrair 
   mais clientes. Posso enviar alguns exemplos?
   ```
4. **Comece a prospectar!** 🚀

---

## ⚠️ Limitações e Dicas

### Limitações:
- Depende da estrutura do Google Maps (pode mudar)
- Algumas empresas podem não ter todos os dados preenchidos
- O Google pode limitar buscas se fizer muitas seguidas

### Dicas:
1. **Não faça muitas buscas seguidas** - aguarde alguns minutos entre execuções
2. **Varie os nichos e cidades** - não repita a mesma busca várias vezes
3. **Comece com poucos resultados** - ajuste `MAX_BUSINESSES` para 20-30 inicialmente
4.**Use o modo "completo"** para ter mais dados e fazer filtros personalizados

---

## 🛠️ Troubleshooting

### Erro "ChromeDriver não encontrado":
```bash
pip3 install --upgradewebdriver-manager
```

### Script muito lento:
- Aumente `DELAY_BETWEEN_BUSINESSES` em `config.py`
- Reduza `MAX_BUSINESSES` para menos empresas

### Nenhuma empresa encontrada:
- Verifique se o nicho existe naquela cidade
- Tente nichos mais amplos ("beleza" ao invés de "micropigmentação")
- Confirme que a cidade está correta ("Cidade, UF")

### Navegador não abre:
- Defina `HEADLESS = False` em `config.py`
- Verifique se o Chrome está instalado

---

## 📂 Estrutura do Projeto

```
lead-scraper/
├── config.py                    # Configurações
├── scraper_selenium.py          # ⭐ Principal (apenas leads)
├── scraper_completo.py          # 📊 Análise completa
├── scraper.py                   # Playwright (alternativo)
├── requirements.txt             # Dependências
├── install.sh                   # Script de instalação
├── README.md                    # Esta documentação
└── resultados/                  # Planilhas geradas aqui
    └── *.xlsx
```

---

## 🎉 Você Está Pronto!

Execute agora:
```bash
python3 scraper_completo.py
```

**Nicho sugeridos para testar**:
- estética
- salão de beleza  
- barbearia
- clínica odontológica
- academia
- restaurante
- lanchonete
- pet shop

**Boa prospecção!** 🚀💼
