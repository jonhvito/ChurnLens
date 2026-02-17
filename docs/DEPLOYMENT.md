# Deployment Guide - Homelab

## Configuração Inicial no Homelab

### 1. Clonar o repositório no homelab

```bash
cd /opt  # ou onde você quiser manter seus projetos
git clone https://github.com/jonhvito/ChurnLens.git
cd ChurnLens
```

### 2. Configurar variáveis de ambiente

```bash
# Copiar template
cp .env.example .env

# Editar e adicionar seu token
nano .env
```

Adicionar:
```env
CLOUDFLARE_TUNNEL_TOKEN=seu_token_cloudflare_aqui
```

### 3. Configurar Self-hosted Runner (se ainda não tiver)

#### Baixar e instalar runner:
```bash
# Criar diretório para o runner
mkdir -p ~/actions-runner && cd ~/actions-runner

# Baixar runner (substituir pela versão mais recente)
curl -o actions-runner-linux-x64-2.314.1.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.314.1/actions-runner-linux-x64-2.314.1.tar.gz

# Extrair
tar xzf ./actions-runner-linux-x64-2.314.1.tar.gz
```

#### Configurar runner:
```bash
# Configurar (você vai precisar do token do GitHub)
./config.sh --url https://github.com/seu-usuario/ChurnLens --token SEU_TOKEN_AQUI

# Quando perguntar tags, adicione: self-hosted,linux
```

#### Instalar como serviço:
```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

#### Verificar status:
```bash
sudo ./svc.sh status
```

### 4. Adicionar usuário do runner ao grupo Docker

```bash
# Descobrir qual usuário está rodando o runner
ps aux | grep actions-runner

# Adicionar ao grupo docker (substitua 'usuario' pelo nome correto)
sudo usermod -aG docker usuario

# Aplicar mudanças sem precisar relogar
newgrp docker

# Ou reiniciar o serviço do runner
sudo ./svc.sh restart
```

### 5. Testar deploy manual

```bash
cd /opt/ChurnLens  # ou onde você clonou
docker compose build
docker compose up -d
docker compose ps
```

### 6. Fazer primeiro commit para testar CI/CD

```bash
# No seu computador de desenvolvimento
git add .
git commit -m "test: configuração inicial do CI/CD"
git push origin main
```

## Comandos Úteis no Homelab

### Gerenciar aplicação:
```bash
# Ver logs
docker compose logs -f

# Reiniciar
docker compose restart

# Parar
docker compose down

# Ver status
docker compose ps

# Ver uso de recursos
docker stats churnlens-churnlens-1
```

### Gerenciar runner:
```bash
cd ~/actions-runner

# Status
sudo ./svc.sh status

# Restart
sudo ./svc.sh restart

# Stop
sudo ./svc.sh stop

# Ver logs do runner
journalctl -u actions.runner.* -f
```

### Atualizar aplicação manualmente:
```bash
cd /opt/ChurnLens
git pull
docker compose build
docker compose up -d
```

## Estrutura no Homelab

```
/opt/ChurnLens/              # Código da aplicação
├── .env                     # Variáveis de ambiente (não vai pro Git)
├── docker-compose.yml       # Configuração do container
├── Dockerfile              # Imagem Docker
└── ...

~/actions-runner/            # GitHub Actions Runner
├── config.sh
├── run.sh
└── svc.sh
```

## Troubleshooting

### Runner não aparece no GitHub:
1. Verificar se está rodando: `sudo ./svc.sh status`
2. Ver logs: `journalctl -u actions.runner.* -f`
3. Reconfigurar se necessário

### Deploy falha:
1. Ver logs no GitHub Actions
2. SSH no homelab e verificar: `docker compose logs`
3. Verificar se `.env` existe e tem o token

### Container não inicia:
1. Verificar logs: `docker compose logs`
2. Verificar se porta 5000 está livre: `sudo lsof -i :5000`
3. Verificar permissões do Docker
