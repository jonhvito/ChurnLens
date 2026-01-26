# ChurnLens - Análise de Churn para E-commerce 🔍

> **Sistema inteligente de predição de churn** que identifica clientes em risco de abandono usando análise RFM e segmentação comportamental.

## 🎯 Objetivo

ChurnLens é uma aplicação web que analisa o comportamento de compra de clientes de e-commerce para prever quais clientes estão em risco de não retornarem (churn). Usando dados reais do [Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (marketplace brasileiro), o sistema:

- ✅ Calcula métricas RFM (Recência, Frequência, Valor Monetário)
- ✅ Identifica clientes inativos (>270 dias sem comprar)
- ✅ Segmenta clientes em 8 níveis de risco
- ✅ Prioriza ações de retenção nos top 50 clientes em risco
- ✅ Fornece visualizações interativas e exportação de dados

**Caso de Uso:** Times de CRM, Marketing e Customer Success podem usar ChurnLens para:
- Criar campanhas de retenção direcionadas
- Reativar clientes inativos com ofertas personalizadas
- Monitorar a saúde da base de clientes ao longo do tempo
- Priorizar recursos em clientes de alto valor em risco

---

## 📊 O que é RFM?

**RFM** é uma metodologia de segmentação de clientes baseada em três pilares:

| Dimensão | Significado | Interpretação |
|----------|-------------|---------------|
| **R**ecency | Há quantos dias foi a última compra? | Quanto mais recente, melhor |
| **F**requency | Quantas vezes o cliente comprou? | Quanto mais frequente, melhor |
| **M**onetary | Quanto dinheiro o cliente gastou? | Quanto maior o valor, melhor |

Cada dimensão recebe uma **pontuação de 1 a 5** (quintis), onde:
- **Score 5**: Top 20% (melhores clientes)
- **Score 1**: Bottom 20% (piores clientes)

O **RFM Score Final** é a média das três pontuações. Clientes com RFM baixo (1-2) têm alta probabilidade de churn.

### Definição de Churn
Um cliente é considerado **"em churn"** quando: `Recência > 270 dias` (configurável).

---

## 📋 Funcionalidades

- **Dashboard interativo** com KPIs e visualizações
- **Análise RFM** (Recency, Frequency, Monetary)
- **Segmentação de risco** baseada em regras de negócio
- **Exportação de dados** (CSV)
- **API REST** para integração

## 🏗️ Arquitetura

O projeto segue princípios de Clean Code com separação clara de responsabilidades:

```
churnlens/
├── app/
│   ├── core/              # Lógica de negócio pura (sem I/O)
│   │   ├── pipeline.py    # Funções do pipeline de análise
│   │   ├── validation.py  # Validação de dados
│   │   └── schemas.py     # Estruturas de dados
│   ├── services/
│   │   └── data_service.py # Carregamento e cache
│   ├── web.py             # Rotas web (templates)
│   ├── api.py             # Rotas API (JSON)
│   └── config.py          # Configurações
├── templates/             # Templates Jinja2
├── static/                # Assets (CSS, JS)
├── tests/                 # Testes unitários
└── data/                  # Datasets CSV (fixos)
```

### Princípios de Design

1. **Funções puras no core**: `pipeline.py` não faz I/O, apenas transformações de DataFrames
2. **Separação de concerns**: service layer gerencia I/O e cache, core foca em lógica
3. **Configuração centralizada**: todos os parâmetros em `config.py` com override por env vars
4. **Templates burros**: apenas renderização, sem lógica de negócio
5. **API desacoplada**: frontend consome dados via fetch/JSON

## 🚀 Como Executar

### Pré-requisitos

- Python 3.9+
- pip

### Instalação

1. **Navegue até o diretório do projeto:**

```bash
cd ChurnLens
```

2. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

3. **Os dados já devem estar em `data/`:**

```
ChurnLens/
├── app/                # Aplicação Flask
├── data/               # Datasets
│   ├── olist_customers_dataset.csv
│   ├── olist_orders_dataset.csv
│   └── olist_order_payments_dataset.csv
├── templates/          # Templates HTML
├── static/             # CSS e JavaScript
└── run.py              # Entrypoint
```

### Execução

```bash
python run.py
```

Acesse: **http://localhost:5000**

### Variáveis de Ambiente (opcional)

```bash
export CHURN_THRESHOLD_DAYS=270    # Dias para considerar churn
export FLASK_DEBUG=True            # Modo debug
export FLASK_HOST=0.0.0.0          # Host
export FLASK_PORT=5000             # Porta
export CACHE_ENABLED=True          # Cache de resultados
```

## 📊 Metodologia

### Pipeline de Análise

1. **Carregamento**: Lê CSVs de customers, orders e payments
2. **Limpeza**: Remove nulls, duplicatas, valores inválidos
3. **Join**: Combina datasets por customer_id e order_id
4. **Features**: Calcula métricas RFM por cliente
   - **Recency**: dias desde última compra
   - **Frequency**: número de pedidos
   - **Monetary**: receita total do cliente
   - **Tenure**: dias desde primeira compra
   - **Avg Ticket**: ticket médio
5. **Churn Label**: Clientes com recency ≥ 270 dias = churn
6. **RFM Scores**: Quintis (1-5) para R, F, M
7. **Risk Segments**: Segmentação por regras

### Definição de Churn

- **Threshold padrão**: 270 dias de inatividade
- **Baseado em**: Análise do dataset Olist (última compra em ago/2018)
- **Configurável**: Ajuste via `CHURN_THRESHOLD_DAYS`

### Segmentação de Risco

**Importante**: Os segmentos de risco são **regras operacionais** baseadas em recency e valor, **não clustering ou ML**.

| Segmento | Critério |
|----------|----------|
| Risco muito alto | Recency ≥ 450 dias |
| Churn (prioritário) | Recency ≥ 270 dias + (Monetary ou Frequency no top 20%) |
| Churn | Recency ≥ 270 dias |
| Risco alto (prioritário) | 180 ≤ Recency < 270 + alto valor |
| Risco alto | 180 ≤ Recency < 270 |
| Risco médio | 90 ≤ Recency < 180 |
| Risco baixo | Recency < 90 dias |

## 🔗 Endpoints

### Web (HTML)

- `GET /` - Dashboard principal
- `GET /health` - Health check

### API (JSON)

- `GET /api/summary` - KPIs gerais
- `GET /api/churn_by_rfm` - Churn rate por RFM score
- `GET /api/recency_hist` - Histograma de recency
- `GET /api/risk_summary` - Resumo por segmento de risco
- `GET /api/top_risk` - Top 50 clientes em risco

### Export (CSV)

- `GET /export/customers.csv` - Todas as features de clientes
- `GET /export/top_risk.csv` - Top 50 clientes em risco

## 🧪 Testes

```bash
# Instalar pytest
pip install pytest

# Rodar testes
pytest tests/
```

### Testes Implementados

- ✅ Churn label aplicado corretamente (threshold 270)
- ✅ RFM scores no range válido (1-5)
- ✅ Sem valores monetários negativos
- ✅ Limpeza de dados remove inválidos
- ✅ Agregação de pagamentos soma corretamente
- ✅ qcut_safe lida com duplicatas

## 📈 Métricas Atuais (Dataset Olist)

```
Data de referência: 2018-08-29
Total de clientes: ~93.358
Taxa de Churn: ~39,36%
Receita Total: ~R$ 15,4M
```

## 🛠️ Tecnologias

- **Backend**: Flask, Pandas
- **Frontend**: Tailwind CSS, Chart.js, Vanilla JS
- **Testes**: Pytest

## ⚠️ Limitações Conhecidas

1. **Dataset fixo**: Dados de 2018, não há atualização automática
2. **Carga em memória**: Não otimizado para datasets muito grandes (>1M linhas)
3. **Sem autenticação**: Aplicação pública, sem controle de acesso
4. **Sem persistência**: Resultados em memória (perde ao reiniciar)
5. **Status fixo**: Apenas pedidos "delivered" são considerados

## 🔮 Melhorias Futuras

- [ ] Upload de CSV customizados
- [ ] Persistência em banco de dados
- [ ] ML model para predição de churn
- [ ] Análise de coorte e sazonalidade
- [ ] Autenticação e multi-tenancy
- [ ] Dashboard de métricas temporais
- [ ] Recomendações de ação por segmento

## 📚 Dataset

**Fonte**: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

Dataset público de e-commerce brasileiro com 100k pedidos (2016-2018).

## 📝 Licença

Projeto educacional - livre para uso e modificação.

## 👨‍💻 Desenvolvimento

### Estrutura de Código

- **Funções puras em `core/`**: Sem side effects, fáceis de testar
- **Service layer**: Gerencia I/O e estado (cache)
- **Blueprints Flask**: Rotas organizadas por responsabilidade
- **Templates Jinja**: Separação clara de apresentação
- **Config centralizada**: Fácil customização

### Adicionando Novas Features

1. Adicione função pura em `core/pipeline.py`
2. Teste em `tests/test_pipeline.py`
3. Exponha via `data_service.py`
4. Crie rota em `api.py` ou `web.py`
5. Atualize frontend em `templates/` ou `static/js/`

---

**Desenvolvido com Flask e Clean Code principles** 🚀
