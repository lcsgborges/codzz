#!/usr/bin/env bash
set -euo pipefail

NOME_CONTAINER="uazapi-paircode"
PORTA_HOST="${PORTA_HOST:-5000}"
PORTA_CONTAINER="${PORTA_CONTAINER:-5000}"
ARQUIVO_ENV="${ARQUIVO_ENV:-.env}"

echo "== Deploy: ${NOME_CONTAINER} =="

if ! command -v docker >/dev/null 2>&1; then
  echo "Erro: Docker não está instalado ou não está no PATH."
  exit 1
fi

if [ ! -f "${ARQUIVO_ENV}" ]; then
  echo "Erro: arquivo ${ARQUIVO_ENV} não encontrado na pasta atual."
  echo "Crie o .env (ou defina ARQUIVO_ENV=... antes de rodar)."
  exit 1
fi

if [ ! -f "Dockerfile" ]; then
  echo "Erro: Dockerfile não encontrado na pasta atual."
  exit 1
fi

echo "Parando/removendo container antigo (se existir)..."
if docker ps -a --format '{{.Names}}' | grep -qx "${NOME_CONTAINER}"; then
  docker stop "${NOME_CONTAINER}" >/dev/null || true
  docker rm "${NOME_CONTAINER}" >/dev/null || true
fi

echo "Buildando imagem..."
docker build -t "${NOME_CONTAINER}:latest" .

echo "Subindo container..."
docker run -d \
  --name "${NOME_CONTAINER}" \
  --restart unless-stopped \
  -p "${PORTA_HOST}:${PORTA_CONTAINER}" \
  --env-file "${ARQUIVO_ENV}" \
  "${NOME_CONTAINER}:latest" >/dev/null

echo "Container no ar!"
echo "Acesse: http://IP_DA_SUA_VPS:${PORTA_HOST}"
echo ""
echo "Logs (Ctrl+C para sair):"
docker logs -f "${NOME_CONTAINER}"
