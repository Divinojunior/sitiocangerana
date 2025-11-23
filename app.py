import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sítio Cangerana", layout="wide")

# CSS para visual compacto (Estilo Dashboard Profissional)
st.markdown("""
<style>
    [data-testid="stNumberInput"] input { padding: 0px 5px; font-size: 14px; height: 30px; }
    label { font-size: 12px !important; margin-bottom: 0px !important; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    h4 { color: #444; border-bottom: 1px solid #eee; padding-bottom: 2px; margin-top: 15px; font-size: 15px; }
    .result-row { display: flex; justify-content: space-between; padding: 2px 0; border-bottom: 1px dotted #eee; font-size: 14px; }
    .result-val { font-weight: bold; color: #0044cc; }
    .group-box { background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px; border: 1px solid #eee; }
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

def fmt(val): return f"{val:,.2f}"
def fmt_int(val): return f"{val:,.0f}"

# --- INÍCIO ---
st.title("🌱 Sítio Cangerana: Painel Gerencial")

file_path = 'Demostrativo de resultado v24.xlsx'
if not os.path.exists(file_path):
    st.error("Arquivo Excel não encontrado.")
    st.stop()

xls = load_data(file_path)
scenarios = [s for s in xls.sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]

# Seletor de Cenário
selected_scenario = st.sidebar.selectbox("Cenário Base:", scenarios)
df_raw = pd.read_excel(xls, sheet_name=selected_scenario)

# --- LAYOUT PRINCIPAL (DUAS COLUNAS) ---
col_left, col_right = st.columns([1, 1.1]) # Direita um pouco maior para caber as tabelas

inputs = {} # Dicionário para guardar todos os inputs

# ==============================================================================
# SEÇÃO DA ESQUERDA: INPUTS (CAUSAS)
# ==============================================================================
with col_left:
    st.markdown("### 📝 Premissas (Entradas)")
    
    with st.container(border=True):
        st.subheader("1. Dados Principais")
        c1, c2 = st.columns(2)
        with c1:
            inputs["Litros/vaca"] = st.number_input("Litros/vaca", value=get_val(df_raw, "Litros/vaca", 20.0))
            inputs["Preço do leite"] = st.number_input("Preço do leite", value=get_val(df_raw, "Preço do leite", 2.50))
            inputs["Qtd. Vacas total"] = st.number_input("Qtd. Vacas total", value=get_val(df_raw, "Qtd. Vacas total", 60.0), step=1.0)
            inputs["Qtd. Vacas em lactação"] = st.number_input("Vacas em lactação", value=get_val(df_raw, "Qtd. Vacas em lactação", 40.0), step=1.0)
        with c2:
            inputs["Qtd. Vacas no pré parto"] = st.number_input("Vacas pré-parto", value=get_val(df_raw, "Qtd. Vacas no pré parto", 5.0), step=1.0)
            inputs["Qtd. Vacas secas"] = st.number_input("Vacas secas", value=get_val(df_raw, "Qtd. Vacas secas", 10.0), step=1.0)
            inputs["Qtd. Novilhas"] = st.number_input("Novilhas", value=get_val(df_raw, "Qtd. Novilhas", 15.0), step=1.0)
            inputs["Qtd. Bezerras"] = st.number_input("Bezerras", value=get_val(df_raw, "Qtd. Bezerras", 10.0), step=1.0)

    with st.container(border=True):
        st.subheader("2. Dados Adicionais (Nutrição)")
        c1, c2 = st.columns(2)
        with c1:
            inputs["Valor Kg conc. lactação"] = st.number_input("R$ Kg Conc. Lactação", value=get_val(df_raw, "Valor Kg concentrado lactação", 2.0))
            inputs["Valor Kg conc. pré parto"] = st.number_input("R$ Kg Conc. Pré", value=get_val(df_raw, "Valor Kg concentrado pré parto", 2.5))
            inputs["Valor Kg ração bezerra"] = st.number_input("R$ Kg Raç. Bezerra", value=get_val(df_raw, "Valor Kg ração bezerra", 3.0))
            inputs["Valor Kg ração novilha"] = st.number_input("R$ Kg Raç. Novilha", value=get_val(df_raw, "Valor Kg ração novilha", 2.2))
        with c2:
            inputs["Valor Kg polpa"] = st.number_input("R$ Kg Polpa", value=get_val(df_raw, "Valor Kg polpa cítrica", 1.5))
            inputs["Valor Kg caroço"] = st.number_input("R$ Kg Caroço", value=get_val(df_raw, "Valor Kg caroço algodão", 1.8))
            inputs["Valor Kg silagem"] = st.number_input("R$ Kg Silagem", value=get_val(df_raw, "Valor Kg silagem", 0.2))
            inputs["Relação leite x conc"] = st.number_input("Relação Leite:Conc", value=get_val(df_raw, "Relação leite x concentrado", 3.0))

    with st.container(border=True):
        st.subheader("3. Limpeza e Sanidade")
        c1, c2 = st.columns(2)
        with c1:
            inputs["Iodo dipping"] = st.number_input("Iodo (Dipping)", value=get_val(df_raw, "Iodo para dipping", 13.96))
            inputs["Papel toalha"] = st.number_input("Papel Toalha", value=get_val(df_raw, "Papel toalha", 19.50))
            inputs["Luvas"] = st.number_input("Luvas Látex", value=get_val(df_raw, "Luvas de látex", 33.00))
        with c2:
            inputs["Detergente Alc."] = st.number_input("Det. Alcalino", value=get_val(df_raw, "Detergente alcalino", 100.0))
            inputs["Detergente Ácido"] = st.number_input("Det. Ácido", value=get_val(df_raw, "Detergente ácido", 80.0))
            inputs["Desinfetante"] = st.number_input("Desinfetante", value=get_val(df_raw, "Desinfetante", 50.0))

    with st.container(border=True):
        st.subheader("4. Financeiro")
        c1, c2 = st.columns(2)
        with c1:
            inputs["Salário Mínimo"] = st.number_input("Salário Mínimo", value=get_val(df_raw, "Salário mínimo", 1412.0))
            inputs["Benfeitorias"] = st.number_input("Valor Benfeitorias", value=get_val(df_raw, "Valor das benfeitorias", 100000.0))
            inputs["Maquinario"] = st.number_input("Valor Maquinário", value=get_val(df_raw, "Trator", 50000.0) + get_val(df_raw, "Vagão", 20000.0))
        with c2:
            inputs["Financ. Mensal"] = st.number_input("Financ. (Mensal)", value=get_val(df_raw, "Valor mensal", 0.0) + get_val(df_raw, "Financiamento", 0.0))
            inputs["Outros Fixos"] = st.number_input("Outros Custos Fixos", value=2000.0) # Estimativa

# ==============================================================================
# LÓGICA DE CÁLCULO (ENGINE)
# ==============================================================================
# 1. Produção
prod_dia = inputs["Litros/vaca"] * inputs["Qtd. Vacas em lactação"]
prod_mes = prod_dia * 30
receita_bruta = prod_mes * inputs["Preço do leite"]

# 2. Consumo Concentrados (Estimativas de Nutrição)
# Lactação
kg_conc_lac_dia = prod_dia / inputs["Relação leite x conc"] if inputs["Relação leite x conc"] > 0 else 0
gasto_conc_lac = kg_conc_lac_dia * 30 * inputs["Valor Kg conc. lactação"]
# Pré-parto (Estimativa: 3kg/dia)
gasto_conc_pre = inputs["Qtd. Vacas no pré parto"] * 3 * 30 * inputs["Valor Kg conc. pré parto"]
# Novilhas (Estimativa: 2kg/dia)
gasto_conc_nov = inputs["Qtd. Novilhas"] * 2 * 30 * inputs["Valor Kg ração novilha"]
# Bezerras (Estimativa: 1kg/dia)
gasto_conc_bez = inputs["Qtd. Bezerras"] * 1 * 30 * inputs["Valor Kg ração bezerra"]

total_concentrado = gasto_conc_lac + gasto_conc_pre + gasto_conc_nov + gasto_conc_bez

# 3. Outros Insumos (Polpa/Caroço) - Buscando inputs ou estimando
gasto_polpa_caroco = (prod_dia * 0.5 * 30 * inputs["Valor Kg polpa"]) # Estimativa simples se não tiver input de kg

# 4. Custos Fixos e Operacionais
# Pessoal
custo_pessoal = inputs["Salário Mínimo"] * 3.5 # 3.5 funcionários
# GEA / Lojas / Alta (Buscando valores fixos da planilha se existirem)
custo_gea = get_val(df_raw, "GEA", 500.0)
custo_lojas = get_val(df_raw, "Lojas apropec", 1000.0)
custo_alta = get_val(df_raw, "Alta genetics", 300.0)
custo_outros = inputs["Outros Fixos"]

desembolso_operacional = total_concentrado + gasto_polpa_caroco + custo_gea + custo_lojas + custo_alta + custo_pessoal + custo_outros

# 5. Provisões
prov_silagem = inputs["Qtd. Vacas total"] * 30 * 30 * inputs["Valor Kg silagem"] # Est: 30kg/cab/dia
prov_financ = inputs["Financ. Mensal"]
prov_adubo = get_val(df_raw, "Adubação", 1000.0)

total_saidas_caixa = desembolso_operacional + prov_silagem + prov_financ + prov_adubo
lucro_liquido = receita_bruta - total_saidas_caixa

# 6. Indicadores
# EBITDA aprox (Lucro + Depreciação + Juros)
depreciacao = (inputs["Benfeitorias"] + inputs["Maquinario"]) * 0.04 / 12
ebitda = lucro_liquido + depreciacao + prov_financ 

custo_por_litro = total_saidas_caixa / prod_mes if prod_mes > 0 else 0
# Pontos de Equilíbrio (PE)
# Margem Contribuição Unit = Preço - Custo Var Unit
custo_var_unit = (total_concentrado + gasto_polpa_caroco) / prod_mes if prod_mes > 0 else 0
margem_unit = inputs["Preço do leite"] - custo_var_unit

pe_coe = desembolso_operacional / margem_unit if margem_unit > 0 else 0
pe_cot = (desembolso_operacional + depreciacao) / margem_unit if margem_unit > 0 else 0
pe_ct = (total_saidas_caixa + depreciacao) / margem_unit if margem_unit > 0 else 0 # Incluindo oportunidade/financ

# ==============================================================================
# SEÇÃO DA DIREITA: RESULTADOS (EFEITOS)
# ==============================================================================
with col_right:
    st.markdown("### 📊 Resultados (Indicadores)")
    
    # --- GRUPO 1: INDICADORES FINANCEIROS ---
    with st.container(border=True):
        st.subheader("1. Indicadores Financeiros")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
            <div class='result-row'><span>EBITDA</span><span class='result-val'>R$ {fmt(ebitda)}</span></div>
            <div class='result-row'><span>Custo por Litro</span><span class='result-val'>R$ {fmt(custo_por_litro)}</span></div>
            <div class='result-row'><span>Endividamento</span><span class='result-val'>{prov_financ/receita_bruta*100:.1f}%</span></div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            <div class='result-row'><span>P.E. (C.O.E)</span><span class='result-val'>{fmt_int(pe_coe)} L</span></div>
            <div class='result-row'><span>P.E. (C.O.T)</span><span class='result-val'>{fmt_int(pe_cot)} L</span></div>
            <div class='result-row'><span>P.E. (C.T.)</span><span class='result-val'>{fmt_int(pe_ct)} L</span></div>
            """, unsafe_allow_html=True)

    # --- GRUPO 2: DESEMBOLSO MENSAL ---
    with st.container(border=True):
        st.subheader("2. Desembolso Mensal")
        st.markdown(f"""
        <div class='result-row'><span>Concentrado Total</span><span class='result-val'>R$ {fmt(total_concentrado)}</span></div>
        <div class='result-row'><span>Polpa + Caroço</span><span class='result-val'>R$ {fmt(gasto_polpa_caroco)}</span></div>
        <div class='result-row'><span>GEA (Manutenção)</span><span class='result-val'>R$ {fmt(custo_gea)}</span></div>
        <div class='result-row'><span>Lojas Agropec.</span><span class='result-val'>R$ {fmt(custo_lojas)}</span></div>
        <div class='result-row'><span>Alta Genetics</span><span class='result-val'>R$ {fmt(custo_alta)}</span></div>
        <div class='result-row'><span>Pessoal (Salários)</span><span class='result-val'>R$ {fmt(custo_pessoal)}</span></div>
        <div class='result-row'><span>Outros</span><span class='result-val'>R$ {fmt(custo_outros)}</span></div>
        <div class='result-row' style='background-color: #eef; font-weight: bold;'><span>TOTAL DESEMBOLSO</span><span>R$ {fmt(desembolso_operacional)}</span></div>
        """, unsafe_allow_html=True)

    # --- GRUPO 3: FLUXO DE CAIXA MENSAL ---
    with st.container(border=True):
        st.subheader("3. Fluxo de Caixa Mensal")
        st.markdown(f"""
        <div class='result-row'><span>(+) Receita Bruta</span><span class='result-val' style='color:green'>R$ {fmt(receita_bruta)}</span></div>
        <div class='result-row'><span>(-) Provisionar Silagem</span><span class='result-val' style='color:red'>R$ {fmt(prov_silagem)}</span></div>
        <div class='result-row'><span>(-) Provisionar Financ.</span><span class='result-val' style='color:red'>R$ {fmt(prov_financ)}</span></div>
        <div class='result-row'><span>(-) Prov. Adubação/Encargos</span><span class='result-val' style='color:red'>R$ {fmt(prov_adubo)}</span></div>
        <div class='result-row' style='font-size:16px; margin-top:5px; border-top: 2px solid #ddd;'><span>(=) LUCRO LÍQUIDO</span><span class='result-val'>{fmt(lucro_liquido)}</span></div>
        """, unsafe_allow_html=True)

    # --- GRUPO 4: INDICADORES DE PRODUÇÃO ---
    with st.container(border=True):
        st.subheader("4. Indicadores de Produção")
        col_a, col_b = st.columns(2)
        with col_a:
             st.markdown(f"""
            <div class='result-row'><span>Vacas Lactação</span><span class='result-val'>{fmt_int(inputs["Qtd. Vacas em lactação"])}</span></div>
            <div class='result-row'><span>Litros/Vaca/Dia</span><span class='result-val'>{inputs["Litros/vaca"]:.1f}</span></div>
            <div class='result-row'><span>Preço Leite</span><span class='result-val'>R$ {inputs["Preço do leite"]:.2f}</span></div>
            """, unsafe_allow_html=True)
        with col_b:
             st.markdown(f"""
            <div class='result-row'><span>Prod. Prevista (L)</span><span class='result-val'>{fmt_int(prod_mes)}</span></div>
            <div class='result-row'><span>Prod. Entregue (Mês)</span><span class='result-val'>{fmt_int(prod_mes * 0.98)}</span></div>
            <div class='result-row'><span>Prod. Entregue (x2)</span><span class='result-val'>{fmt_int(prod_mes * 2)}</span></div>
            """, unsafe_allow_html=True)

    # --- GRUPO 5: GASTO DE CONCENTRADO ---
    with st.container(border=True):
        st.subheader("5. Gasto de Concentrado (Detalhe)")
        st.markdown(f"""
        <div class='result-row'><span>Conc. Lactação</span><span class='result-val'>R$ {fmt(gasto_conc_lac)}</span></div>
        <div class='result-row'><span>Conc. Pré-Parto</span><span class='result-val'>R$ {fmt(gasto_conc_pre)}</span></div>
        <div class='result-row'><span>Conc. Novilhas</span><span class='result-val'>R$ {fmt(gasto_conc_nov)}</span></div>
        <div class='result-row'><span>Conc. Bezerras</span><span class='result-val'>R$ {fmt(gasto_conc_bez)}</span></div>
        """, unsafe_allow_html=True)

# --- DOWNLOAD ---
st.markdown("---")
if st.button("💾 Baixar Relatório Completo (CSV)"):
    # Monta um dataframe simples para exportação
    csv = pd.DataFrame([inputs]).T.to_csv().encode('utf-8')
    st.download_button("Clique para Download", csv, "relatorio_cangerana.csv", "text/csv")
