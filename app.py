import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sítio Cangerana", layout="wide")

# --- FUNÇÃO DE CARREGAMENTO (CACHEADA) ---
@st.cache_resource
def load_data(file_path):
    return pd.ExcelFile(file_path, engine='openpyxl')

# --- TÍTULO ---
st.title("🌱 Sítio Cangerana: Simulador de Cenários")
st.markdown("---")

# --- VERIFICAÇÃO DO ARQUIVO ---
file_path = 'Demostrativo de resultado v24.xlsx'

if not os.path.exists(file_path):
    st.error("⚠️ Arquivo Excel não encontrado!")
    st.warning(f"O arquivo '{file_path}' precisa estar na mesma pasta que este script 'app.py'.")
    st.stop() # Para a execução aqui se não achar o arquivo

# --- SE O ARQUIVO EXISTE, O CÓDIGO SEGUE AQUI (SEM INDENTAÇÃO EXTRA) ---

try:
    xls = load_data(file_path)
    all_sheet_names = xls.sheet_names
    
    # Filtra abas que não queremos
    scenarios = [s for s in all_sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]
    
    # --- BARRA LATERAL ---
    st.sidebar.header("1. Escolha o Cenário")
    selected_scenario = st.sidebar.selectbox("Carregar dados de:", scenarios)

    # Lê a aba selecionada
    df_raw = pd.read_excel(xls, sheet_name=selected_scenario)

except Exception as e:
    st.error(f"Erro ao ler as abas do Excel: {e}")
    st.stop()

# --- FUNÇÃO DE BUSCA INTELIGENTE ---
def get_val(df, search_term, default=0.0):
    try:
        # Varre colunas de texto procurando a palavra chave
        for col in df.select_dtypes(include=['object']):
            matches = df[df[col].astype(str).str.contains(search_term, case=False, na=False)]
            if not matches.empty:
                col_idx = df.columns.get_loc(col)
                # Pega o valor da coluna da direita
                if col_idx + 1 < len(df.columns):
                    val = matches.iloc[0, col_idx + 1]
                    if isinstance(val, str):
                        val = val.replace('R$', '').replace(',', '.').strip()
                    return float(val)
        return default
    except:
        return default

# --- 2. INPUTS (COM VALORES DA PLANILHA) ---
st.sidebar.header("2. Simulação")
st.sidebar.subheader("🐄 Produção")

# Valores iniciais
litros_vaca_init = get_val(df_raw, "Litros/vaca", 20.0)
qtd_vacas_lac_init = get_val(df_raw, "Qtd. Vacas em lactação", 40.0)

# Inputs editáveis
litros_vaca = st.sidebar.number_input("Litros/Vaca/Dia", value=litros_vaca_init, step=0.5)
qtd_vacas_lactacao = st.sidebar.number_input("Vacas em Lactação", value=qtd_vacas_lac_init, step=1.0)

st.sidebar.subheader("💰 Mercado")
preco_leite_init = get_val(df_raw, "Preço do leite", 2.50)
preco_leite = st.sidebar.number_input("Preço do Leite (R$)", value=preco_leite_init, step=0.05)

st.sidebar.subheader("📉 Custos")
custo_conc_init = get_val(df_raw, "Valor Kg concentrado lactação", 2.0)
custo_concentrado = st.sidebar.number_input("Preço Kg Concentrado", value=custo_conc_init, format="%.2f")

# --- 3. CÁLCULOS (LÓGICA MATEMÁTICA) ---
# Receita
producao_dia = litros_vaca * qtd_vacas_lactacao
producao_mensal = producao_dia * 30
receita_bruta = producao_mensal * preco_leite

# Custos Variáveis
relacao_leite_conc = get_val(df_raw, "Relação leite x concentrado", 3.0)
if relacao_leite_conc == 0: relacao_leite_conc = 3.0

consumo_conc_dia = (producao_dia / relacao_leite_conc)
custo_conc_mensal = consumo_conc_dia * 30 * custo_concentrado

# Outros custos variáveis (estimativa 10%)
outros_custos_var = receita_bruta * 0.10 
custo_variavel_total = custo_conc_mensal + outros_custos_var

# Margem de contribuição
margem_contribuicao = receita_br
