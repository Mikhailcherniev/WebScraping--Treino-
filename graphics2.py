import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu

# Configurações iniciais 
st.set_page_config(page_title="Dashboard Orçamentário", page_icon="💰", layout="wide")

# Carrega os dados
df = pd.read_excel("dados_orcamento_tratados.xlsx")

# FILTROS - sidebar
st.sidebar.header("Selecione os filtros")

# Filtro por setor
setores = st.sidebar.multiselect(
    "Setores",
    options=df["setor"].unique(),
    default=df["setor"].unique(),
    key="setor"
)

# Filtro por período (data)
datas = st.sidebar.multiselect(
    "Período (Mês/Ano)",
    options=df["data"].unique(),
    default=df["data"].unique(),
    key="data"
)

# Filtrar o dataframe de acordo com as opções selecionadas
df_selecao = df.query("`setor` in @setores and `data` in @datas")

# Funções da página
def Home():
    st.title("Análise Orçamentária")
    
    # Calcula métricas totais
    total_previsto = df_selecao["valor_previsto"].sum()
    total_realizado = df_selecao["valor_realizado"].sum()
    diferenca = total_previsto - total_realizado
    percentual = (diferenca / total_previsto) * 100 if total_previsto != 0 else 0
    
    # Exibe métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Previsto", value=f"R$ {total_previsto:,.2f}")
    
    with col2:
        st.metric("Total Realizado", value=f"R$ {total_realizado:,.2f}")
        
    with col3: 
        st.metric("Diferença", value=f"R$ {diferenca:,.2f}", delta=f"{percentual:.2f}%")
        
    st.markdown("---")
    
def Graficos():
    # Gráfico de barras comparando previsto vs realizado por setor
    fig_barras = px.bar(
        df_selecao,
        x="data",
        y=["valor_previsto", "valor_realizado"],
        color="setor",
        barmode="group",
        title="Comparação Previsto vs Realizado por Setor",
        labels={"value": "Valor (R$)", "data": "Mês/Ano"}
    )
    
    # Gráfico de linha com evolução do realizado por setor
    fig_linha = px.line(
        df_selecao,
        x="data",
        y="valor_realizado",
        color="setor",
        title="Evolução do Realizado por Setor",
        labels={"valor_realizado": "Valor Realizado (R$)", "data": "Mês/Ano"}
    ) 
    
    # Gráfico de pizza com distribuição por setor
    total_por_setor = df_selecao.groupby("setor")["valor_realizado"].sum().reset_index()
    fig_pizza = px.pie(
        total_por_setor,
        values="valor_realizado",
        names="setor",
        title="Distribuição do Realizado por Setor"
    )
    
    # Exibe os gráficos
    st.plotly_chart(fig_barras, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_linha, use_container_width=True)
    with col2:
        st.plotly_chart(fig_pizza, use_container_width=True)
        
def sideBar():
    with st.sidebar:
        selecionado = option_menu(
            menu_title="Menu",
            options=["Visão Geral", "Análise Gráfica"],
            icons=["house", "bar-chart"],
            default_index=0 
        )
    
    if selecionado == "Visão Geral":
        Home()
    elif selecionado == "Análise Gráfica":
        Graficos()
        
sideBar()