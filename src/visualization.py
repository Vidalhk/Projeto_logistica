# === Imports ===
import pandas as pd
import json
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import altair as alt
import warnings
from math import radians, sin, cos, sqrt, atan2

# Configuração da Página (deve ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="Painel Logístico",
    layout="wide",
)

# === Função para cálculo de distância vetorizada ===
def haversine_vectorized(df):
    R = 6371  # raio da terra em km
    lon1 = np.radians(df['hub_lng'])
    lat1 = np.radians(df['hub_lat'])
    lon2 = np.radians(df['delivery_lng'])
    lat2 = np.radians(df['delivery_lat'])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

# Cache para carregamento eficiente
@st.cache_data
def load_and_process_data():
    with open('deliveries.json', mode='r', encoding='utf8') as file:
        data = json.load(file)

    df = pd.DataFrame(data)
    hub_origin_df = pd.json_normalize(df['origin'])
    df = pd.merge(df, hub_origin_df, left_index=True, right_index=True)
    df = df.drop('origin', axis=1)
    df = df[['name', 'region', 'lng', 'lat', 'vehicle_capacity', 'deliveries']]
    df.rename(columns={'lng': 'hub_lng', 'lat': 'hub_lat'}, inplace=True)

    df_exploded = df[['name', 'region', 'hub_lng', 'hub_lat']].copy()
    df_exploded = df_exploded.loc[df.index.repeat(df['deliveries'].apply(len))].reset_index(drop=True)

    deliveries_data = pd.json_normalize([d for sublist in df['deliveries'] for d in sublist])
    df_exploded['delivery_size'] = deliveries_data['size']
    df_exploded['delivery_lng'] = deliveries_data['point.lng']
    df_exploded['delivery_lat'] = deliveries_data['point.lat']

    df_exploded['distance_km'] = haversine_vectorized(df_exploded)

    df_hubs = df_exploded[['region', 'hub_lng', 'hub_lat', 'name']].drop_duplicates().dropna()

    return df_exploded, df_hubs

# === Carregando os dados processados
df_deliveries, df_hub = load_and_process_data()

# === Cores por região
unique_regions = sorted(df_hub['region'].unique())
colors = plt.cm.get_cmap("Set1", len(unique_regions))
region_color_map = {
    region: [int(c * 255) for c in colors(i)[:3]]
    for i, region in enumerate(unique_regions)
}
region_color_hex_map = {
    region: '#%02x%02x%02x' % tuple(rgb)
    for region, rgb in region_color_map.items()
}

# === Sidebar ===
st.sidebar.title('Configurações')
selected_region = st.sidebar.selectbox(
    'Selecione o Hub para análise individual ou comparativa:',
    ['Todos os Hubs'] + list(unique_regions)
)

st.sidebar.markdown('---')
st.sidebar.markdown('''
### Funcionalidades do Projeto
- Mapa interativo das entregas por região  
- Gráfico de volume de entregas por hub  
- Distância total estimada por região  
- Filtro para análise individual de hubs  
''')

# === Título ===
st.title('Projeto de Logística com Análise Geoespacial')

# === Filtro por região ===
if selected_region != 'Todos os Hubs':
    df_deliveries = df_deliveries[df_deliveries['region'] == selected_region]
    df_hub = df_hub[df_hub['region'] == selected_region]

# === Métricas ===
st.subheader("Métricas")
num_entregas = df_deliveries.shape[0]
num_hubs = df_hub['name'].nunique()
num_regioes = df_deliveries['region'].nunique()

colA, colB = st.columns(2)
colA.metric("📦 Total de Entregas", num_entregas)
colB.metric("🏢 N° Hubs Ativos", num_regioes)

# === Distância Total ===
total_distance_km = df_deliveries.groupby('region')['distance_km'].sum().round(2).reset_index()
st.subheader('Distância Total Estimada por Região')
for _, row in total_distance_km.iterrows():
    st.write(f"**Região {row['region']}**: {row['distance_km']} km")

# === Dados para o mapa ===
df_map = df_deliveries[['delivery_lat', 'delivery_lng', 'region']].rename(columns={'delivery_lat': 'lat', 'delivery_lng': 'lon'})
df_map['color'] = df_map['region'].map(region_color_map)
df_map['size'] = 100

df_hubs_map = df_hub.rename(columns={'hub_lat': 'lat', 'hub_lng': 'lon'})
df_hubs_map['color'] = [[0, 0, 0]] * len(df_hubs_map)
df_hubs_map['size'] = 400

df_total = pd.concat([
    df_map[['lat', 'lon', 'color', 'size']],
    df_hubs_map[['lat', 'lon', 'color', 'size']]
], ignore_index=True)

# === Gráfico de Entregas ===
df_counts = df_deliveries['region'].value_counts().reset_index()
df_counts.columns = ['region', 'num_entregas']

chart = alt.Chart(df_counts).mark_bar().encode(
    x=alt.X('region:N', title='Região'),
    y=alt.Y('num_entregas:Q', title='Número de Entregas'),
    color=alt.Color('region:N',
                    scale=alt.Scale(domain=list(region_color_hex_map.keys()), range=list(region_color_hex_map.values())),
                    legend=None)
).properties(
    width=600,
    height=400,
    title='Número de Entregas por Hub (por Região)'
)

# === Exibição lado a lado ===
st.subheader("Visualização Geográfica e Volume de Entregas")
col1, col2 = st.columns(2)
with col1:
    st.map(df_total, latitude='lat', longitude='lon', color='color', size='size')
    st.caption("⚫ Pontos pretos representam os hubs logísticos.")
with col2:
    st.altair_chart(chart, use_container_width=True)

# === Rodapé ===
st.markdown('''
---
📌 **Desenvolvido por Luiz Vidal**  
💡 Projeto de análise de dados e visualização geográfica usando Python e Streamlit.
''')