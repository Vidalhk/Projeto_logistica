import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import altair as alt

# === Configuração da Página ===
st.set_page_config(page_title="Painel Logístico", layout="wide")

# === Carregamento do Dataset Pré-processado ===
@st.cache_data
def load_data():
    return pd.read_parquet('data/processed/dados_processados.parquet')

df = load_data()

# === Construção de DataFrames auxiliares ===
df_hub = df[['region', 'hub_lng', 'hub_lat', 'name']].drop_duplicates().dropna()

# === Cores por região ===
unique_regions = sorted(df_hub['region'].unique())
colors = plt.cm.get_cmap("Set1", len(unique_regions))
region_color_map = {region: [int(c * 255) for c in colors(i)[:3]] for i, region in enumerate(unique_regions)}
region_color_hex_map = {r: '#%02x%02x%02x' % tuple(rgb) for r, rgb in region_color_map.items()}

# === Sidebar ===
st.sidebar.title('Configurações')
selected_region = st.sidebar.selectbox(
    'Selecione o Hub para análise individual ou comparativa:',
    ['Todos os Hubs'] + list(unique_regions)
)
st.sidebar.markdown('''---''')
st.sidebar.markdown('''
### Funcionalidades do Projeto
- Mapa interativo das entregas por região  
- Gráfico de volume de entregas por hub  
- Distância total estimada por região  
- Filtro para análise individual de hubs  
''')

# === Título ===
st.title('Projeto de Logística com Análise Geoespacial')
st.markdown('''
Este painel apresenta uma análise geográfica e quantitativa das entregas realizadas por hubs logísticos em diferentes regiões.
''')

# === Filtro por região ===
if selected_region != 'Todos os Hubs':
    df = df[df['region'] == selected_region]
    df_hub = df_hub[df_hub['region'] == selected_region]

# === Métricas ===
st.subheader("Métricas")
num_entregas = df.shape[0]
num_regioes = df['region'].nunique()

colA, colB = st.columns(2)
colA.metric("📦 Total de Entregas", f"{num_entregas:,}".replace(",", "."))
colB.metric("🏢 N° Hubs Ativos", num_regioes)

# === Distância total por região ===
total_distance_km = df.groupby('region')['distance_km'].sum().round(2).reset_index()
st.subheader('Distância Total Estimada por Região')
for _, row in total_distance_km.iterrows():
    km_formatado = f"{row['distance_km']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.write(f"**Região {row['region']}**: {km_formatado} km")

# === Dados para mapa ===
df_map = df[['delivery_lat', 'delivery_lng', 'region']].rename(columns={'delivery_lat': 'lat', 'delivery_lng': 'lon'})
df_map['color'] = df_map['region'].map(region_color_map)
df_map['size'] = 100

df_hubs_map = df_hub.rename(columns={'hub_lat': 'lat', 'hub_lng': 'lon'})
df_hubs_map['color'] = [[0, 0, 0]] * len(df_hubs_map)
df_hubs_map['size'] = 400

df_total = pd.concat([df_map[['lat', 'lon', 'color', 'size']], df_hubs_map[['lat', 'lon', 'color', 'size']]], ignore_index=True)

# === Gráfico de barras ===
df_counts = df['region'].value_counts().reset_index()
df_counts.columns = ['region', 'num_entregas']

chart = alt.Chart(df_counts).mark_bar().encode(
    x=alt.X('region:N', title='Região'),
    y=alt.Y('num_entregas:Q', title='Número de Entregas'),
    color=alt.Color('region:N', scale=alt.Scale(domain=list(region_color_hex_map.keys()), range=list(region_color_hex_map.values())), legend=None)
).properties(
    width=600,
    height=400,
    title='Número de Entregas por Hub (por Região)'
)

# === Gráficos lado a lado ===
st.subheader("Visualização Geográfica e Volume de Entregas")
col1, col2 = st.columns(2)
with col1:
    st.map(df_total, latitude='lat', longitude='lon', color='color', size='size')
    st.caption("⚫ Pontos pretos indicam os hubs logísticos.")
with col2:
    st.altair_chart(chart, use_container_width=True)

# === Rodapé ===
st.markdown('''
---
📌 **Desenvolvido por Luiz Vidal**  
💡 Projeto de análise de dados e visualização geográfica usando Python e Streamlit.
''')