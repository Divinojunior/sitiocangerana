import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sítio Cangerana", layout="wide")

# CSS para deixar os inputs compactos e parecidos com células de Excel
st.markdown("""
<style>
    [data-testid="stNumberInput"] input {
        padding: 0px 5px;
        font-size: 14px;
        height: 30px;
    }
    label {
        font-size: 12px !important;
        margin-bottom: 0px !important;
    }
    .block-container {
        padding-top: 2rem;
    }
    h3 {
        font-size: 16px !important;
        color: #333;
        border-bottom: 2px solid #ddd;
        padding-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---
@st.cache_resource
def load_data(file_path):
    return pd.ExcelFile(file_path, engine='openpyxl')

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
                    return float(val) if val else default
        return default
    except:
        return default

# --- INÍCIO DO APP ---
st.title("🌱 Sítio Cangerana: Painel de Controle")

# Verifica arquivo
file_path = 'Demostrativo de resultado v24.xlsx'
if not os.path.exists(file_path):
    st.error("Arquivo Excel não encontrado.")
    st.stop()

# Carrega Excel
xls = load_data(file_path)
scenarios = [s for s in xls.sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]

# --- SELETOR DE CENÁRIO (Topo) ---
col_sel, col_blank = st.columns([1, 3])
with col_sel:
    selected_scenario = st.selectbox("📂 Selecione o Cenário Base:", scenarios)

df_raw = pd.read_excel(xls, sheet_name=selected_scenario)

# --- OS 4 GRUPOS (LAYOUT EXATO DA PLANILHA) ---
# Dicionário para guardar os valores editados
inputs = {}

with st.container(border=True):
    # Cria 4 colunas iguais
    c1, c2, c3, c4 = st.columns(4)

    # --- COLUNA 1: DADOS PRINCIPAIS ---
    with c1:
        st.subheader("1. Dados Principais")
        # Lista exata de campos deste grupo
        fields_c1 = [
            "Litros/vaca", "Preço do leite", "Qtd. Vacas total", 
            "Qtd. Vacas em lactação", "Qtd. Vacas no pré parto", 
            "Qtd. Vacas secas", "Qtd. Novilhas", "Qtd. Bezerras"
        ]
        for f in fields_c1:
            val_init = get_val(df_raw, f, 0.0)
            # Cria o input e salva no dicionário 'inputs'
            inputs[f] = st.number_input(f, value=val_init, format="%.2f" if val_init < 100 else "%.0f")

    # --- COLUNA 2: DADOS ADICIONAIS ---
    with c2:
        st.subheader("2. Dados Adicionais")
        fields_c2 = [
            "Valor Kg concentrado lactação", "Valor Kg polpa cítrica", 
            "Valor Kg caroço algodão", "Valor Kg concentrado pré parto",
            "Valor Kg ração bezerra", "Valor Kg ração novilha",
            "Valor Kg silagem", "Relação leite x concentrado"
        ]
        for f in fields_c2:
            val_init = get_val(df_raw, f, 0.0)
            inputs[f] = st.number_input(f, value=val_init, format="%.2f")

    # --- COLUNA 3: LIMPEZA / SANIDADE ---
    with c3:
        st.subheader("3. Limpeza/Sanidade")
        fields_c3 = [
            "Iodo para dipping (Theraflex L)", "Papel toalha (pacote com 1250)",
            "Luvas de látex (pacote com 100)", "Detergente alcalino",
            "Detergente ácido", "Desinfetante", 
            "Pedilúvio - Valor por passada"
        ]
        for f in fields_c3:
            # Encurtar nome para caber na tela
            label = f.split("(")[0].strip()
            val_init = get_val(df_raw, f, 0.0)
            inputs[f] = st.number_input(label, value=val_init, format="%.2f")

    # --- COLUNA 4: DADOS FINANCEIROS ---
    with c4:
        st.subheader("4. Financeiro")
        fields_c4 = [
            "Valor das benfeitorias", "Ordenha", "Galpão ordenha",
            "Trator", "Vagão", "Tanque", 
            "Salário mínimo", "Valor do litro de leite descontado"
        ]
        for f in fields_c4:
            val_init = get_val(df_raw, f, 0.0)
            inputs[f] = st.number_input(f, value=val_init, format="%.2f" if val_init < 1000 else "%.0f")

# --- CÁLCULOS DO DRE (Usando os inputs editados) ---
st.markdown("---")
st.header("📊 Resultados (DRE)")

# Recuperando valores dos inputs
prod_dia = inputs["Litros/vaca"] * inputs["Qtd. Vacas em lactação"]
prod_mensal = prod_dia * 30
receita_bruta = prod_mensal * inputs["Preço do leite"]

# Custo Alimentação (Lógica Simples baseada nos inputs)
relacao = inputs["Relação leite x concentrado"] if inputs["Relação leite x concentrado"] > 0 else 3.0
kg_conc_dia = prod_dia / relacao
custo_conc_mes = kg_conc_dia * 30 * inputs["Valor Kg concentrado lactação"]

# Outros custos variáveis (estimativa somando insumos de limpeza base + 10%)
custo_limpeza_mes = (inputs["Iodo para dipping (Theraflex L)"] * 2) + 200 # Estimativa base
outros_custos = receita_bruta * 0.05 
custo_var_total = custo_conc_mes + custo_limpeza_mes + outros_custos

# Custos Fixos (Salários + Manutenção Benfeitorias)
salario_total = inputs["Salário mínimo"] * 3.5 # Estimativa de 3.5 funcionários/encargos
depreciacao_mensal = (inputs["Valor das benfeitorias"] + inputs["Ordenha"] + inputs["Trator"]) * 0.04 / 12
custo_fixo_total = salario_total + depreciacao_mensal + 2000 # +2000 energia/outros

lucro = receita_bruta - custo_var_total - custo_fixo_total
margem = (lucro / receita_bruta * 100) if receita_bruta > 0 else 0

# --- EXIBIÇÃO DOS RESULTADOS ---

# 1. Cards Coloridos
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Produção Diária", f"{prod_dia:,.0f} L")
kpi2.metric("Receita Bruta", f"R$ {receita_bruta:,.2f}")
kpi3.metric("Custo Total", f"R$ {custo_var_total + custo_fixo_total:,.2f}")
kpi4.metric("Resultado Operacional", f"R$ {lucro:,.2f}", delta=f"{margem:.1f}%")

# 2. Gráfico Waterfall (Cascata)
fig = go.Figure(go.Waterfall(
    orientation = "v",
    measure = ["relative", "relative", "relative", "total"],
    x = ["Receita", "Custo Variável", "Custo Fixo", "Lucro/Prejuízo"],
    textposition = "auto",
    text = [f"{receita_bruta/1000:.1f}k", f"-{custo_var_total/1000:.1f}k", f"-{custo_fixo_total/1000:.1f}k", f"{lucro/1000:.1f}k"],
    y = [receita_bruta, -custo_var_total, -custo_fixo_total, lucro],
    connector = {"line":{"color":"rgb(63, 63, 63)"}},
    decreasing = {"marker":{"color":"#ef553b"}},
    increasing = {"marker":{"color":"#00cc96"}},
    totals = {"marker":{"color":"#1f77b4"}}
))
fig.update_layout(title="Composição do Resultado Financeiro", height=400)
st.plotly_chart(fig, use_container_width=True)

# --- BOTÃO SALVAR ---
st.markdown("### 💾 Exportar Cenário Atual")
df_out = pd.DataFrame([inputs]) # Cria uma tabela com todos os inputs atuais
df_out["RESULTADO_LUCRO"] = lucro # Adiciona o resultado
csv = df_out.to_csv(index=False).encode('utf-8')
st.download_button("Baixar Dados (CSV)", csv, "simulacao_cangerana.csv", "text/csv")
