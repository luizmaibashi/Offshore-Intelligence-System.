# Use a imagem base oficial do Python
FROM python:3.11-slim

# Evita que o Python gere arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para algumas bibliotecas de data science
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas o requirements primeiro para aproveitar o cache das camadas do Docker
COPY requirements.txt .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código do projeto
COPY . .

# Instala o pacote core do OIS em modo editável (conforme o Manual Operacional)
RUN pip install -e .

# Expõe a porta padrão do Streamlit
EXPOSE 8501

# Adiciona um healthcheck para monitorar o status da aplicação
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Comando para rodar a aplicação
ENTRYPOINT ["streamlit", "run", "app/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
