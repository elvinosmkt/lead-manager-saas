#!/bin/bash

echo "🎯 Instalando Google Maps Lead Scraper..."
echo ""

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale o Python 3.8 ou superior."
    exit 1
fi

echo "✓ Python encontrado"

# Instala as dependências
echo "📦 Instalando dependências Python..."
pip3 install -r requirements.txt

# Instala o Playwright
echo "🎭 Instalando Playwright..."
python3 -m playwright install chromium

# Cria o diretório de resultados
mkdir -p resultados

echo ""
echo "✅ Instalação concluída!"
echo ""
echo "Para usar o scraper, execute:"
echo "  python3 scraper.py"
echo ""
