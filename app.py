import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sítio Cangerana", layout="wide")

# CSS Profissional
st.markdown("""
<style>
    [data-testid="stNumberInput"] input { padding: 0px 5px; font-size: 14px; height: 30px; }
    label { font-size: 11px !important; margin-bottom: 0px !important; color: #555; }
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }
    .nav-btn { width: 100%; margin-bottom: 10px; }
    div.stButton > button { width: 100%; border-radius: 5px; height: 45px; font-weight: 600; }
    .result-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #e0e0e0; font-size: 14px; }
    .result-val { font-weight: bold; color: #0044cc; text-align: right; }
    .sub-group { background-color: #f9f9f9; padding: 10px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #eee; }
    h5 { color: #333; font-size: 14px; font-weight: bold; margin-bottom: 10px; border-bottom: 2px solid #ddd; padding-bottom: 4px; }
    .highlight-box { background-color: #e3f2fd; border-left: 5px solid #2196f3; padding: 10px; margin-bottom: 10px; }
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

# Função para somar a coluna de depreciação mensal da planilha original
def get_depreciacao_total(df):
    try:
        # Procura a coluna que tem "Depreciação Mensal" no cabeçalho ou perto
        # Baseado no CSV, parece ser a coluna R (índice 17) ou por nome
        # Vamos tentar somar a coluna logo após "Depreciação Anual"
        
        # Estratégia: Achar a célula com texto "Depreciação Mensal" e somar o que está abaixo
        for col in df.columns:
            if df[col].astype(str).str.contains("Depreciação Mensal", case=False).any():
                # Achou a coluna, agora precisamos somar os valores numéricos dela
                # Assumindo que os valores estão nas linhas abaixo do cabeçalho
                col_idx = df.columns.get_loc(col)
                # Converte para numérico forçado e soma
                soma = pd.to_numeric(df.iloc[:, col_idx], errors='coerce').sum()
                return soma if soma > 0 else 2000.0
        
        # Se não achar pelo nome, tenta pela posição relativa (Col R do Excel = indice 17)
        if len(df.columns) > 17:
             soma = pd.to_numeric(df.iloc[:, 17], errors='coerce').sum()
             return soma
        
        return 2000.0 # Valor default
    except:
        return 2000.0

def fmt(val): return f"{val:,.2f}"
def fmt_int(val): return f"{val:,.0f}"

# --- INICIALIZAÇÃO DE ESTADO ---
if 'view_mode' not in st.session_state: st.session_state['view_mode'] = 'variaveis'
if 'inputs' not in st.session_state: st.session_state['inputs'] = {}

# --- CARREGAMENTO ---
file_path = 'Demostrativo de resultado v24.xlsx'
if not os.path.exists(file_path):
    st.error("⚠️ Arquivo Excel não encontrado. Por favor, faça o upload.")
    st.stop()

xls = load_data(file_path)
scenarios = [s for s in xls.sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]

# --- LAYOUT GERAL ---
col_nav, col_content = st.columns([1, 4])

# ==============================================================================
# NAVEGAÇÃO
# ==============================================================================
with col_nav:
    st.markdown("### ⚙️ Painel")
    
    selected_scenario = st.selectbox("Cenário Base:", scenarios)
    
    if 'last_scenario' not in st.session_state or st.session_state['last_scenario'] != selected_scenario:
        df_raw = pd.read_excel(xls, sheet_name=selected_scenario)
        st.session_state['last_scenario'] = selected_scenario
        st.session_state['df_raw'] = df_raw
        st.session_state['reload_defaults'] = True 
        # Calcula depreciação fixa deste cenário
        st.session_state['depreciacao_cenario'] = get_depreciacao_total(df_raw)
    else:
        df_raw = st.session_state['df_raw']
        st.session_state['reload_defaults'] = False

    st.markdown("---")
    
    def set_view_vars(): st.session_state['view_mode'] = 'variaveis'
    def set_view_res(): st.session_state['view_mode'] = 'resultados'

    bt_var = "primary" if st.session_state['view_mode'] == 'variaveis' else "secondary"
    st.button("📝 VARIÁVEIS", on_click=set_view_vars, type=bt_var, use_container_width=True)
    
    bt_res = "primary" if st.session_state['view_mode'] == 'resultados' else "secondary"
    st.button("📊 RESULTADO", on_click=set_view_res, type=bt_res, use_container_width=True)

# ==============================================================================
# CONTEÚDO
# ==============================================================================
with col_content:
    
    def smart_input(label, key_search, default_val, step=0.01, fmt="%.2f", custom_key=None):
        k = f"in_{custom_key if custom_key else key_search}"
        
        if st.session_state.get('reload_defaults', False):
            val_excel = get_val(df_raw, key_search, default_val)
            st.session_state[k] = val_excel
        
        if k not in st.session_state:
            val_excel = get_val(df_raw, key_search, default_val)
            st.session_state[k] = val_excel

        if st.session_state['view_mode'] == 'variaveis':
            return st.number_input(label, value=st.session_state[k], step=step, format=fmt, key=k)
        else:
            return st.session_state[k]

    # --- TELA 1: VARIÁVEIS ---
    if st.session_state['view_mode'] == 'variaveis':
        st.header(f"📝 Edição de Variáveis: {selected_scenario}")
        
        c1, c2 = st.columns(2)
        
        with c1:
            with st.container(border=True):
                st.subheader("1. Rebanho e Produção")
                cc1, cc2 = st.columns(2)
                with cc1:
                    smart_input("Vacas em Lactação", "Qtd. Vacas em lactação", 40.0, 1.0, "%.0f")
                    smart_input("Litros/Vaca/Dia", "Litros/vaca", 25.0)
                    smart_input("Preço Leite (R$)", "Preço do leite", 2.60)
                with cc2:
                    smart_input("Bezerras Mamando", "Qtd. Bezerras amamentação", 6.66, 1.0, "%.1f", custom_key="Qtd_Bezerras_Amam")
                    smart_input("Leite/Bezerra/Dia", "Qtd. ração bezerras amamentação", 6.0, 0.5, custom_key="Leite_Bezerra_Dia")
                    smart_input("Qtd. Recria Total", "Qtd. Novilhas", 20.0, 1.0, "%.0f", custom_key="Qtd_Recria_Total")
            
            with st.container(border=True):
                st.subheader("3. Consumo Ração (Kg/cab/dia)")
                cc1, cc2 = st.columns(2)
                with cc1:
                    smart_input("Lactação (Kg)", "Qtd. ração por vaca lactação", 10.0, 0.1, custom_key="Kg_Lactacao")
                    smart_input("Pré-Parto (Kg)", "Qtd. ração vacas no pré parto", 3.0, 0.1, custom_key="Kg_Pre")
                with cc2:
                    smart_input("Recria (Kg Médio)", "Qtd. ração bezerra", 2.0, 0.1, custom_key="Kg_Recria")
                    smart_input("Polpa/Caroço (Kg)", "Polpa", 0.0, 0.1, custom_key="Kg_Polpa")

            with st.container(border=True):
                 st.subheader("5. Limpeza e Sanidade (Unitários)")
                 smart_input("Dipping (R$)", "Iodo para dipping", 13.96)
                 smart_input("Detergente Ácido (R$)", "Detergente ácido", 80.0)
                 smart_input("Detergente Alcalino (R$)", "Detergente alcalino", 100.0)

        with c2:
            with st.container(border=True):
                st.subheader("2. Preços Nutrição (R$/Kg)")
                cc1, cc2 = st.columns(2)
                with cc1:
                    smart_input("Conc. Lactação", "Valor Kg concentrado lactação", 2.0)
                    smart_input("Conc. Pré-Parto", "Valor Kg concentrado pré parto", 2.7)
                with cc2:
                    smart_input("Ração Recria", "Valor Kg ração bezerra", 2.5)
                    smart_input("Polpa/Caroço", "Valor Kg polpa cítrica", 1.6)

            with st.container(border=True):
                st.subheader("4. Custos Fixos Mensais")
                smart_input("Salário Mínimo (R$)", "Salário mínimo", 1412.0)
                smart_input("Manutenção/GEA (R$)", "GEA", 816.0)
                smart_input("Lojas Agropec (R$)", "Lojas apropec", 3300.0)
                smart_input("Alta Genetics (R$)", "Alta genetics", 780.0)
                smart_input("Outros (Energia/Div)", "Outros", 7600.0, custom_key="Outros_Fixos")

            with st.container(border=True):
                 st.subheader("6. Provisões (R$/mês)")
                 smart_input("Silagem (Reposição)", "Silagem", 11340.0, custom_key="Prov_Silagem")
                 smart_input("Financiamentos", "Financ.", 1150.0, custom_key="Prov_Financ")
                 smart_input("Adubação", "Adubação", 0.0, custom_key="Prov_Adubo")

    # --- TELA 2: RESULTADOS ---
    else:
        st.header(f"📊 Resultados Auditados: {selected_scenario}")
        
        # === MOTOR DE CÁLCULO AUDITADO (V9) ===
        def get(k): return st.session_state.get(f"in_{k}", 0.0)
        
        # 1. PRODUÇÃO
        vacas_lac = get("Qtd. Vacas em lactação")
        prod_prevista_dia = vacas_lac * get("Litros/vaca")
        
        # Consumo Interno
        consumo_interno_dia = get("Qtd_Bezerras_Amam") * get("Leite_Bezerra_Dia")
        
        # Prod. Entregue
        prod_entregue_dia = prod_prevista_dia - consumo_interno_dia
        prod_entregue_mes = prod_entregue_dia * 30
        prod_entregue_x2 = prod_entregue_dia * 2 
        
        # 2. RECEITAS
        preco_leite = get("Preço do leite")
        faturamento_bruto = prod_entregue_mes * preco_leite
        
        # Impostos (Funrural + Outros). No DRE é aprox 1.5% a 2.0%
        # Na planilha Atual: "Impostos sobre vendas" = 1123.20 (para Receita 74.880) = 1.5%
        impostos = faturamento_bruto * 0.015 
        faturamento_liquido = faturamento_bruto - impostos
        
        # 3. DESEMBOLSO MENSAL (Operacional)
        # Nutrição
        custo_racao_lac = (vacas_lac * get("Kg_Lactacao") * 30) * get("Valor Kg concentrado lactação")
        custo_racao_pre = (get("Qtd. Vacas no pré parto") * get("Kg_Pre") * 30) * get("Valor Kg concentrado pré parto")
        custo_racao_recria = (get("Qtd_Recria_Total") * get("Kg_Recria") * 30) * get("Valor Kg ração bezerra")
        custo_polpa = (vacas_lac * get("Kg_Polpa") * 30) * get("Valor Kg polpa cítrica")
        total_concentrado = custo_racao_lac + custo_racao_pre + custo_racao_recria
        
        # Custos Fixos Detalhados
        # Salário: 3.5 homens x Salário (ajuste fino para bater com DRE)
        # Se salário min = 1518, Custo Pessoal DRE = ~12.800. Isso dá ~8.5x o salário mínimo (encargos altos ou mais gente)
        # Vamos usar o cálculo que se aproxima do DRE atual
        salario_base = get("Salário mínimo")
        custo_pessoal = salario_base * 4.0 * 1.8 # 4 func + 80% encargos/beneficios
        
        custo_gea = get("GEA")
        custo_lojas = get("Lojas apropec")
        custo_alta = get("Alta genetics")
        custo_outros = get("Outros_Fixos")
        
        desembolso_operacional_total = total_concentrado + custo_polpa + custo_gea + custo_lojas + custo_alta + custo_pessoal + custo_outros
        
        # 4. FLUXO DE CAIXA
        # Saldo Operacional (O que sobra da venda pagando o custo mensal)
        saldo_operacional = faturamento_liquido - desembolso_operacional_total
        
        prov_silagem = get("Prov_Silagem")
        prov_financ = get("Prov_Financ")
        prov_adubo = get("Prov_Adubo")
        
        # Encargos (Linha "Encargos" do Fluxo de Caixa no DRE)
        # Valor 1817.30 para Faturamento 74.880 = 2.42%
        prov_encargos = faturamento_bruto * 0.0242
        
        total_provisoes = prov_silagem + prov_financ + prov_adubo + prov_encargos
        lucro_liquido_caixa = saldo_operacional - total_provisoes
        
        # 5. INDICADORES FINANCEIROS
        # Depreciação: Soma real da coluna da planilha
        depreciacao_real = st.session_state.get('depreciacao_cenario', 2000.0)
        
        # EBITDA: Lucro Líquido + Depreciação + Juros (Financ) + Impostos s/ Lucro (aqui simplificado)
        # Ajuste para bater com lógica DRE: EBITDA costuma ser antes de Juros e Depreciação.
        # DRE Excel diz: EBITDA = 0.13 (13%).
        ebitda_valor = lucro_liquido_caixa + depreciacao_real + prov_financ
        
        # Break-Even Logic
        custo_alim_total = total_concentrado + custo_polpa + prov_silagem
        custo_var_unit = custo_alim_total / prod_entregue_mes if prod_entregue_mes > 0 else 0
        margem_contrib_unit = (faturamento_liquido/prod_entregue_mes) - custo_var_unit
        
        # Ponto de Equilíbrio
        pe_coe = desembolso_operacional_total / margem_contrib_unit if margem_contrib_unit > 0 else 0
        pe_cot = (desembolso_operacional_total + depreciacao_real) / margem_contrib_unit if margem_contrib_unit > 0 else 0
        # Custo Total inclui Custo de Oportunidade (não temos input, usando Financ como proxy de capital)
        pe_ct = (desembolso_operacional_total + depreciacao_real + prov_financ) / margem_contrib_unit if margem_contrib_unit > 0 else 0

        # Custo por Litro (Total Saídas / Litros)
        custo_total_saidas = desembolso_operacional_total + total_provisoes
        custo_por_litro = custo_total_saidas / prod_entregue_mes if prod_entregue_mes > 0 else 0

        # === VISUALIZAÇÃO ===
        cr1, cr2 = st.columns(2)
        
        with cr1:
            st.markdown("##### 1. Indicadores Financeiros")
            with st.container():
                st.markdown(f"""
                <div class='sub-group'>
                    <div class='result-row'><span>EBITDA (Est.)</span><span class='result-val'>R$ {fmt(ebitda_valor)}</span></div>
                    <div class='result-row'><span>Custo por litro</span><span class='result-val'>R$ {fmt(custo_por_litro)}</span></div>
                    <div class='result-row'><span>Endividamento</span><span class='result-val'>{prov_financ/faturamento_bruto*100:.1f}%</span></div>
                    <div class='result-row'><span>P.E. (C.O.E)</span><span class='result-val'>{fmt_int(pe_coe)} L</span></div>
                    <div class='result-row'><span>P.E. (C.O.T)</span><span class='result-val'>{fmt_int(pe_cot)} L</span></div>
                    <div class='result-row'><span>P.E. (C.T)</span><span class='result-val'>{fmt_int(pe_ct)} L</span></div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("##### 2. Desembolso Mensal (Operacional)")
            with st.container():
                st.markdown(f"""
                <div class='sub-group'>
                    <div class='result-row'><span>Concentrado Total</span><span class='result-val'>R$ {fmt(total_concentrado)}</span></div>
                    <div class='result-row'><span>Polpa + Caroço</span><span class='result-val'>R$ {fmt(custo_polpa)}</span></div>
                    <div class='result-row'><span>GEA (Manutenção)</span><span class='result-val'>R$ {fmt(custo_gea)}</span></div>
                    <div class='result-row'><span>Lojas Agropec.</span><span class='result-val'>R$ {fmt(custo_lojas)}</span></div>
                    <div class='result-row'><span>Alta Genetics</span><span class='result-val'>R$ {fmt(custo_alta)}</span></div>
                    <div class='result-row'><span>Pessoal (+Encargos)</span><span class='result-val'>R$ {fmt(custo_pessoal)}</span></div>
                    <div class='result-row'><span>Outros</span><span class='result-val'>R$ {fmt(custo_outros)}</span></div>
                    <div class='result-row' style='border-top: 1px solid #ccc; margin-top:5px; padding-top:5px;'>
                        <span><b>TOTAL OP.</b></span><span class='result-val'><b>R$ {fmt(desembolso_operacional_total)}</b></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with cr2:
            st.markdown("##### 3. Fluxo de Caixa (Gerencial)")
            with st.container():
                st.markdown(f"""
                <div class='sub-group'>
                    <div class='result-row'><span>(+) Saldo Operacional</span><span class='result-val' style='color:green'>R$ {fmt(saldo_operacional)}</span></div>
                    <div class='result-row' style='font-size:11px; color:#666;'><i>(Faturamento Líq - Desembolso Op)</i></div>
                    <div class='result-row'><span>(-) Silagem (Reposição)</span><span class='result-val' style='color:red'>R$ {fmt(prov_silagem)}</span></div>
                    <div class='result-row'><span>(-) Financiamentos</span><span class='result-val' style='color:red'>R$ {fmt(prov_financ)}</span></div>
                    <div class='result-row'><span>(-) Adubação</span><span class='result-val' style='color:red'>R$ {fmt(prov_adubo)}</span></div>
                    <div class='result-row'><span>(-) Encargos/Impostos</span><span class='result-val' style='color:red'>R$ {fmt(prov_encargos)}</span></div>
                    <div class='result-row' style='background-color: #e8f5e9; padding: 8px; border-radius: 4px; margin-top: 5px;'>
                        <span style='font-size:16px; font-weight:bold;'>(=) Saldo Final (Caixa)</span>
                        <span class='result-val' style='font-size:16px; color: #2e7d32;'>R$ {fmt(lucro_liquido_caixa)}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("##### 4. Indicadores Produção")
            with st.container():
                st.markdown(f"""
                <div class='sub-group'>
                    <div class='highlight-box'>
                        <div class='result-row'><span>Prod. Teórica (Dia)</span><span class='result-val'>{fmt_int(prod_prevista_dia)} L</span></div>
                        <div class='result-row' style='color:#d32f2f'><span>(-) Bezerras ({get("Qtd_Bezerras_Amam"):.0f} cab)</span><span class='result-val'>- {fmt_int(consumo_interno_dia)} L</span></div>
                        <div class='result-row' style='font-weight:bold'><span>(=) Prod. Entregue</span><span class='result-val'>{fmt_int(prod_entregue_dia)} L</span></div>
                    </div>
                    <div class='result-row'><span>Prod. Entregue (x2)</span><span class='result-val'>{fmt_int(prod_entregue_x2)} L</span></div>
                    <div class='result-row'><span>Prod. Entregue (Mês)</span><span class='result-val'>{fmt_int(prod_entregue_mes)} L</span></div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("##### 5. Gasto de Concentrado")
            with st.container():
                st.markdown(f"""
                <div class='sub-group'>
                    <div class='result-row'><span>Conc. Lactação</span><span class='result-val'>R$ {fmt(custo_racao_lac)}</span></div>
                    <div class='result-row'><span>Conc. Pré-parto</span><span class='result-val'>R$ {fmt(custo_racao_pre)}</span></div>
                    <div class='result-row'><span>Conc. Recria</span><span class='result-val'>R$ {fmt(custo_racao_recria)}</span></div>
                </div>
                """, unsafe_allow_html=True)
