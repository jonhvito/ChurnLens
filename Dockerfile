# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependências em uma camada separada
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

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

# Mudar para usuário não-root
USER appuser

# Garantir que scripts do pip estejam no PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Expor a porta
EXPOSE 5000

# Rodar aplicação
CMD ["python", "run.py"]
