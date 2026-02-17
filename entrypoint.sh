#!/bin/bash
set -e

# Iniciar cloudflared em background se o token estiver definido
if [ -n "$CLOUDFLARE_TUNNEL_TOKEN" ]; then
    echo "🌐 Iniciando Cloudflare Tunnel..."
    cloudflared tunnel run --token "$CLOUDFLARE_TUNNEL_TOKEN" &
fi

# Iniciar a aplicação Flask
echo "🚀 Iniciando ChurnLens..."
exec python run.py
