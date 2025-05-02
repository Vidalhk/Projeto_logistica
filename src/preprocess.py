import pandas as pd
import json
from math import radians, sin, cos, sqrt, atan2

# Função Haversine
def haversine(lon1, lat1, lon2, lat2):
    R = 6371
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# Carrega JSON
with open(r'C:\Projetos\Portfolio\Projeto_Transporte\data\raw\deliveries.json', encoding='utf8') as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Normaliza colunas
hub_origin_df = pd.json_normalize(df['origin'])
df = df.drop('origin', axis=1)
df = pd.concat([df, hub_origin_df], axis=1)
df.rename(columns={'lng': 'hub_lng', 'lat': 'hub_lat'}, inplace=True)

df_exploded = df.explode('deliveries')
df_normalized = pd.json_normalize(df_exploded['deliveries'])

# Junta dados finais
df_final = pd.concat([
    df_exploded.drop(columns=['deliveries']).reset_index(drop=True),
    df_normalized[['size', 'point.lng', 'point.lat']].rename(columns={
        'size': 'delivery_size',
        'point.lng': 'delivery_lng',
        'point.lat': 'delivery_lat'
    }).reset_index(drop=True)
], axis=1)

# Calcula distância
df_final['distance_km'] = df_final.apply(
    lambda r: haversine(r['hub_lng'], r['hub_lat'], r['delivery_lng'], r['delivery_lat']), axis=1
)

# Salva como Parquet
df_final.to_parquet(r'C:\Projetos\Portfolio\Projeto_Transporte\data\processed\dados_processados.parquet', index=False)