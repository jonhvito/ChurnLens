# Quick Start Guide - ChurnLens

## 🚀 Início Rápido (3 passos)

### 1. Instalar Dependências
```bash
cd churnlens
pip install -r requirements.txt
```

### 2. Verificar Dados
Certifique-se de que os CSVs estão em `../data/`:
```bash
ls -la ../data/*.csv
```

Deve mostrar:
- `olist_customers_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_order_payments_dataset.csv`

### 3. Rodar Aplicação
```bash
python run.py
```

Acesse: **http://localhost:5000**

---

## 🧪 Rodar Testes

```bash
# Instalar pytest (se necessário)
pip install pytest

# Rodar testes
pytest tests/ -v
```

Deve mostrar: **6 passed**

---

## ⚙️ Configuração Avançada

### Variáveis de Ambiente

Crie arquivo `.env` (opcional):
```bash
# .env
CHURN_THRESHOLD_DAYS=270
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
CACHE_ENABLED=True
```

Ou exporte diretamente:
```bash
export CHURN_THRESHOLD_DAYS=180
export FLASK_DEBUG=False
python run.py
```

---

## 📊 Endpoints Disponíveis

### Web (Browser)
- http://localhost:5000 - Dashboard principal
- http://localhost:5000/health - Health check

### API (JSON)
- http://localhost:5000/api/summary - KPIs
- http://localhost:5000/api/churn_by_rfm - Churn por RFM
- http://localhost:5000/api/recency_hist - Histograma
- http://localhost:5000/api/top_risk - Top 50 clientes

### Export (CSV)
- http://localhost:5000/export/customers.csv - Todas features
- http://localhost:5000/export/top_risk.csv - Top 50

---

## 🐛 Troubleshooting

### Erro: "File not found"
```bash
# Verifique se está no diretório correto
pwd  # Deve terminar em /churnlens

# Verifique se dados existem
ls -la ../data/
```

### Erro: "Module not found"
```bash
# Reinstale dependências
pip install -r requirements.txt

# Ou instale manualmente
pip install flask pandas
```

### Porta 5000 já em uso
```bash
# Use outra porta
export FLASK_PORT=8000
python run.py
```

### Cache desatualizado
```bash
# Desabilite cache temporariamente
export CACHE_ENABLED=False
python run.py
```

---

## 🔄 Desenvolvimento

### Hot Reload (já habilitado em DEBUG=True)
```bash
# Edite qualquer arquivo Python
# O servidor reinicia automaticamente
```

### Adicionar Nova Feature

1. **Core logic** em `app/core/pipeline.py`:
```python
def compute_new_feature(df: pd.DataFrame) -> pd.DataFrame:
    """Nova feature."""
    df = df.copy()
    df["new_col"] = ...
    return df
```

2. **Teste** em `tests/test_pipeline.py`:
```python
def test_new_feature():
    assert ...
```

3. **Expor no service** em `app/services/data_service.py`:
```python
def get_new_data(self):
    features, _ = self.get_features()
    return features["new_col"].to_dict()
```

4. **API endpoint** em `app/api.py`:
```python
@api.route("/new_endpoint")
def new_endpoint():
    return jsonify(data_service.get_new_data())
```

---

## 📦 Deployment

### Opção 1: Gunicorn (Produção)
```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

### Opção 2: Docker
```dockerfile
# Dockerfile (criar)
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app()"]
```

```bash
docker build -t churnlens .
docker run -p 5000:5000 -v $(pwd)/../data:/app/data churnlens
```

---

## 📚 Estrutura do Projeto

```
churnlens/
├── run.py              # 👈 PONTO DE ENTRADA
├── requirements.txt    # Dependências
├── README.md          # Documentação completa
├── app/
│   ├── __init__.py    # Flask factory
│   ├── config.py      # Configurações
│   ├── web.py         # Rotas HTML
│   ├── api.py         # Rotas JSON
│   ├── core/          # ⭐ Lógica pura
│   │   ├── pipeline.py
│   │   ├── validation.py
│   │   └── schemas.py
│   └── services/      # I/O e cache
│       └── data_service.py
├── templates/         # Jinja2 HTML
├── static/            # CSS/JS
└── tests/             # Pytest
```

---

## ✅ Checklist de Verificação

Antes de usar em produção:

- [ ] Testes passando (`pytest`)
- [ ] Dados CSV presentes em `../data/`
- [ ] Dependências instaladas
- [ ] Porta disponível (5000 ou customizada)
- [ ] `FLASK_DEBUG=False` em produção
- [ ] Usar gunicorn ao invés de `python run.py`
- [ ] Considerar proxy reverso (nginx)

---

## 💡 Dicas

1. **Performance**: Cache ativado por padrão, desabilite só se necessário
2. **Logs**: Ative com `export FLASK_DEBUG=True` para ver detalhes
3. **Customização**: Todos os parâmetros estão em `config.py`
4. **Export**: Use `/export/*.csv` para baixar dados processados

---

**Pronto para usar!** 🎉

Qualquer dúvida, consulte [README.md](README.md) ou [MIGRATION.md](MIGRATION.md).
