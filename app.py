import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sítio Cangerana", layout="wide")

# --- ESTILO CSS PERSONALIZADO (Para deixar os grupos bonitos) ---
st.markdown("""
<style>
    .group-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE CARREGAMENTO ---
@st.cache_resource
def load_data(file_path):
    return pd.ExcelFile(file_path, engine='openpyxl')

# --- BUSCA INTELIGENTE DE VALORES ---
def get_val(df, search_term, default=0.0):
    try:
        for col in df.select_dtypes(include=['object']):
            matches = df[df[col].astype(str).str.contains(search_term, case=False, na=False)]
            if not matches.empty:
                col_idx = df.columns.get_loc(col)
                if col_idx + 1 < len(df.columns):
                    val = matches.iloc[0, col_idx + 1]
                    if isinstance(val, str):
                        val = val.replace('R$', '').replace(',', '.').strip()
                    return float(val)
        return default
    except:
        return default

# --- TÍTULO ---
st.title("🌱 Sítio Cangerana: Painel de Controle")
st.markdown("---")

# --- CARREGAMENTO DO ARQUIVO ---
file_path = 'Demostrativo de resultado v24.xlsx'
if not os.path.exists(file_path):
    st.error(f"⚠️ Arquivo '{file_path}' não encontrado na pasta.")
    st.stop()

try:
    xls = load_data(file_path)
    # Filtra abas de sistema
    scenarios = [s for s in xls.sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]
    
    # --- SIDEBAR (CONTROLES) ---
    st.sidebar.header("🕹️ Painel de Comando")
    selected_scenario = st.sidebar.selectbox("Cenário Base:", scenarios)
    
    # Carrega dados da aba
    df_raw = pd.read_excel(xls, sheet_name=selected_scenario)

    st.sidebar.markdown("### 📝 Ajustes Rápidos")
    
    # Grupo 1: Produção (Inputs interativos)
    litros_vaca_init = get_val(df_raw, "Litros/vaca", 20.0)
    qtd_vacas_lac_init = get_val(df_raw, "Qtd. Vacas em lactação", 40.0)
    preco_leite_init = get_val(df_raw, "Preço do leite", 2.50)
    
    litros_vaca = st.sidebar.number_input("Litros/Vaca", value=litros_vaca_init, step=0.5)
    qtd_vacas_lactacao = st.sidebar.number_input("Vacas Lactação", value=qtd_vacas_lac_init, step=1.0)
    preco_leite = st.sidebar.number_input("Preço Leite (R$)", value=preco_leite_init, step=0.05)
    
    # Grupo 2: Custos (Inputs interativos)
    custo_conc_init = get_val(df_raw, "Valor Kg concentrado lactação", 2.0)
    custo_concentrado = st.sidebar.number_input("R$ Kg Concentrado", value=custo_conc_init, format="%.2f")

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# --- CÁLCULOS (MOTOR DO SIMULADOR) ---

# Receitas
producao_dia = litros_vaca * qtd_vacas_lactacao
producao_mensal = producao_dia * 30
receita_bruta = producao_mensal * preco_leite

# Grupo 2: Nutrição (Capturando outros valores para exibição)
val_polpa = get_val(df_raw, "Valor Kg polpa cítrica", 1.6)
val_caroco = get_val(df_raw, "Valor Kg caroço algodão", 2.4)
val_pre_parto = get_val(df_raw, "Valor Kg concentrado pré parto", 3.0)

# Custos Variáveis (Cálculo Estimado)
relacao_leite_conc = get_val(df_raw, "Relação leite x concentrado", 3.0)
consumo_conc_dia = (producao_dia / relacao_leite_conc) if relacao_leite_conc > 0 else 0
custo_conc_mensal = consumo_conc_dia * 30 * custo_concentrado
# Adicional de outros ingredientes (estimativa fixa baseada na planilha ou % da receita)
outros_nutricao = receita_bruta * 0.05 
custo_variavel_total = custo_conc_mensal + outros_nutricao + (receita_bruta * 0.03) # +3% para sanidade

# Grupo 3: Sanidade (Apenas leitura para exibição)
val_iodo = get_val(df_raw, "Iodo para dipping", 13.96)
val_papel = get_val(df_raw, "Papel toalha", 19.50)
val_luvas = get_val(df_raw, "Luvas de látex", 33.00)

# Grupo 4: Financeiro
salario_min = get_val(df_raw, "Salário mínimo", 1412.0)
benfeitorias = get_val(df_raw, "Valor das benfeitorias", 50000.0)
# Estimativa de Custo Fixo Total (Mão de obra + Manutenção + Energia)
custo_fixo_total = (salario_min * 3.5) + (producao_dia * 0.10 * 30) # Ex: 3.5 salários + energia

# Resultado
lucro_operacional = receita_bruta - custo_variavel_total - custo_fixo_total
margem_lucro = (lucro_operacional / receita_bruta) * 100 if receita_bruta > 0 else 0

# --- LAYOUT DO DASHBOARD ---

# 1. KPIs TOPO
col1, col2, col3, col4 = st.columns(4)
col1.metric("🥛 Produção Diária", f"{producao_dia:,.0f} L", delta=f"{litros_vaca} L/vaca")
col2.metric("💰 Receita Mensal", f"R$ {receita_bruta:,.2f}")
col3.metric("📉 Custo Total Est.", f"R$ {custo_variavel_total + custo_fixo_total:,.2f}")
col4.metric("📈 Lucro Operacional", f"R$ {lucro_operacional:,.2f}", delta=f"{margem_lucro:.1f}%")

st.markdown("### 📊 Detalhamento do Cenário")

# 2. OS 4 GRUPOS (GRID 2x2)
# Criamos duas colunas grandes, e dentro delas colocamos os blocos
grid_row1_c1, grid_row1_c2 = st.columns(2)

with grid_row1_c1:
    with st.container(border=True):
        st.subheader("1. Dados Principais (Produção)")
        c_a, c_b = st.columns(2)
        c_a.write(f"**Litros/Vaca:** {litros_vaca:.1f}")
        c_a.write(f"**Preço Leite:** R$ {preco_leite:.2f}")
        c_b.write(f"**Vacas Lactação:** {qtd_vacas_lactacao:.0f}")
        c_b.write(f"**Total Vacas:** {get_val(df_raw, 'Qtd. Vacas total', 0):.0f}")
        st.progress(qtd_vacas_lactacao / (get_val(df_raw, 'Qtd. Vacas total', 100)) if get_val(df_raw, 'Qtd. Vacas total', 1) > 0 else 0, text="Taxa de Lactação")

with grid_row1_c2:
    with st.container(border=True):
        st.subheader("2. Dados Adicionais (Nutrição)")
        c_a, c_b = st.columns(2)
        c_a.write(f"**Conc. Lactação:** R$ {custo_concentrado:.2f}/kg")
        c_a.write(f"**Conc. Pré-parto:** R$ {val_pre_parto:.2f}/kg")
        c_b.write(f"**Polpa Cítrica:** R$ {val_polpa:.2f}/kg")
        c_b.write(f"**Caroço Algodão:** R$ {val_caroco:.2f}/kg")
        st.caption(f"Relação Leite x Conc: 1 para {relacao_leite_conc:.1f}")

grid_row2_c1, grid_row2_c2 = st.columns(2)

with grid_row2_c1:
    with st.container(border=True):
        st.subheader("3. Limpeza e Sanidade")
        st.markdown(f"""
        * **Iodo (Dipping):** R$ {val_iodo:.2f}
        * **Papel Toalha:** R$ {val_papel:.2f}
        * **Luvas Látex:** R$ {val_luvas:.2f}
        """)
        st.caption("Custos unitários de insumos recorrentes")

with grid_row2_c2:
    with st.container(border=True):
        st.subheader("4. Dados Financeiros")
        c_a, c_b = st.columns(2)
        c_a.metric("Salário Mínimo", f"R$ {salario_min:,.2f}")
        c_b.metric("Benfeitorias", f"R$ {benfeitorias/1000:.0f}k")
        st.write(f"**Depreciação Estimada:** R$ {benfeitorias * 0.04 / 12:,.2f}/mês")

# 3. GRÁFICOS INFERIORES
st.markdown("---")
g1, g2 = st.columns([2,1])

with g1:
    st.subheader("DRE Visual (Simulado)")
    fig = go.Figure(go.Waterfall(
        name = "20", orientation = "v",
        measure = ["relative", "relative", "relative", "total"],
        x = ["Receita", "Custo Variável", "Custo Fixo", "Lucro"],
        textposition = "outside",
        text = [f"{receita_bruta/1000:.1f}k", f"-{custo_variavel_total/1000:.1f}k", f"-{custo_fixo_total/1000:.1f}k", f"{lucro_operacional/1000:.1f}k"],
        y = [receita_bruta, -custo_variavel_total, -custo_fixo_total, lucro_operacional],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    st.plotly_chart(fig, use_container_width=True)

with g2:
    st.subheader("Ponto de Equilíbrio")
    margem_unit = (receita_bruta - custo_variavel_total) / producao_mensal if producao_mensal > 0 else 0
    pe_litros = custo_fixo_total / margem_unit if margem_unit > 0 else 0
    pe_dia = pe_litros / 30
    
    st.metric("Litros/Dia para Zero a Zero", f"{pe_dia:,.0f} L")
    st.progress(min(producao_dia / (pe_dia * 1.5) if pe_dia > 0 else 0, 1.0))
    if producao_dia > pe_dia:
        st.success("Operação Saudável")
    else:
        st.error("Abaixo do Ponto de Equilíbrio")

# --- BOTÃO DE DOWNLOAD ---
st.markdown("### 💾 Exportar Dados")
df_export = pd.DataFrame({
    'Indicador': ['Receita', 'Lucro', 'Produção Dia', 'Custo Total'],
    'Valor': [receita_bruta, lucro_operacional, producao_dia, custo_variavel_total + custo_fixo_total]
})
csv = df_export.to_csv(index=False).encode('utf-8')
st.download_button("Baixar Relatório CSV", data=csv, file_name="simulacao_cangerana.csv", mime="text/csv")
