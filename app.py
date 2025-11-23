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
    .fc-header { font-weight: bold; font-size: 14px; color: #1565c0; margin-top: 5px; }
    .fc-item { padding-left: 15px; font-size: 13px; color: #555; }
    .fc-total { font-weight: bold; font-size: 15px; background-color: #e8f5e9; padding: 8px; border-radius: 4px; margin-top: 5px; color: #2e7d32; }
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

# Soma Depreciação (Coluna R)
def get_depreciacao_total(df):
    try:
        if len(df.columns) > 17:
             soma = pd.to_numeric(df.iloc[:, 17], errors='coerce').sum()
             return soma if soma > 0 else 2000.0
        return 2000.0
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
    st.error("⚠️ Arquivo Excel não encontrado.")
    st.stop()

xls = load_data(file_path)
scenarios = [s for s in xls.sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]

# --- LAYOUT GERAL ---
col_nav, col_content = st.columns([1, 4])

# ==============================================================================
# MENU LATERAL
# ==============================================================================
with col_nav:
    st.markdown("### ⚙️ Painel")
    
    selected_scenario = st.selectbox("Cenário Base:", scenarios)
    
    if 'last_scenario' not in st.session_state or st.session_state['last_scenario'] != selected_scenario:
        df_raw = pd.read_excel(xls, sheet_name=selected_scenario)
        st.session_state['last_scenario'] = selected_scenario
        st.session_state['df_raw'] = df_raw
        st.session_state['reload_defaults'] = True 
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
# CONTEÚDO PRINCIPAL
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
                    smart_input("Vacas Lactação", "Qtd. Vacas em lactação", 40.0, 1.0, "%.0f")
                    smart_input("Litros/Vaca/Dia", "Litros/vaca", 25.0)
                    smart_input("Preço Leite (R$)", "Preço do leite", 2.60)
                with cc2:
                    smart_input("Bezerras Mamando", "Qtd. Bezerras amamentação", 6.66, 1.0, "%.1f", custom_key="Qtd_Bezerras_Amam")
                    smart_input("Leite/Bezerra/Dia", "Qtd. ração bezerras amamentação", 6.0, 0.5, custom_key="Leite_Bezerra_Dia")
                    smart_input("Recria Total", "Qtd. Novilhas", 20.0, 1.0, "%.0f", custom_key="Qtd_Recria_Total")
            
            with st.container(border=True):
                st.subheader("3. Detalhamento Equipe (Pessoal)")
                st.info("Valores individuais para cálculo exato dos Encargos (21.2%)")
                # Valores padrão baseados no DRE "Atual"
                smart_input("Gerente", "Gerente", 0.0, custom_key="Sal_Gerente")
                smart_input("Ordenhador 1", "Ordenhador 1", 3278.88, custom_key="Sal_Ord1")
                smart_input("Tratador 1", "Tratador 1", 3278.88, custom_key="Sal_Trat1")
                smart_input("Bonificações (Total)", "Bonificação ordenhador 1", 2014.40, custom_key="Sal_Bonif")
                smart_input("Ordenhador 2 (S/ Encargo)", "Ordenhador 2", 2459.16, custom_key="Sal_Ord2")

            with st.container(border=True):
                 st.subheader("5. Provisões (R$/mês)")
                 smart_input("Silagem (Reposição)", "Silagem", 11340.0, custom_key="Prov_Silagem")
                 smart_input("Financiamentos", "Financ.", 1150.0, custom_key="Prov_Financ")
                 smart_input("Adubação", "Adubação", 0.0, custom_key="Prov_Adubo")

        with c2:
            with st.container(border=True):
                st.subheader("2. Custos Nutrição (R$/Kg)")
                cc1, cc2 = st.columns(2)
                with cc1:
                    smart_input("Conc. Lactação", "Valor Kg concentrado lactação", 2.0)
                    smart_input("Conc. Pré-Parto", "Valor Kg concentrado pré parto", 2.7)
                with cc2:
                    smart_input("Ração Recria", "Valor Kg ração bezerra", 2.5)
                    smart_input("Polpa/Caroço", "Valor Kg polpa cítrica", 1.6)
                
                # Consumo (Kg)
                st.markdown("**Consumo Diário (Kg/cab):**")
                cc3, cc4 = st.columns(2)
                with cc3:
                    smart_input("Lactação (Kg)", "Qtd. ração por vaca lactação", 10.0, 0.1, custom_key="Kg_Lactacao")
                    smart_input("Pré-Parto (Kg)", "Qtd. ração vacas no pré parto", 3.0, 0.1, custom_key="Kg_Pre")
                with cc4:
                    smart_input("Recria (Kg)", "Qtd. ração bezerra", 2.0, 0.1, custom_key="Kg_Recria")
                    smart_input("Polpa (Kg)", "Polpa", 0.0, 0.1, custom_key="Kg_Polpa")

            with st.container(border=True):
                st.subheader("4. Outros Custos Operacionais")
                smart_input("Manutenção/GEA", "GEA", 816.60)
                smart_input("Lojas Agropec", "Lojas apropec", 3324.60)
                smart_input("Alta Genetics", "Alta genetics", 782.20)
                smart_input("Outros (Energia, etc)", "Outros", 7685.80, custom_key="Outros_Fixos")
                
                # Sanidade Básica (apenas visualização de referência)
                st.caption("Custos unitários (Dipping, Detergentes) já incluídos em 'Lojas' ou 'Outros' no DRE base.")

    # --- TELA 2: RESULTADOS ---
    else:
        st.header(f"📊 Resultados Auditados: {selected_scenario}")
        
        def get(k): return st.session_state.get(f"in_{k}", 0.0)
        
        # 1. PRODUÇÃO
        vacas_lac = get("Qtd. Vacas em lactação")
        prod_prevista_dia = vacas_lac * get("Litros/vaca")
        consumo_interno_dia = get("Qtd_Bezerras_Amam") * get("Leite_Bezerra_Dia")
        prod_entregue_dia = prod_prevista_dia - consumo_interno_dia
        prod_entregue_mes = prod_entregue_dia * 30
        prod_entregue_x2 = prod_entregue_dia * 2 
        
        # 2. RECEITAS
        preco_leite = get("Preço do leite")
        faturamento_bruto = prod_entregue_mes * preco_leite
        impostos = faturamento_bruto * 0.015 
        faturamento_liquido = faturamento_bruto - impostos
        
        # 3. PESSOAL & ENCARGOS (FÓRMULA DO USUÁRIO)
        # Encargos C72 = SUM(C66:C70) * 0.212
        # C66=Gerente, C67=Ord1, C68=Bonif, C69=Trat1, C70=Bonif
        # Ord2 (C71) fica de fora da base de cálculo.
        base_encargos = get("Sal_Gerente") + get("Sal_Ord1") + get("Sal_Trat1") + get("Sal_Bonif")
        encargos_trabalhistas = base_encargos * 0.212
        
        # Custo Pessoal Total (para o Desembolso) = Soma de tudo + Encargos
        custo_pessoal_total = base_encargos + get("Sal_Ord2") + encargos_trabalhistas

        # 4. DESEMBOLSO MENSAL
        custo_racao_lac = (vacas_lac * get("Kg_Lactacao") * 30) * get("Valor Kg concentrado lactação")
        custo_racao_pre = (get("Qtd. Vacas no pré parto") * get("Kg_Pre") * 30) * get("Valor Kg concentrado pré parto")
        custo_racao_recria = (get("Qtd_Recria_Total") * get("Kg_Recria") * 30) * get("Valor Kg ração bezerra")
        custo_polpa = (vacas_lac * get("Kg_Polpa") * 30) * get("Valor Kg polpa cítrica")
        total_concentrado = custo_racao_lac + custo_racao_pre + custo_racao_recria
        
        custo_gea = get("GEA")
        custo_lojas = get("Lojas apropec")
        custo_alta = get("Alta genetics")
        custo_outros = get("Outros_Fixos")
        
        desembolso_operacional_total = total_concentrado + custo_polpa + custo_gea + custo_lojas + custo_alta + custo_pessoal_total + custo_outros
        
        # 5. FLUXO DE CAIXA (LÓGICA DRE)
        # Saldo Operacional = Faturamento Liquido - Desembolso
        saldo_operacional = faturamento_liquido - desembolso_operacional_total
        
        prov_silagem = get("Prov_Silagem")
        prov_financ = get("Prov_Financ")
        prov_adubo = get("Prov_Adubo")
        
        # Provisionar (Total) = Silagem + Financ + Adubo + Encargos Trabalhistas
        total_provisionar = prov_silagem + prov_financ + prov_adubo + encargos_trabalhistas
        
        # Lucro Líquido
        lucro_liquido_caixa = saldo_operacional - total_provisionar
        
        # 6. INDICADORES
        depreciacao_real = st.session_state.get('depreciacao_cenario', 2000.0)
        ebitda_valor = lucro_liquido_caixa + depreciacao_real + prov_financ
        
        custo_total_saidas = desembolso_operacional_total + total_provisionar
        custo_por_litro = custo_total_saidas / prod_entregue_mes if prod_entregue_mes > 0 else 0
        
        custo_alim_total = total_concentrado + custo_polpa + prov_silagem
        custo_var_unit = custo_alim_total / prod_entregue_mes if prod_entregue_mes > 0 else 0
        margem_contrib_unit = (faturamento_liquido/prod_entregue_mes) - custo_var_unit
        
        pe_coe = desembolso_operacional_total / margem_contrib_unit if margem_contrib_unit > 0 else 0
        pe_cot = (desembolso_operacional_total + depreciacao_real) / margem_contrib_unit if margem_contrib_unit > 0 else 0
        pe_ct = (desembolso_operacional_total + depreciacao_real + prov_financ) / margem_contrib_unit if margem_contrib_unit > 0 else 0

        # === VISUALIZAÇÃO ===
        cr1, cr2 = st.columns(2)
        
        with cr1:
            st.markdown("##### 1. Indicadores Financeiros")
            with st.container():
                st.markdown(f"""
                <div class='sub-group'>
                    <div class='result-row'><span>EBITDA</span><span class='result-val'>R$ {fmt(ebitda_valor)}</span></div>
                    <div class='result-row'><span>Custo por litro</span><span class='result-val'>R$ {fmt(custo_por_litro)}</span></div>
                    <div class='result-row'><span>Endividamento</span><span class='result-val'>{prov_financ/faturamento_bruto*100:.1f}%</span></div>
                    <div class='result-row'><span>P.E. (C.O.E)</span><span class='result-val'>{fmt_int(pe_coe)} L</span></div>
                    <div class='result-row'><span>P.E. (C.O.T)</span><span class='result-val'>{fmt_int(pe_cot)} L</span></div>
                    <div class='result-row'><span>P.E. (C.T)</span><span class='result-val'>{fmt_int(pe_ct)} L</span></div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("##### 2. Desembolso Mensal")
            with st.container():
                st.markdown(f"""
                <div class='sub-group'>
                    <div class='result-row'><span>Concentrado Total</span><span class='result-val'>R$ {fmt(total_concentrado)}</span></div>
                    <div class='result-row'><span>Polpa + Caroço</span><span class='result-val'>R$ {fmt(custo_polpa)}</span></div>
                    <div class='result-row'><span>GEA (Manutenção)</span><span class='result-val'>R$ {fmt(custo_gea)}</span></div>
                    <div class='result-row'><span>Lojas Agropec.</span><span class='result-val'>R$ {fmt(custo_lojas)}</span></div>
                    <div class='result-row'><span>Alta Genetics</span><span class='result-val'>R$ {fmt(custo_alta)}</span></div>
                    <div class='result-row'><span>Pessoal Total</span><span class='result-val'>R$ {fmt(custo_pessoal_total)}</span></div>
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
                    <div class='result-row fc-header'><span>(+) Saldo operacional</span><span class='result-val' style='color:green'>R$ {fmt(saldo_operacional)}</span></div>
                    <div class='result-row fc-header'><span>(-) Provisionar</span><span class='result-val' style='color:red'>R$ {fmt(total_provisionar)}</span></div>
                    <div class='result-row fc-item'><span>• Silagem</span><span class='result-val' style='font-weight:normal'>R$ {fmt(prov_silagem)}</span></div>
                    <div class='result-row fc-item'><span>• Financiamento</span><span class='result-val' style='font-weight:normal'>R$ {fmt(prov_financ)}</span></div>
                    <div class='result-row fc-item'><span>• Adubação</span><span class='result-val' style='font-weight:normal'>R$ {fmt(prov_adubo)}</span></div>
                    <div class='result-row fc-item'><span>• Encargos trabalhistas</span><span class='result-val' style='font-weight:normal'>R$ {fmt(encargos_trabalhistas)}</span></div>
                    <div class='result-row fc-total'>
                        <span>(=) Lucro líquido</span>
                        <span>R$ {fmt(lucro_liquido_caixa)}</span>
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
