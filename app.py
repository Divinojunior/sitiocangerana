import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# Configuração da Página
st.set_page_config(page_title="Sítio Cangerana - Simulador", layout="wide")

# --- CORREÇÃO AQUI: Usamos cache_resource para o arquivo Excel ---
# cache_resource é feito para conexões e arquivos abertos, resolvendo o erro de serialização
@st.cache_resource
def load_data(file_path):
    return pd.ExcelFile(file_path, engine='openpyxl')

# --- TÍTULO E CABEÇALHO ---
st.title("🌱 Sítio Cangerana: Simulador de Cenários")
st.markdown("---")

# --- BARRA LATERAL (CONFIGURAÇÕES) ---
st.sidebar.header("1. Escolha o Cenário Base")

try:
    file_path = 'Demostrativo de resultado v24.xlsx'
    # Chama a função corrigida
    xls = load_data(file_path)
    
    all_sheet_names = xls.sheet_names
    
    # Filtra as abas que não são cenários de input
    scenarios = [s for s in all_sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]
    
    selected_scenario = st.sidebar.selectbox("Carregar dados de:", scenarios)

    # Carrega os dados da aba selecionada
    df_raw = pd.read_excel(xls, sheet_name=selected_scenario)
    
    # --- PROCESSAMENTO DOS DADOS (Busca Inteligente) ---
    # Função que varre a planilha procurando onde está o texto (ex: "Litros/vaca")
    # e pega o valor da célula ao lado, não importa em qual coluna esteja.
    def get_val(df, search_term, default=0.0):
        try:
            # Procura em todas as colunas de texto
            for col in df.select_dtypes(include=['object']):
                # Acha a linha que contém o termo
                matches = df[df[col].astype(str).str.contains(search_term, case=False, na=False)]
                if not matches.empty:
                    # Pega o índice da coluna onde achou
                    col_idx = df.columns.get_loc(col)
                    # Pega o valor da coluna DA DIREITA (col_idx + 1)
                    if col_idx + 1 < len(df.columns):
                        val = matches.iloc[0, col_idx + 1]
                        # Tenta converter para float, se for string limpa sujeira
                        if isinstance(val, str):
                            val = val.replace('R$', '').replace(',', '.').strip()
                        return float(val)
            return default
        except:
            return default

    st.sidebar.header("2. Ajuste as Variáveis")
    
    # --- INPUTS AUTOMÁTICOS ---
    st.sidebar.subheader("🐄 Produção")
    # Busca os valores iniciais na aba selecionada
    litros_vaca_init = get_val(df_raw, "Litros/vaca", 20.0)
    qtd_vacas_lac_init = get_val(df_raw, "Qtd. Vacas em lactação", 40.0)
    
    litros_vaca = st.sidebar.number_input("Litros/Vaca/Dia", value=litros_vaca_init, step=0.5)
    qtd_vacas_lactacao = st.sidebar.number_input("Vacas em Lactação", value=qtd_vacas_lac_init, step=1.0)
    
    st.sidebar.subheader("💰 Mercado")
    preco_leite_init = get_val(df_raw, "Preço do leite", 2.50)
    preco_leite = st.sidebar.number_input("Preço do Leite (R$)", value=preco_leite_init, step=0.05)

    st.sidebar.subheader("📉 Custos Principais")
    custo_conc_init = get_val(df_raw, "Valor Kg concentrado lactação", 2.0)
    custo_concentrado = st.sidebar.number_input("Preço Kg Concentrado", value=custo_conc_init, format="%.2f")
    
    # --- CÁLCULOS DO DRE (Lógica Reconstruída em Python) ---
    
    # 1. Receitas
    producao_dia = litros_vaca * qtd_vacas_lactacao
    producao_mensal = producao_dia * 30
    receita_bruta = producao_mensal * preco_leite
    
    # 2. Custos Variáveis (Alimentação)
    # Lógica: Tenta achar a "Relação leite x concentrado" na planilha, se não achar usa 3.0
    relacao_leite_conc = get_val(df_raw, "Relação leite x concentrado", 3.0)
    if relacao_leite_conc == 0: relacao_leite_conc = 3.0 # Evitar divisão por zero
    
    consumo_conc_dia = (producao_dia / relacao_leite_conc)
    custo_conc_mensal = consumo_conc_dia * 30 * custo_concentrado
    
    # Estima outros custos variáveis como 20% da receita (medicamentos, energia, etc) se não tiver detalhado
    outros_custos_var = receita_bruta * 0.10 
    
    custo_variavel_total = custo_conc_mensal + outros_custos_var
    margem_contribuicao = receita_bruta - custo_variavel_total

    # 3. Custos Fixos (Mão de obra, etc)
    salario_minimo = get_val(df_raw, "Salário mínimo", 1412.0)
    # Estimativa simples: 2 salários + encargos ou valor fixo
    custos_fixos_estimados = (salario_minimo * 3) + 5000 
    
    # 4. Resultado Final
    lucro_operacional = margem_contribuicao - custos_fixos_estimados
    margem_lucro = (lucro_operacional / receita_bruta) * 100 if receita_bruta > 0 else 0

    # --- DASHBOARD ---
    
    # KPI Cards (Indicadores)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Produção Diária", f"{producao_dia:,.0f} L")
    col2.metric("Receita Mensal", f"R$ {receita_bruta:,.2f}")
    col
