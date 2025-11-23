import streamlit as st
import pandas as pd
import numpy as np
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sítio Cangerana", layout="wide")

# CSS Otimizado
st.markdown("""
<style>
    [data-testid="stNumberInput"] input { padding: 0px 5px; font-size: 14px; height: 30px; }
    label { font-size: 11px !important; margin-bottom: 0px !important; color: #555; }
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }
    .result-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #e0e0e0; font-size: 14px; }
    .result-val { font-weight: bold; color: #0044cc; text-align: right; }
    .sub-group { background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #dee2e6; }
    h5 { color: #1f2937; font-size: 15px; font-weight: 700; margin-bottom: 12px; border-bottom: 2px solid #e5e7eb; padding-bottom: 5px; }
    
    /* Destaques Fluxo de Caixa */
    .fc-main { font-weight: bold; font-size: 14px; color: #1565c0; margin-top: 5px; background-color: #e3f2fd; padding: 5px; border-radius: 4px; }
    .fc-sub { padding-left: 20px; font-size: 13px; color: #555; border-left: 2px solid #eee; }
    .fc-total { font-weight: bold; font-size: 16px; background-color: #d1e7dd; padding: 10px; border-radius: 4px; margin-top: 10px; color: #0f5132; border: 1px solid #badbcc; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE CARGA ---
@st.cache_resource
def load_excel_file(file_path):
    return pd.ExcelFile(file_path, engine='openpyxl')

def get_val_matrix(df, search_term, col_offset=1, default=0.0):
    try:
        for col in df.columns:
            mask = df[col].astype(str).str.contains(search_term, case=False, na=False)
            if mask.any():
                row_idx = df.index[mask][0]
                col_idx = df.columns.get_loc(col)
                target_col_idx = col_idx + col_offset
                
                if target_col_idx < len(df.columns):
                    val = df.iat[row_idx, target_col_idx]
                    if isinstance(val, str): val = val.replace('R$', '').replace(',', '.').strip()
                    return float(val) if pd.notnull(val) else default
        return default
    except:
        return default

def get_depreciacao_total(df):
    try:
        if len(df.columns) > 17:
             soma = pd.to_numeric(df.iloc[:, 17], errors='coerce').sum()
             return soma if soma > 0 else 2000.0
        return 2000.0
    except:
        return 2000.0

def get_financiamento_total(df):
    try:
        for col in df.columns:
            mask = df[col].astype(str).str.contains("Valor mensal", case=False, na=False)
            if mask.any():
                col_idx = df.columns.get_loc(col)
                vals = pd.to_numeric(df.iloc[:, col_idx], errors='coerce').fillna(0)
                return vals.sum()
        return 1151.44
    except:
        return 1151.44

def fmt(val): return f"{val:,.2f}"
def fmt_int(val): return f"{val:,.0f}"

# --- INICIALIZAÇÃO ---
if 'view_mode' not in st.session_state: st.session_state['view_mode'] = 'variaveis'
if 'inputs' not in st.session_state: st.session_state['inputs'] = {}

file_path = 'Demostrativo de resultado v24.xlsx'
if not os.path.exists(file_path):
    st.error("⚠️ Arquivo Excel não encontrado.")
    st.stop()

xls = load_excel_file(file_path)
scenarios = [s for s in xls.sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]

# --- LAYOUT ---
col_nav, col_content = st.columns([1, 4])

with col_nav:
    st.markdown("### ⚙️ Painel")
    selected_scenario = st.selectbox("Cenário:", scenarios)
    
    if 'last_scenario' not in st.session_state or st.session_state['last_scenario'] != selected_scenario:
        df_raw = pd.read_excel(xls, sheet_name=selected_scenario, header=None)
        st.session_state['df_raw'] = df_raw
        st.session_state['reload_defaults'] = True
        st.session_state['deprec_total'] = get_depreciacao_total(df_raw)
        st.session_state['financ_total'] = get_financiamento_total(df_raw)
        
        # CARGA DIETA (Matrix Mode)
        st.session_state['d_lac_conc'] = get_val_matrix(df_raw, "Qtd. ração por vaca lactação", 4, 10.0)
        st.session_state['d_pre_conc'] = get_val_matrix(df_raw, "Qtd. ração vacas no pré parto", 4, 3.0)
        st.session_state['d_lac_sil'] = get_val_matrix(df_raw, "Qtd. ração por vaca lactação", 2, 34.0)
        st.session_state['d_pre_sil'] = get_val_matrix(df_raw, "Qtd. ração vacas no pré parto", 2, 25.0)
        st.session_state['d_seca_sil'] = get_val_matrix(df_raw, "Qtd. ração vacas secas", 2, 25.0)
        
    else:
        df_raw = st.session_state['df_raw']
        st.session_state['reload_defaults'] = False

    st.markdown("---")
    if st.button("📝 VARIÁVEIS", type="primary" if st.session_state['view_mode']=='variaveis' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'variaveis'
    if st.button("📊 RESULTADO", type="primary" if st.session_state['view_mode']=='resultados' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'resultados'

with col_content:
    
    def smart_input(label, key_search, default_val, step=0.01, fmt="%.2f", custom_key=None, offset=1):
        k = f"in_{custom_key if custom_key else key_search}"
        
        if st.session_state.get('reload_defaults', False):
            val = get_val_matrix(df_raw, key_search, offset, None)
            st.session_state[k] = val if val is not None else default_val
            
        if k not in st.session_state:
            val = get_val_matrix(df_raw, key_search, offset, None)
            st.session_state[k] = val if val is not None else default_val
        
        if st.session_state['view_mode'] == 'variaveis':
            return st.number_input(label, value=st.session_state[k], step=step, format=fmt, key=k)
        return st.session_state[k]

    # --- MODO VARIÁVEIS ---
    if st.session_state['view_mode'] == 'variaveis':
        st.header(f"📝 Variáveis: {selected_scenario}")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### 1. Rebanho e Produção")
            with st.container(border=True):
                cc1, cc2 = st.columns(2)
                with cc1:
                    smart_input("Vacas Lactação", "Qtd. Vacas em lactação", 40.0, 1.0, "%.0f")
                    smart_input("Litros/Vaca", "Litros/vaca", 25.0)
                    smart_input("Preço Leite", "Preço do leite", 2.60)
                with cc2:
                    smart_input("Bezerras (Leite)", "Qtd. Bezerras amamentação", 6.6667, 1.0, "%.4f", custom_key="Qtd_Bezerras_Amam")
                    smart_input("Leite/Bezerra/Dia", "Qtd. ração bezerras amamentação", 6.0, 0.5, custom_key="Leite_Bezerra_Dia") 
                    
                    smart_input("Vacas Pré-Parto", "Qtd. Vacas no pré parto", 8.0, 1.0, "%.0f")
                    smart_input("Qtd. Recria Total", "Qtd. Novilhas", 20.0, 1.0, "%.0f")

            st.markdown("#### 3. Pessoal (Base Encargos)")
            with st.container(border=True):
                st.info("Base cálculo 21,2%")
                smart_input("Salário 1 (C66)", "Ordenhador 1", 3278.88, custom_key="Sal_C66")
                smart_input("Bonificação 1 (C67)", "Bonificação ordenhador 1", 1007.20, custom_key="Sal_C67")
                smart_input("Salário 2 (C68)", "Tratador 1", 3278.88, custom_key="Sal_C68")
                smart_input("Bonificação 2 (C69)", "Bonificação tratador 1", 1007.20, custom_key="Sal_C69")
                smart_input("Outros (C70)", "Ordenhador 2", 2459.16, custom_key="Sal_C70")

            st.markdown("#### 5. Provisões (R$/mês)")
            with st.container(border=True):
                 smart_input("Silagem (Reposição)", "Silagem", 11340.0, custom_key="Prov_Silagem", offset=8) 
                 smart_input("Financiamentos", "Financ.", st.session_state['financ_total'], custom_key="Prov_Financ")
                 smart_input("Adubação", "Adubação", 0.0, custom_key="Prov_Adubo")

        with c2:
            st.markdown("#### 2. Custos Nutrição")
            with st.container(border=True):
                cc1, cc2 = st.columns(2)
                with cc1:
                    smart_input("Conc. Lactação (R$)", "Valor Kg concentrado lactação", 2.0)
                    smart_input("Conc. Pré-Parto (R$)", "Valor Kg concentrado pré parto", 2.7)
                    smart_input("Polpa/Caroço (R$)", "Valor Kg polpa cítrica", 1.6)
                with cc2:
                    st.number_input("Lactação (Kg/dia)", value=st.session_state['d_lac_conc'], key="in_Kg_Lactacao", step=0.1)
                    st.number_input("Pré-Parto (Kg/dia)", value=st.session_state['d_pre_conc'], key="in_Kg_Pre", step=0.1)
                    smart_input("Polpa (Kg/dia)", "Polpa", 0.0, 0.1, custom_key="Kg_Polpa", offset=3)
                
                st.markdown("**Custos Extras**")
                smart_input("Custo Recria/Sal (R$)", "Custo_Recria_Fixo", 3883.50, custom_key="Custo_Recria_Fixo")
                
                smart_input("Silagem Lactação (Kg)", "Sil_Lac_Ignored", st.session_state['d_lac_sil'], custom_key="Sil_Kg_Lac")
                smart_input("Silagem Pré (Kg)", "Sil_Pre_Ignored", st.session_state['d_pre_sil'], custom_key="Sil_Kg_Pre")
                smart_input("Silagem Seca (Kg)", "Sil_Seca_Ignored", st.session_state['d_seca_sil'], custom_key="Sil_Kg_Seca")

            st.markdown("#### 4. Outros Custos")
            with st.container(border=True):
                smart_input("Manutenção GEA", "GEA", 816.61)
                smart_input("Lojas Agropec", "Lojas apropec", 3324.64)
                smart_input("Alta Genetics", "Alta genetics", 782.22)
                smart_input("Outros Fixos", "Outros", 7685.80, custom_key="Outros_Fixos")

    # --- MODO RESULTADOS ---
    else:
        st.header(f"📊 Resultado: {selected_scenario}")
        def get(k): return st.session_state.get(f"in_{k}", 0.0)

        # ============================================
        # MOTOR DE CÁLCULO V20 (Corrigido)
        # ============================================

        # 1. PRODUÇÃO
        vacas_lac = get("Qtd. Vacas em lactação")
        prod_teorica_dia = vacas_lac * get("Litros/vaca")
        consumo_interno_dia = get("Qtd_Bezerras_Amam") * get("Leite_Bezerra_Dia")
        
        prod_entregue_dia = prod_teorica_dia - consumo_interno_dia
        prod_entregue_mes = prod_entregue_dia * 30
        prod_entregue_x2 = prod_entregue_dia * 2 
        
        faturamento_bruto = prod_entregue_mes * get("Preço do leite")
        impostos = faturamento_bruto * 0.015 
        faturamento_liquido = faturamento_bruto - impostos

        # 2. PESSOAL
        soma_base = get("Sal_C66") + get("Sal_C67") + get("Sal_C68") + get("Sal_C69")
        encargos = soma_base * 0.212
        custo_pessoal_total = soma_base + get("Sal_C70") + encargos

        # 3. DESEMBOLSO
        custo_racao_lac = (vacas_lac * get("Kg_Lactacao") * 30) * get("Valor Kg concentrado lactação")
        custo_racao_pre = (get("Qtd. Vacas no pré parto") * get("Kg_Pre") * 30) * get("Valor Kg concentrado pré parto")
        custo_recria = get("Custo_Recria_Fixo")
        
        custo_polpa = (vacas_lac * get("Kg_Polpa") * 30) * get("Valor Kg polpa cítrica")
        total_concentrado = custo_racao_lac + custo_racao_pre + custo_recria

        desembolso_op = (total_concentrado + custo_polpa + get("GEA") + get("Lojas apropec") + 
                         get("Alta genetics") + custo_pessoal_total + get("Outros_Fixos"))

        # 4. FLUXO
        saldo_op = faturamento_liquido - desembolso_op
        
        prov_silagem = get("Prov_Silagem") 
        prov_financ = get("Prov_Financ")
        prov_adubo = get("Prov_Adubo")
        
        total_prov = prov_silagem + prov_financ + prov_adubo + encargos
        lucro = saldo_op - total_prov

        # 5. INDICADORES (Safe Division)
        deprec = st.session_state.get('deprec_total', 2000.0)
        ebitda = lucro + deprec + prov_financ
        
        custo_saidas = desembolso_op + total_prov
        custo_litro = custo_saidas / prod_entregue_mes if prod_entregue_mes > 0 else 0
        
        # Endividamento
        endividamento_pct = (prov_financ / faturamento_bruto * 100) if faturamento_bruto > 0 else 0
        
        custo_var = total_concentrado + custo_polpa + prov_silagem
        mcu = (faturamento_liquido / prod_entregue_mes) - (custo_var / prod_entregue_mes) if prod_entregue_mes > 0 else 0
        
        pe_coe = desembolso_op / mcu if mcu > 0 else 0
        pe_cot = (desembolso_op + deprec) / mcu if mcu > 0 else 0
        pe_ct = custo_saidas / mcu if mcu > 0 else 0

        # RENDER
        cr1, cr2 = st.columns(2)
        with cr1:
            st.markdown("##### 1. Indicadores Financeiros")
            st.markdown(f"""<div class='sub-group'>
                <div class='result-row'><span>EBITDA</span><span class='result-val'>R$ {fmt(ebitda)}</span></div>
                <div class='result-row'><span>Custo por litro</span><span class='result-val'>R$ {fmt(custo_litro)}</span></div>
                <div class='result-row'><span>Endividamento</span><span class='result-val'>{endividamento_pct:.1f}%</span></div>
                <div class='result-row'><span>P.E. (C.O.E)</span><span class='result-val'>{fmt_int(pe_coe)} L</span></div>
                <div class='result-row'><span>P.E. (C.O.T)</span><span class='result-val'>{fmt_int(pe_cot)} L</span></div>
                <div class='result-row'><span>P.E. (C.T)</span><span class='result-val'>{fmt_int(pe_ct)} L</span></div>
            </div>""", unsafe_allow_html=True)

            st.markdown("##### 2. Desembolso Mensal")
            st.markdown(f"""<div class='sub-group'>
                <div class='result-row'><span>Concentrado Total</span><span class='result-val'>R$ {fmt(total_concentrado)}</span></div>
                <div class='result-row'><span>Polpa + Caroço</span><span class='result-val'>R$ {fmt(custo_polpa)}</span></div>
                <div class='result-row'><span>GEA</span><span class='result-val'>R$ {fmt(get("GEA"))}</span></div>
                <div class='result-row'><span>Lojas Agropec.</span><span class='result-val'>R$ {fmt(get("Lojas apropec"))}</span></div>
                <div class='result-row'><span>Alta Genetics</span><span class='result-val'>R$ {fmt(get("Alta genetics"))}</span></div>
                <div class='result-row'><span>Pessoal (c/ Encargos)</span><span class='result-val'>R$ {fmt(custo_pessoal_total)}</span></div>
                <div class='result-row'><span>Outros</span><span class='result-val'>R$ {fmt(get("Outros_Fixos"))}</span></div>
                <div class='result-row' style='border-top:1px solid #ccc; margin-top:5px'><span><b>TOTAL</b></span><span class='result-val'><b>R$ {fmt(desembolso_op)}</b></span></div>
            </div>""", unsafe_allow_html=True)

        with cr2:
            st.markdown("##### 3. Fluxo de Caixa")
            st.markdown(f"""<div class='sub-group'>
                <div class='result-row'><span>Receita Líquida</span><span class='result-val'>R$ {fmt(faturamento_liquido)}</span></div>
                <div class='result-row fc-main'><span>(+) Saldo Operacional</span><span class='result-val'>R$ {fmt(saldo_op)}</span></div>
                <div class='result-row fc-main' style='background-color:#ffebee; color:#c62828'><span>(-) Provisionar</span><span class='result-val'>R$ {fmt(total_prov)}</span></div>
                <div class='result-row fc-sub'><span>• Silagem</span><span class='result-val'>R$ {fmt(prov_silagem)}</span></div>
                <div class='result-row fc-sub'><span>• Financ.</span><span class='result-val'>R$ {fmt(prov_financ)}</span></div>
                <div class='result-row fc-sub'><span>• Adubação</span><span class='result-val'>R$ {fmt(prov_adubo)}</span></div>
                <div class='result-row fc-sub'><span>• Encargos (21,2%)</span><span class='result-val'>R$ {fmt(encargos)}</span></div>
                <div class='fc-total'><span>(=) Lucro Líquido</span><span>R$ {fmt(lucro)}</span></div>
            </div>""", unsafe_allow_html=True)

            st.markdown("##### 4. Produção")
            st.markdown(f"""<div class='sub-group'>
                <div class='result-row'><span>Vacas Lactação</span><span class='result-val'>{fmt_int(vacas_lac)}</span></div>
                <div class='result-row'><span>Litros/Vaca</span><span class='result-val'>{get("Litros/vaca"):.1f}</span></div>
                <div class='result-row'><span>Prod. Teórica (Dia)</span><span class='result-val'>{fmt_int(prod_teorica_dia)} L</span></div>
                <div class='result-row'><span>Prod. Prevista (Mês)</span><span class='result-val'>{fmt_int(prod_teorica_dia*30)} L</span></div>
                <div class='result-row'><span>(-) Consumo Bezerras</span><span class='result-val'>- {fmt_int(consumo_interno_dia*30)} L</span></div>
                <div class='result-row' style='font-weight:bold'><span>Prod. Entregue Mês</span><span class='result-val'>{fmt_int(prod_entregue_mes)} L</span></div>
            </div>""", unsafe_allow_html=True)
            
            st.markdown("##### 5. Gasto Concentrado")
            st.markdown(f"""<div class='sub-group'>
                <div class='result-row'><span>Lactação</span><span class='result-val'>R$ {fmt(custo_racao_lac)}</span></div>
                <div class='result-row'><span>Pré-Parto</span><span class='result-val'>R$ {fmt(custo_racao_pre)}</span></div>
                <div class='result-row'><span>Recria/Sal</span><span class='result-val'>R$ {fmt(custo_recria)}</span></div>
            </div>""", unsafe_allow_html=True)
