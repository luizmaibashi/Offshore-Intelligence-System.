# Use a imagem base oficial do Python
# Pinada por digest 2026-08-29 (ADR-0005) — revisar a cada 6 meses ou em CVE alta/critica
# divulgada para python:3.11-slim (https://hub.docker.com/_/python)
FROM python:3.11-slim@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6

# Evita que o Python gere arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para algumas bibliotecas de data science
# software-properties-common removido (2026-08-29): não usado por nenhum script do repo
# (nenhum add-apt-repository) e ausente do repo default do Debian 13/trixie, que quebrava o
# build após o pin de digest do ADR-0005 — achado ao testar, não efeito do pin em si.
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
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

# Usuário não-root (ADR-0005) — dashboard.py escreve em data/processed/ em runtime,
# chown precisa cobrir isso antes de trocar de usuário
RUN useradd --create-home --shell /bin/bash oisuser \
    && chown -R oisuser:oisuser /app
USER oisuser

# Expõe a porta padrão do Streamlit
EXPOSE 8501

# Adiciona um healthcheck para monitorar o status da aplicação
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Comando para rodar a aplicação
ENTRYPOINT ["streamlit", "run", "app/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
