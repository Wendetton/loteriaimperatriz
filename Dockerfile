# Use Python 3.11 slim como base
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expor porta
EXPOSE 5000

# Comando para executar a aplicação
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

