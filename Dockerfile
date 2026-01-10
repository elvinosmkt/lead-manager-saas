# Force Rebuild - Clean Python+Selenium setup
FROM python:3.10-slim

# Instala dependências do sistema e Chromium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Configura diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala dependências Python (apenas o necessário)
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta
EXPOSE 5001

# Define variáveis de ambiente para Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Comando de inicialização
CMD ["python", "start_app.py"]
