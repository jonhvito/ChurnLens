# GitHub Actions - CI/CD

## Workflow: Deploy to Homelab

Deploys automático da aplicação ChurnLens no homelab quando há push na branch `main`.

### Pré-requisitos no Homelab

1. **Self-hosted Runner configurado**
   - Instalado e rodando no homelab
   - Conectado ao repositório GitHub
   - Com acesso ao Docker e Docker Compose

2. **Arquivo `.env` configurado**
   - Criar arquivo `.env` no homelab com:
   ```bash
   CLOUDFLARE_TUNNEL_TOKEN=seu_token_aqui
   ```

3. **Permissões necessárias**
   - O runner deve ter permissão para executar `docker` sem sudo
   - Adicionar usuário do runner ao grupo docker:
   ```bash
   sudo usermod -aG docker nome_do_usuario_runner
   ```

### Como funciona

1. **Trigger:** Push na branch `main` ou execução manual
2. **Checkout:** Baixa o código mais recente
3. **Stop:** Para containers antigos
4. **Build:** Constrói nova imagem Docker
5. **Deploy:** Sobe a aplicação
6. **Verify:** Verifica status e logs
7. **Cleanup:** Remove imagens antigas

### Execução Manual

Você pode executar o deploy manualmente via GitHub Actions tab:
- Vá em "Actions" → "Deploy to Homelab" → "Run workflow"

### Monitoramento

Acesse a aba "Actions" no GitHub para ver:
- Status do deploy
- Logs completos
- Tempo de execução
- Erros (se houver)

### Troubleshooting

**Runner não conecta:**
- Verificar se o serviço do runner está ativo: `sudo systemctl status actions.runner.*`
- Restartar runner: `sudo systemctl restart actions.runner.*`

**Erro de permissão do Docker:**
- Verificar se usuário está no grupo docker: `groups`
- Relogar após adicionar ao grupo ou: `newgrp docker`

**Build falha:**
- Verificar logs no Actions
- SSH no homelab e rodar manualmente: `docker compose build`

**Container não sobe:**
- Verificar arquivo `.env` no homelab
- Verificar logs: `docker compose logs`
