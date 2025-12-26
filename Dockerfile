FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências de sistema (opcional, mas ajuda com builds / SSL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Instala deps primeiro (cache)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia o app
COPY . /app

# FastAPI vai servir templates e arquivos do projeto
EXPOSE 8000

# Produção: sem reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
