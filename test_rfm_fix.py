"""Script para verificar se o RFM Score está correto após a correção."""
from app import create_app
from app.services.data_service import data_service

app = create_app()
with app.app_context():
    # Limpar cache para recarregar com novo cálculo
    data_service._features = None
    
    # Verificar os scores RFM (get_features retorna tupla)
    features, as_of_date = data_service.get_features()
    
    print('=== VERIFICAÇÃO DO RFM SCORE ===')
    print(f'Total de clientes: {len(features):,}')
    print(f'\nRFM Score - Valores únicos (primeiros 30):')
    rfm_values = sorted(features['RFM_score'].unique())[:30]
    print(rfm_values)
    print(f'\nRFM Score - Mín: {features["RFM_score"].min()}, Máx: {features["RFM_score"].max()}')
    print(f'\nRFM Score - Estatísticas:')
    print(features['RFM_score'].describe())
    
    print(f'\n=== EXEMPLOS DE CLIENTES ===')
    print(features[['customer_unique_id', 'R_score', 'F_score', 'M_score', 'RFM_score', 'churn']].head(15).to_string())
    
    print(f'\n=== DISTRIBUIÇÃO DE CHURN POR RFM SCORE ===')
    churn_by_rfm = features.groupby('RFM_score')['churn'].agg(['mean', 'count']).round(4)
    churn_by_rfm.columns = ['Taxa_Churn', 'Qtd_Clientes']
    churn_by_rfm = churn_by_rfm.sort_index()
    print(churn_by_rfm.head(20).to_string())
    
    # Verificar se cálculo está correto
    print(f'\n=== VERIFICAÇÃO DO CÁLCULO ===')
    sample = features.head(5).copy()
    sample['RFM_calculado'] = ((sample['R_score'] + sample['F_score'] + sample['M_score']) / 3.0).round(1)
    sample['Match'] = sample['RFM_score'] == sample['RFM_calculado']
    print(sample[['R_score', 'F_score', 'M_score', 'RFM_score', 'RFM_calculado', 'Match']].to_string())
    
    if sample['Match'].all():
        print('\n✅ CÁLCULO CORRETO: RFM Score = (R + F + M) / 3')
    else:
        print('\n❌ ERRO NO CÁLCULO!')
