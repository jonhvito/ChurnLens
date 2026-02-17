# Guia de Migração: app.py → ChurnLens Flask

Este documento explica como o código monolítico foi refatorado para a aplicação Flask.

## 📊 Visão Geral da Refatoração

### Antes (app.py - 163 linhas)
- ✗ Tudo em um arquivo
- ✗ Código executado no import
- ✗ Prints diretos no console
- ✗ Sem separação de responsabilidades
- ✗ Difícil de testar

### Depois (churnlens/ - estrutura modular)
- ✓ Separação clara de responsabilidades
- ✓ Funções puras testáveis
- ✓ Interface web + API REST
- ✓ Configuração centralizada
- ✓ Testes automatizados

## 🗂️ Mapeamento de Código

### Configurações
**Antes** (app.py, linhas 6-11):
```python
PATH_CUSTOMERS = "./data/olist_customers_dataset.csv"
PATH_ORDERS    = "./data/olist_orders_dataset.csv"
PATH_PAYMENTS  = "./data/olist_order_payments_dataset.csv"
CHURN_THRESHOLD_DAYS = 270
VALID_STATUS = {"delivered"}
```

**Depois** → `app/config.py`:
```python
PATH_CUSTOMERS = str(DATA_DIR / "olist_customers_dataset.csv")
PATH_ORDERS = str(DATA_DIR / "olist_orders_dataset.csv")
PATH_PAYMENTS = str(DATA_DIR / "olist_order_payments_dataset.csv")
CHURN_THRESHOLD_DAYS = int(os.getenv("CHURN_THRESHOLD_DAYS", "270"))
VALID_STATUS = {"delivered"}
```

**Benefícios:**
- ✓ Configurável por variáveis de ambiente
- ✓ Paths absolutos via Path
- ✓ Centralizado em um único lugar

---

### Carregamento de Dados
**Antes** (app.py, linhas 14-24):
```python
customers = pd.read_csv(PATH_CUSTOMERS, dtype={...})
orders = pd.read_csv(PATH_ORDERS, dtype={...}, parse_dates=[...])
payments = pd.read_csv(PATH_PAYMENTS, dtype={...})
```

**Depois** → `app/services/data_service.py` método `load_raw_data()`:
```python
def load_raw_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    try:
        customers = pd.read_csv(config.PATH_CUSTOMERS, dtype={...})
        # ... similar para orders e payments
        validation.validate_datasets(customers, orders, payments)
        return customers, orders, payments
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {e}")
```

**Benefícios:**
- ✓ Tratamento de erros explícito
- ✓ Validação de esquema
- ✓ Retorno tipado
- ✓ Sem side effects

---

### Limpeza de Dados
**Antes** (app.py, linhas 26-40):
```python
orders = orders.dropna(subset=["order_id", "customer_id", "order_purchase_timestamp"])
orders = orders.drop_duplicates(subset=["order_id"])
orders = orders[orders["order_status"].isin(VALID_STATUS)].copy()
# ... mais limpeza
```

**Depois** → `app/core/pipeline.py`:
```python
def clean_orders(orders: pd.DataFrame, valid_status: set[str]) -> pd.DataFrame:
    """Clean orders dataset: remove nulls, duplicates, filter by status."""
    df = orders.dropna(subset=["order_id", "customer_id", "order_purchase_timestamp"])
    df = df.drop_duplicates(subset=["order_id"])
    df = df[df["order_status"].isin(valid_status)].copy()
    return df

def clean_payments(payments: pd.DataFrame) -> pd.DataFrame:
    """Clean payments dataset: remove nulls, convert types, filter negatives."""
    # ... lógica de limpeza
    return df
```

**Benefícios:**
- ✓ Funções puras (sem side effects)
- ✓ Testáveis isoladamente
- ✓ Reutilizáveis
- ✓ Docstrings claras

---

### Features RFM
**Antes** (app.py, linhas 48-63):
```python
g = orders.groupby("customer_unique_id", sort=False)
features = pd.DataFrame({
    "customer_unique_id": g.size().index,
    "frequency": g.size().to_numpy(),
    # ...
})
features["recency_days"] = (as_of_date - features["last_purchase"]).dt.days.astype("int64")
features["avg_ticket"] = features["monetary"] / features["frequency"]
```

**Depois** → `app/core/pipeline.py` função `compute_customer_features()`:
```python
def compute_customer_features(
    orders: pd.DataFrame,
    as_of_date: pd.Timestamp
) -> pd.DataFrame:
    """Compute RFM features per customer."""
    g = orders.groupby("customer_unique_id", sort=False)
    features = pd.DataFrame({
        "customer_unique_id": g.size().index,
        "frequency": g.size().to_numpy(),
        # ... same logic
    })
    # ... recency, tenure, avg_ticket
    return features
```

**Benefícios:**
- ✓ Assinatura clara com tipos
- ✓ Recebe as_of_date como parâmetro (não global)
- ✓ Retorna DataFrame (não modifica global)

---

### Churn Label
**Antes** (app.py, linhas 65-66):
```python
features["churn"] = (features["recency_days"] >= CHURN_THRESHOLD_DAYS).astype("int8")
```

**Depois** → `app/core/pipeline.py` função `add_churn_label()`:
```python
def add_churn_label(features: pd.DataFrame, threshold_days: int) -> pd.DataFrame:
    """Add binary churn label based on recency threshold."""
    df = features.copy()
    df["churn"] = (df["recency_days"] >= threshold_days).astype("int8")
    return df
```

**Benefícios:**
- ✓ Não modifica input (imutabilidade)
- ✓ Threshold como parâmetro (configurável)
- ✓ Testável: `assert add_churn_label(df, 270)["churn"].sum() == expected`

---

### RFM Scores
**Antes** (app.py, linhas 68-82):
```python
def _qcut_safe(s: pd.Series, q: int, labels):
    x = s.astype(float)
    r = x.rank(method="first")
    return pd.qcut(r, q=q, labels=labels)

features["R_score"] = _qcut_safe(features["recency_days"], q=5, labels=[5, 4, 3, 2, 1]).astype("int8")
# ...
```

**Depois** → `app/core/pipeline.py`:
```python
def qcut_safe(s: pd.Series, q: int, labels: list) -> pd.Series:
    """Safely compute quantile bins using rank to handle duplicates."""
    # ... same logic

def compute_rfm_scores(features: pd.DataFrame) -> pd.DataFrame:
    """Compute RFM scores (1-5) using quintiles."""
    df = features.copy()
    df["R_score"] = qcut_safe(df["recency_days"], q=5, labels=[5, 4, 3, 2, 1])
    # ...
    return df
```

**Benefícios:**
- ✓ Função auxiliar promovida a função de módulo
- ✓ Docstring explicando o "porquê"
- ✓ Type hints completos

---

### Risk Segments
**Antes** (app.py, linhas 84-113):
```python
def _risk_bucket(row) -> str:
    r = row["recency_days"]
    # ... lógica de regras
    return "Churn (prioritário)"

features["monetary_q80"] = features["monetary"].quantile(0.80)
features["risk_segment"] = features.apply(_risk_bucket, axis=1)
features = features.drop(columns=["monetary_q80", "frequency_q80"])
```

**Depois** → `app/core/pipeline.py` função `compute_risk_segments()`:
```python
def compute_risk_segments(features: pd.DataFrame) -> pd.DataFrame:
    """Compute risk segments using business rules based on recency and value."""
    df = features.copy()
    monetary_q80 = df["monetary"].quantile(0.80)
    frequency_q80 = df["frequency"].quantile(0.80)
    
    def risk_bucket(row) -> str:
        # ... lógica
        return segment
    
    df["risk_segment"] = df.apply(risk_bucket, axis=1)
    return df
```

**Benefícios:**
- ✓ Quantiles calculados localmente (não poluem features)
- ✓ Closure para risk_bucket ter acesso aos quantiles
- ✓ Não modifica input

---

### Output (Prints)
**Antes** (app.py, linhas 115-148):
```python
print(f"as_of_date: {as_of_date.date()}")
print(f"clientes: {len(features)}")
print(f"churn_rate(%): {churn_rate:.2f}")
print("\n== Resumo por risk_segment ==")
print(risk_summary.sort_values(...).to_string(index=False))
```

**Depois** → Múltiplas saídas:

1. **API JSON** (`app/api.py`):
```python
@api.route("/summary")
def summary():
    kpis = data_service.get_kpis()
    return jsonify(kpis)
```

2. **Dashboard Web** (`templates/dashboard.html`):
```html
<p class="text-3xl font-bold">{{ kpis.total_customers }}</p>
<p class="text-3xl font-bold text-red-600">{{ kpis.churn_rate }}%</p>
```

3. **Export CSV** (`app/api.py`):
```python
@export.route("/customers.csv")
def export_customers():
    features = data_service.get_all_features()
    # ... convert to CSV
    return response
```

**Benefícios:**
- ✓ Múltiplos formatos de saída
- ✓ Separação de lógica e apresentação
- ✓ Reutilizável (API pode ser consumida por outros sistemas)
- ✓ Interativo (dashboard com charts)

---

## 🎯 Pipeline Orquestração

### Antes (app.py)
Todo código executado linearmente no módulo:
```python
# (imports)
# (config)
customers = pd.read_csv(...)
orders = pd.read_csv(...)
# ... limpeza inline
# ... features inline
# ... prints
```

### Depois (app/core/pipeline.py)
Função orquestradora `run_pipeline()`:
```python
def run_pipeline(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    payments: pd.DataFrame,
    churn_threshold_days: int,
    valid_status: set[str]
) -> Tuple[pd.DataFrame, pd.Timestamp]:
    """Execute the complete churn analysis pipeline."""
    orders_clean = clean_orders(orders, valid_status)
    payments_clean = clean_payments(payments)
    payments_agg = aggregate_payments_by_order(payments_clean)
    orders_joined = join_datasets(orders_clean, customers, payments_agg)
    as_of_date = orders_joined["order_purchase_timestamp"].max()
    
    features = compute_customer_features(orders_joined, as_of_date)
    features = add_churn_label(features, churn_threshold_days)
    features = compute_rfm_scores(features)
    features = compute_risk_segments(features)
    
    return features, as_of_date
```

**Invocado por** `app/services/data_service.py`:
```python
def get_features(self, force_refresh: bool = False):
    if config.CACHE_ENABLED and not force_refresh and self._features is not None:
        return self._features, self._as_of_date
    
    customers, orders, payments = self.load_raw_data()
    features, as_of_date = pipeline.run_pipeline(
        customers, orders, payments,
        config.CHURN_THRESHOLD_DAYS,
        config.VALID_STATUS
    )
    
    if config.CACHE_ENABLED:
        self._features = features
        self._as_of_date = as_of_date
    
    return features, as_of_date
```

**Benefícios:**
- ✓ Pipeline testável end-to-end
- ✓ Cache opcional
- ✓ Separação I/O (service) vs lógica (pipeline)
- ✓ Refresh sob demanda

---

## 🧪 Testes

### Antes
- ❌ Sem testes
- ❌ Difícil testar (tudo acoplado)

### Depois (`tests/test_pipeline.py`)
```python
def test_churn_label_threshold():
    features = pd.DataFrame({
        "recency_days": [100, 269, 270, 500]
    })
    result = pipeline.add_churn_label(features, threshold_days=270)
    assert result.loc[2, "churn"] == 1  # 270 >= 270
```

**6 testes implementados:**
- ✓ Churn label threshold
- ✓ RFM score range (1-5)
- ✓ No negative monetary
- ✓ Clean orders removes invalid
- ✓ Aggregate payments sums correctly
- ✓ qcut_safe handles duplicates

---

## 📂 Estrutura de Arquivos

| Antes | Depois | Responsabilidade |
|-------|--------|------------------|
| `app.py` (linhas 1-11) | `app/config.py` | Configurações |
| `app.py` (linhas 14-24) | `app/services/data_service.py` | Carregamento de dados |
| `app.py` (linhas 26-113) | `app/core/pipeline.py` | Lógica de negócio |
| `app.py` (linhas 115-148) | `app/api.py` + `app/web.py` | Output (API + Web) |
| - | `app/core/validation.py` | Validação de schemas |
| - | `app/core/schemas.py` | Estruturas de dados |
| - | `templates/*.html` | UI/Templates |
| - | `static/js/dashboard.js` | Frontend (charts) |
| - | `tests/test_pipeline.py` | Testes automatizados |

---

## 🔄 Fluxo de Execução

### Antes (app.py)
```
Import → Carrega CSVs → Limpa → Calcula → Printa → Fim
```

### Depois (Flask App)
```
1. Usuário acessa http://localhost:5000
   ↓
2. web.py rota "/" renderiza dashboard.html
   ↓
3. Frontend (JS) faz fetch em /api/summary, /api/churn_by_rfm, etc.
   ↓
4. api.py chama data_service.get_kpis(), get_churn_by_rfm()
   ↓
5. data_service verifica cache → se vazio, executa pipeline
   ↓
6. pipeline.run_pipeline() executa todas as etapas
   ↓
7. Resultado cachado e retornado como JSON
   ↓
8. Frontend renderiza charts com Chart.js
```

---

## ✨ Melhorias Implementadas

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Separação de Concerns** | ❌ Tudo em um arquivo | ✅ Core/Service/Web/API separados |
| **Testabilidade** | ❌ Impossível testar | ✅ 6 testes unitários |
| **Configuração** | ❌ Hardcoded | ✅ Env vars + config.py |
| **Output** | ❌ Apenas console | ✅ Web + API + CSV export |
| **Reutilização** | ❌ Código duplicado | ✅ Funções puras reutilizáveis |
| **Manutenibilidade** | ❌ Difícil alterar | ✅ Módulos pequenos e focados |
| **Escalabilidade** | ❌ Reprocessa tudo | ✅ Cache de resultados |
| **UI/UX** | ❌ Terminal | ✅ Dashboard interativo |
| **Documentação** | ⚠️ Comentários | ✅ README + Docstrings |
| **Validação** | ❌ Nenhuma | ✅ Schema validation |

---

## 🚀 Como Usar

### Executar App Antiga (monolítico)
```bash
cd ChurnLens
python app.py
```
**Output:** Prints no console

### Executar Nova App (Flask)
```bash
cd ChurnLens/churnlens
pip install -r requirements.txt
python run.py
```
**Output:** Dashboard em http://localhost:5000

---

## 📖 Conclusão

A refatoração transformou um **script monolítico de análise** em uma **aplicação web profissional** seguindo:

- ✅ **Clean Code**: Funções pequenas, nomes claros, responsabilidades únicas
- ✅ **Separation of Concerns**: Core/Service/Web/API em camadas
- ✅ **Testability**: Funções puras facilmente testáveis
- ✅ **Configurability**: Env vars para customização
- ✅ **Usability**: Dashboard interativo vs prints

**Preservou 100% da lógica original** enquanto adicionou:
- Interface web
- API REST
- Testes automatizados
- Export de dados
- Visualizações interativas
- Documentação completa

---

**Zero breaking changes na lógica de negócio, 100% de melhoria na arquitetura.** 🎯
