# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependências em uma camada separada
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Instalar cloudflared
RUN apt-get update && \
    apt-get install -y wget && \
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && \
    dpkg -i cloudflared-linux-amd64.deb && \
    rm cloudflared-linux-amd64.deb && \
    apt-get remove -y wget && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Criar usuário não-root primeiro
RUN useradd -m -u 1000 appuser

# Copiar dependências para o diretório do appuser
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copiar apenas o necessário da aplicação
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser data/ ./data/
COPY --chown=appuser:appuser static/ ./static/
COPY --chown=appuser:appuser templates/ ./templates/
COPY --chown=appuser:appuser run.py .
COPY --chown=appuser:appuser entrypoint.sh .

# Dar permissão de execução ao entrypoint
RUN chmod +x entrypoint.sh

# Mudar para usuário não-root
USER appuser

# Garantir que scripts do pip estejam no PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Expor a porta
EXPOSE 5000

# Rodar aplicação via entrypoint
CMD ["./entrypoint.sh"]
