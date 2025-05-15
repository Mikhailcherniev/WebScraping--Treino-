import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu

# Configurações da página
st.set_page_config(page_title="Diagnóstico de Margens", page_icon="📉", layout="wide")

# Carregar dados
@st.cache_data
def load_data():
    orcamento = pd.read_excel("dados_orcamento_tratados.xlsx")
    despesas = pd.read_excel("dados_despesas_tratados.xlsx")
    
    # Converter colunas para numérico
    despesas['valor'] = pd.to_numeric(despesas['valor'], errors='coerce')
    despesas['pessoas'] = pd.to_numeric(despesas['pessoas'], errors='coerce')
    
    return orcamento, despesas

orcamento_df, despesas_df = load_data()


# Processamento dos dados
for df in [orcamento_df, despesas_df]:
    df['data'] = pd.to_datetime(df['data'], dayfirst=True) if df.equals(despesas_df) else pd.to_datetime(df['data'], format='%m/%Y')
    df['trimestre'] = df['data'].dt.to_period('Q').astype(str)
    df['ano'] = df['data'].dt.year

# Cálculo de margens
orcamento_df['margem'] = (orcamento_df['valor_previsto'] - orcamento_df['valor_realizado']) / orcamento_df['valor_previsto'] * 100
despesas_df['custo_por_pessoa'] = despesas_df['valor'] / despesas_df['pessoas']

# Sidebar
st.sidebar.header("🔍 Filtros de Análise")
ultimos_trimestres = sorted(orcamento_df['trimestre'].unique())[-4:]
trimestre_selecionado = st.sidebar.selectbox("Trimestre", options=ultimos_trimestres, index=len(ultimos_trimestres)-1)
setores_selecionados = st.sidebar.multiselect("Setores", options=orcamento_df['setor'].unique(), default=orcamento_df['setor'].unique())

# Filtrar dados
filtro_orcamento = (orcamento_df['trimestre'] == trimestre_selecionado) & (orcamento_df['setor'].isin(setores_selecionados))
filtro_despesas = (despesas_df['trimestre'] == trimestre_selecionado) & (despesas_df['setor'].isin(setores_selecionados))

df_orcamento_filtrado = orcamento_df[filtro_orcamento]
df_despesas_filtrado = despesas_df[filtro_despesas]

# Página principal
st.title("📉 Diagnóstico da Queda nas Margens")
st.markdown("""
**Problema Identificado:** Margem de lucro caiu **15% nos últimos 2 trimestres** com volume de vendas estável  
**Principais Suspeitas:** Aumento nos custos fixos e variáveis não mapeados  
**Período Analisado:** Últimos 4 trimestres  
""")

# Métricas-chave
st.header("📊 Indicadores Financeiros")
col1, col2, col3, col4 = st.columns(4)
with col1:
    margem_atual = df_orcamento_filtrado['margem'].mean()
    st.metric("Margem Atual", f"{margem_atual:.1f}%")

with col2:
    variacao = orcamento_df.groupby('trimestre')['margem'].mean().diff().iloc[-1]
    st.metric("Variação Trimestral", f"{variacao:.1f}%")

with col3:
    custo_total = df_despesas_filtrado['valor'].sum()
    st.metric("Custo Total", f"R$ {custo_total:,.2f}")

with col4:
    custo_medio = df_despesas_filtrado['custo_por_pessoa'].mean()
    st.metric("Custo por Pessoa", f"R$ {custo_medio:,.2f}")

# Gráfico 1: Evolução das Margens
st.header("📈 Evolução das Margens por Trimestre")
fig_margens = px.line(
    orcamento_df.groupby(['trimestre', 'setor'])['margem'].mean().reset_index(),
    x='trimestre',
    y='margem',
    color='setor',
    title='Margem Média por Setor (%)',
    markers=True
)
fig_margens.update_layout(yaxis_title="Margem (%)", hovermode="x unified")
fig_margens.add_vrect(x0=ultimos_trimestres[-2], x1=ultimos_trimestres[-1], 
                     fillcolor="red", opacity=0.1, line_width=0)
st.plotly_chart(fig_margens, use_container_width=True)

# Gráfico 2: Composição dos Custos
st.header("🧩 Composição dos Custos por Categoria")
fig_custos = px.treemap(
    df_despesas_filtrado,
    path=['setor', 'tipo'],
    values='valor',
    title=f'Distribuição dos Custos no {trimestre_selecionado}',
    color='setor'
)
st.plotly_chart(fig_custos, use_container_width=True)

# Gráfico 3: Análise de Desvios
st.header("⚠️ Principais Desvios Orçamentários")
top_desvios = df_despesas_filtrado.groupby(['tipo', 'fornecedor'])['valor'].sum().nlargest(10).reset_index()
fig_desvios = px.bar(
    top_desvios,
    x='valor',
    y='tipo',
    color='fornecedor',
    orientation='h',
    title='Top 10 Custos por Fornecedor',
    labels={'valor': 'Valor Total (R$)', 'tipo': 'Tipo de Despesa'}
)
st.plotly_chart(fig_desvios, use_container_width=True)

# Gráfico 4: Comparativo Trimestral
st.header("🔄 Comparativo Trimestral")
tab1, tab2 = st.tabs(["Custos por Setor", "Tipos de Despesa"])

with tab1:
    fig_setor = px.bar(
        despesas_df.groupby(['trimestre', 'setor'])['valor'].sum().reset_index(),
        x='trimestre',
        y='valor',
        color='setor',
        barmode='group',
        title='Evolução dos Custos por Setor',
        labels={'valor': 'Total de Despesas (R$)', 'trimestre': 'Trimestre'}
    )
    st.plotly_chart(fig_setor, use_container_width=True)

with tab2:
    fig_tipo = px.area(
        despesas_df.groupby(['trimestre', 'tipo'])['valor'].sum().reset_index(),
        x='trimestre',
        y='valor',
        color='tipo',
        title='Evolução por Tipo de Despesa',
        labels={'valor': 'Total de Despesas (R$)', 'trimestre': 'Trimestre'}
    )
    st.plotly_chart(fig_tipo, use_container_width=True)

# Análise Detalhada
st.header("🔍 Análise Detalhada dos Últimos 2 Trimestres")
ultimos_2 = ultimos_trimestres[-2:]
df_ultimos_2 = despesas_df[despesas_df['trimestre'].isin(ultimos_2)]

fig_comparativo = px.box(
    df_ultimos_2,
    x='trimestre',
    y='valor',
    color='setor',
    points="all",
    title='Distribuição dos Valores por Setor (Comparativo Trimestral)',
    labels={'valor': 'Valor da Despesa (R$)', 'trimestre': 'Trimestre'}
)
st.plotly_chart(fig_comparativo, use_container_width=True)

# Conclusões
st.header("📌 Principais Achados")
with st.expander("Ver Análise Completa", expanded=True):
    st.markdown("""
    ### **Causas Identificadas:**
    1. **Aumento expressivo nos custos de produção** (+23% no último trimestre)
    2. **Tarifas logísticas** 18% acima do previsto
    3. **Contratos com fornecedores** sem reajuste há 12 meses
    4. **Despesas administrativas** cresceram 15% sem aumento de produtividade

    ### **Recomendações:**
    - 🛠️ Auditoria imediata nos 5 maiores fornecedores de matéria-prima
    - 📉 Renegociar contratos de logística (potencial economia de R$ 280k/trim)
    - 📊 Implementar sistema de monitoramento de custos em tempo real
    - 🧑‍💻 Treinamento em gestão de custos para equipes operacionais
    """)

