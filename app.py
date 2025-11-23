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
    st.stop()

# --- SE O ARQUIVO EXISTE, O CÓDIGO SEGUE AQUI ---
try:
    xls = load_data(file_path)
    all_sheet_names = xls.sheet_names
    
    # Filtra abas que não queremos (ajuste conforme o nome real das suas abas)
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
                        # Limpa caracteres de moeda se houver
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

# Margem de contribuição (CORREÇÃO AQUI: receita_bruta estava cortado)
margem_contribuicao = receita_bruta - custo_variavel_total

# Custos Fixos
salario_minimo = get_val(df_raw, "Salário mínimo", 1412.0)
custos_fixos_estimados = (salario_minimo * 3) + 5000 # Estimativa baseada no seu DRE

# Resultado Final
lucro_operacional = margem_contribuicao - custos_fixos_estimados
margem_lucro = (lucro_operacional / receita_bruta) * 100 if receita_bruta > 0 else 0

# --- 4. DASHBOARD (VISUALIZAÇÃO) ---

# Métricas no topo
c1, c2, c3, c4 = st.columns(4)
c1.metric("Produção Diária", f"{producao_dia:,.0f} L")
c2.metric("Receita Mensal", f"R$ {receita_bruta:,.2f}")
c3.metric("Custo Alimentação", f"R$ {custo_conc_mensal:,.2f}")
c4.metric("Lucro Operacional", f"R$ {lucro_operacional:,.2f}", delta=f"{margem_lucro:.1f}%")

# Colunas para gráficos
col_graf1, col_graf2 = st.columns([2, 1])

with col_graf1:
    st.subheader("DRE Visual")
    fig = go.Figure(go.Waterfall(
        name = "DRE", orientation = "v",
        measure = ["relative", "relative", "relative", "total"],
        x = ["Receita", "Custo Var.", "Custo Fixo", "Lucro"],
        textposition = "outside",
        text = [f"{receita_bruta/1000:.1f}k", f"-{custo_variavel_total/1000:.1f}k", f"-{custos_fixos_estimados/1000:.1f}k", f"{lucro_operacional/1000:.1f}k"],
        y = [receita_bruta, -custo_variavel_total, -custos_fixos_estimados, lucro_operacional],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    st.plotly_chart(fig, use_container_width=True)

with col_graf2:
    st.subheader("Ponto de Equilíbrio")
    # Cálculo PE
    margem_unit = (receita_bruta - custo_variavel_total) / producao_mensal if producao_mensal > 0 else 0
    pe_litros_mes = custos_fixos_estimados / margem_unit if margem_unit > 0 else 0
    pe_litros_dia = pe_litros_mes / 30
    
    st.metric("Meta Zero a Zero", f"{pe_litros_dia:,.0f} L/dia")
    
    delta = producao_dia - pe_litros_dia
    if delta > 0:
        st.success(f"Acima da meta: +{delta:.0f} L")
    else:
        st.error(f"Faltam: {delta:.0f} L")

# --- 5. DOWNLOAD ---
st.markdown("### 💾 Salvar Dados")
df_export = pd.DataFrame({
    'Cenário': [selected_scenario],
    'Receita': [receita_bruta],
    'Lucro': [lucro_operacional],
    'Litros/Dia': [producao_dia]
})

csv = df_export.to_csv(index=False).encode('utf-8')
st.download_button("Baixar Simulação (CSV)", data=csv, file_name="simulacao_cangerana.csv", mime="text/csv")
