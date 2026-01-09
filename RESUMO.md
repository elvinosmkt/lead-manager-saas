# 🎯 GOOGLE MAPS LEAD SCRAPER
## Automação para Prospecção de Clientes sem Website

---

## ✅ STATUS: FUNCIONANDO PERFEITAMENTE!

**Teste realizado com sucesso:**
- 🎯 Nicho: Estética
- 📍 Local: Curitiba, PR
- ✅ 27 empresas coletadas
- 🏆 1 lead qualificado (sem site + com WhatsApp)
- 📊 Planilha Excel gerada

---

## 🚀 INÍCIO RÁPIDO

```bash
# 1. Entre na pasta
cd lead-scraper

# 2. Execute (já está instalado!)
python3 scraper_completo.py

# 3. Digite nicho e cidade quando solicitado
```

**Resultado**: Planilha Excel em `resultados/` com todas as empresas

---

## 📁 ARQUIVOS PRINCIPAIS

### Para Você Usar:
- **`scraper_completo.py`** ⭐ - Coleta TODAS as empresas (recomendado)
- **`scraper_selenium.py`** 🎯 - Apenas leads sem site
- **`config.py`** ⚙️ - Configurações (velocidade, limites, etc)

### Documentação:
- **`README.md`** 📖 - Documentação completa
- **`GUIA_RAPIDO.md`** ⚡ - Guia de 3 passos

### Suporte:
- **`requirements.txt`** - Dependências
- **`install.sh`** - Script de instalação

---

## 💡 COMO FUNCIONA

1. **Você escolhe** um nicho (ex: "estética") e cidade (ex: "Curitiba, PR")
2. **O script**: 
   - Abre o Google Maps
   - Busca empresas
   - Extrai dados (nome, telefone, WhatsApp, endereço, avaliação)
   - Identifica quais têm/não têm site
3. **Você recebe** uma planilha Excel pronta para usar

---

## 📊 O QUE VOCÊ RECEBE

### Dados Coletados:
- ✅ Nome da empresa
- ✅ Tem site? (Sim/Não)  
- ✅ Tem WhatsApp? (Sim/Não)
- ✅ Telefone
- ✅ WhatsApp (formatado com +55)
- ✅ Endereço completo
- ✅ Avaliação (estrelas)
- ✅ Número de avaliações

### Formato:
Planilha Excel (.xlsx) salva em `resultados/`

---

## 🎯 CASOS DE USO

### 1. Prospecção para Web Design
Busque empresas sem site para oferecer criação de websites

### 2. Análise de Mercado
Veja quantas empresas do nicho têm ou não site

### 3. Base de Leads
Gere listas de prospects por cidade e nicho

---

## ⭐ NICHOS TESTADOS

- ✅ Estética (funciona!)
- Salão de beleza
- Barbearia
- Clínica odontológica
- Academia
- Restaurante
- Pet shop
- Manicure

---

## 💻 REQUISITOS

- ✅ Python 3.9+
- ✅ Google Chrome
- ✅ Conexão com internet
- ✅ Cerca de 2-5 minutos por busca

---

## 📞 PRÓXIMOS PASSOS

1. Execute o script
2. Abra a planilha gerada
3. Filtre por "tem_site = Não"
4. Copie os WhatsApps
5. Comece a prospectar! 🚀

---

## 🌟 FEATURES

- ✅ Interface em português
- ✅ Mensagens claras de progresso
- ✅ Tratamento de erros
- ✅ Configurações ajustáveis
- ✅ Excel formatado e organizado
- ✅ Estatísticas ao final
- ✅ Dois modos (filtrado e completo)

---

## 📝 CONFIGURAÇÕES (config.py)

```python
"MAX_BUSINESSES": 100,    # Máximo de empresas
"HEADLESS": False,        # Mostra navegador
"DELAY_BETWEEN_BUSINESSES": 1,  # Velocidade
```

---

**Ver documentação completa**: `README.md`  
**Guia rápido**: `GUIA_RAPIDO.md`

🎉 **Boa prospecção!**
