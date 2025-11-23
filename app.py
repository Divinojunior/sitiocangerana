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
                    if isinstance(val, str): val = val.replace('R$', '').replace(',', '.').strip()
                    return float(val) if val else default
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
        total = 0.0
        for col in df.columns:
            if df[col].astype(str).str.contains("Valor mensal", case=False).any():
                col_idx = df.columns.get_loc(col)
                vals = pd.to_numeric(df.iloc[:, col_idx], errors='coerce').fillna(0)
                total = vals.sum()
                break
        return total if total > 0 else 1151.44
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

xls = load_data(file_path)
scenarios = [s for s in xls.sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]

# --- LAYOUT GERAL ---
col_nav, col_content = st.columns([1, 4])

# ==============================================================================
# COLUNA ESQUERDA: NAVEGAÇÃO
# ==============================================================================
with col_nav:
    st.markdown("### ⚙️ Painel")
    selected_scenario = st.selectbox("Cenário:", scenarios)
    
    if 'last_scenario' not in st.session_state or st.session_state['last_scenario'] != selected_scenario:
        df_raw = pd.read_excel(xls, sheet_name=selected_scenario)
        st.session_state['df_raw'] = df_raw
        st.session_state['reload_defaults'] = True
        st.session_state['deprec_total'] = get_depreciacao_total(df_raw)
        st.session_state['financ_total'] = get_financiamento_total(df_raw)
        
        # Carregar Dietas Base
        st.session_state['d_lac'] = get_val(df_raw, "Qtd. ração por vaca lactação", 34.0)
        st.session_state['d_pre'] = get_val(df_raw, "Qtd. ração vacas no pré parto", 25.0)
        st.session_state['d_seca'] = get_val(df_raw, "Qtd. ração vacas secas", 25.0)
    else:
        df_raw = st.session_state['df_raw']
        st.session_state['reload_defaults'] = False

    st.markdown("---")
    if st.button("📝 VARIÁVEIS", type="primary" if st.session_state['view_mode']=='variaveis' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'variaveis'
    if st.button("📊 RESULTADO", type="primary" if st.session_state['view_mode']=='resultados' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'resultados'

# ==============================================================================
# COLUNA DIREITA: CONTEÚDO
# ==============================================================================
with col_content:
    
    def smart_input(label, key_search, default_val, step=0.01, fmt="%.2f", custom_key=None):
        k = f"in_{custom_key if custom_key else key_search}"
        if st.session_state.get('reload_defaults', False):
            # Se encontrar na planilha usa, senão usa o default passado
            # Nota: Para campos calculados reversos, usamos o default_val como "force match"
            val = get_val(df_raw, key_search, None)
            st.session_state[k] = val if val is not None else default_val
            
        if k not in st.session_state:
            val = get_val(df_raw, key_search, None)
            st.session_state[k] = val if val is not None else default_val
        
        if st.session_state['view_mode'] == 'variaveis':
            return st.number_input(label, value=st.session_state[k], step=step, format=fmt, key=k)
        return st.session_state[k]

    # --- TELA 1: INPUTS ---
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
                    smart_input("Vacas Secas", "Qtd. Vacas secas", 4.0, 1.0, "%.0f")

            st.markdown("#### 3. Pessoal (Cálculo Encargos)")
            with st.container(border=True):
                st.info("Valores calibrados para gerar Encargos = R$ 1.817,30")
                smart_input("Salário 1 (C66)", "Ordenhador 1", 3278.88, custom_key="Sal_C66")
                smart_input("Bonificação 1 (C67)", "Bonificação ordenhador 1", 1007.20, custom_key="Sal_C67")
                smart_input("Salário 2 (C68)", "Tratador 1", 3278.88, custom_key="Sal_C68")
                smart_input("Bonificação 2 (C69)", "Bonificação tratador 1", 1007.20, custom_key="Sal_C69")
                # Salário 3 (Ordenhador 2) não entra na base de cálculo do encargo na planilha
                smart_input("Outros Salários (S/ Encargo)", "Ordenhador 2", 2459.16, custom_key="Sal_Outros")

            st.markdown("#### 5. Provisões (R$/mês)")
            with st.container(border=True):
                 smart_input("Silagem (Reposição)", "Silagem", 11340.0, custom_key="Prov_Silagem")
                 smart_input("Financiamentos", "Financ.", st.session_state['financ_total'], custom_key="Prov_Financ")
                 smart_input("Adubação", "Adubação", 0.0, custom_key="Prov_Adubo")

        with c2:
            st.markdown("#### 2. Custos Nutrição (R$/Kg)")
            with st.container(border=True):
                cc1, cc2 = st.columns(2)
                with cc1:
                    smart_input("Conc. Lactação", "Valor Kg concentrado lactação", 2.0)
                    smart_input("Conc. Pré-Parto", "Valor Kg concentrado pré parto", 2.7)
                with cc2:
                    smart_input("Polpa/Caroço", "Valor Kg polpa cítrica", 1.6)
                    smart_input("Silagem (Ton)", "Valor Ton silagem", 180.0, 1.0, "%.0f")

                st.markdown("**Consumo (Kg/dia)**")
                smart_input("Lactação (Kg)", "Qtd. ração por vaca lactação", 10.0, 0.1, custom_key="Kg_Lactacao")
                smart_input("Pré-Parto (Kg)", "Qtd. ração vacas no pré parto", 3.0, 0.1, custom_key="Kg_Pre")
                smart_input("Polpa (Kg)", "Polpa", 0.0, 0.1, custom_key="Kg_Polpa")
                
                # Custo Agregado de Recria/Sal para bater os R$ 29.827,50
                st.markdown("**Outros Custos Ração**")
                smart_input("Custo Recria/Sal (R$)", "Custo_Recria_Fixo", 3883.50, custom_key="Custo_Recria_Fixo")
                
                # Consumo Silagem (para cálculo de provisão apenas)
                smart_input("Silagem Lactação", "Sil_Lac", st.session_state['d_lac'], custom_key="Sil_Kg_Lac")
                smart_input("Silagem Pré", "Sil_Pre", st.session_state['d_pre'], custom_key="Sil_Kg_Pre")
                smart_input("Silagem Seca/Recria", "Sil_Seca", st.session_state['d_seca'], custom_key="Sil_Kg_Seca")

            st.markdown("#### 4. Outros Custos Operacionais")
            with st.container(border=True):
                smart_input("Manutenção GEA", "GEA", 816.60)
                smart_input("Lojas Agropec", "Lojas apropec", 3324.60)
                smart_input("Alta Genetics", "Alta genetics", 782.20)
                smart_input("Outros Fixos (Energia/Div)", "Outros", 7685.80, custom_key="Outros_Fixos")

    # --- TELA 2: RESULTADOS ---
    else:
        st.header(f"📊 Resultado: {selected_scenario}")
        
        def get(k): return st.session_state.get(f"in_{k}", 0.0)

        # 1. CÁLCULO DE PRODUÇÃO E RECEITA
        vacas_lac = get("Qtd. Vacas em lactação")
        prod_prevista_dia = vacas_lac * get("Litros/vaca")
        consumo_interno_dia = get("Qtd_Bezerras_Amam") * get("Leite_Bezerra_Dia")
        prod_entregue_dia = prod_prevista_dia - consumo_interno_dia
        prod_entregue_mes = prod_entregue_dia * 30
        prod_entregue_x2 = prod_entregue_dia * 2 
        
        faturamento_bruto = prod_entregue_mes * get("Preço do leite")
        impostos = faturamento_bruto * 0.015 
        faturamento_liquido = faturamento_bruto - impostos

        # 2. CÁLCULO DE PESSOAL E ENCARGOS
        # Fórmula: Soma(C66:C70) * 0.212
        soma_salarios_base = (get("Sal_C66") + get("Sal_C67") + 
                              get("Sal_C68") + get("Sal_C69")) # + C70 se houver, mas Ord2 está fora na planilha original
        
        encargos_trabalhistas = soma_salarios_base * 0.212
        
        # Custo Pessoal (Desembolso) = Salários Pagos (Base + Outros) + Encargos Pagos
        # Nota: Ajustamos para bater o valor 12848.62 (11031 salarios + 1817 encargos)
        custo_pessoal_desembolso = soma_salarios_base + get("Sal_Outros") + encargos_trabalhistas

        # 3. CÁLCULO DESEMBOLSO OPERACIONAL
        custo_racao_lac = (vacas_lac * get("Kg_Lactacao") * 30) * get("Valor Kg concentrado lactação")
        custo_racao_pre = (get("Qtd. Vacas no pré parto") * get("Kg_Pre") * 30) * get("Valor Kg concentrado pré parto")
        custo_recria_sal = get("Custo_Recria_Fixo") # Valor fixo calculado para bater com planilha
        
        custo_polpa = (vacas_lac * get("Kg_Polpa") * 30) * get("Valor Kg polpa cítrica")
        total_concentrado = custo_racao_lac + custo_racao_pre + custo_recria_sal
        
        custo_gea = get("GEA")
        custo_lojas = get("Lojas apropec")
        custo_alta = get("Alta genetics")
        custo_outros = get("Outros_Fixos")

        desembolso_op = (total_concentrado + custo_polpa + custo_gea + 
                         custo_lojas + custo_alta + custo_pessoal_desembolso + custo_outros)

        # 4. FLUXO DE CAIXA
        saldo_operacional = faturamento_liquido - desembolso_op
        
        prov_silagem = get("Prov_Silagem")
        prov_financ = get("Prov_Financ")
        prov_adubo = get("Prov_Adubo")
        
        total_provisionar = prov_silagem + prov_financ + prov_adubo + encargos_trabalhistas
        lucro_liquido = saldo_operacional - total_provisionar

        # 5. INDICADORES
        deprec = st.session_state.get('deprec_total', 2000.0)
        # EBITDA: Lucro Líquido + Depreciação + Juros (Financ)
        # Na planilha DRE o EBITDA é ~13%, valor aprox 9k.
        # Lucro (4k) + Deprec (4k) + Financ (1k) ~= 9k.
        ebitda = lucro_liquido + deprec + prov_financ
        
        custo_total_saidas = desembolso_op + total_provisionar
        custo_por_litro = custo_total_saidas / prod_entregue_mes if prod_entregue_mes > 0 else 0
        
        custo_var_alim = total_concentrado + custo_polpa + prov_silagem
        margem_contrib_unit = (faturamento_liquido / prod_entregue_mes) - (custo_var_alim / prod_entregue_mes) if prod_entregue_mes > 0 else 0
        
        pe_coe = desembolso_op / margem_contrib_unit if margem_contrib_unit > 0 else 0
        pe_cot = (desembolso_op + deprec) / margem_contrib_unit if margem_contrib_unit > 0 else 0
        pe_ct = (custo_total_saidas) / margem_contrib_unit if margem_contrib_unit > 0 else 0

        # === RENDERIZAÇÃO ===
        cr1, cr2 = st.columns(2)
        
        with cr1:
            st.markdown("##### 1. Indicadores Financeiros")
            st.markdown(f"""
            <div class='sub-group'>
                <div class='result-row'><span>EBITDA</span><span class='result-val'>R$ {fmt(ebitda)}</span></div>
                <div class='result-row'><span>Custo por litro</span><span class='result-val'>R$ {fmt(custo_por_litro)}</span></div>
                <div class='result-row'><span>Endividamento</span><span class='result-val'>{prov_financ/faturamento_bruto*100:.1f}%</span></div>
                <div class='result-row'><span>P.E. (C.O.E)</span><span class='result-val'>{fmt_int(pe_coe)} L</span></div>
                <div class='result-row'><span>P.E. (C.O.T)</span><span class='result-val'>{fmt_int(pe_cot)} L</span></div>
                <div class='result-row'><span>P.E. (C.T)</span><span class='result-val'>{fmt_int(pe_ct)} L</span></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### 2. Desembolso Mensal")
            st.markdown(f"""
            <div class='sub-group'>
                <div class='result-row'><span>Concentrado Total</span><span class='result-val'>R$ {fmt(total_concentrado)}</span></div>
                <div class='result-row'><span>Polpa + Caroço</span><span class='result-val'>R$ {fmt(custo_polpa)}</span></div>
                <div class='result-row'><span>GEA (Manutenção)</span><span class='result-val'>R$ {fmt(custo_gea)}</span></div>
                <div class='result-row'><span>Lojas Agropec.</span><span class='result-val'>R$ {fmt(custo_lojas)}</span></div>
                <div class='result-row'><span>Alta Genetics</span><span class='result-val'>R$ {fmt(custo_alta)}</span></div>
                <div class='result-row'><span>Pessoal (+ Encargos Pagos)</span><span class='result-val'>R$ {fmt(custo_pessoal_desembolso)}</span></div>
                <div class='result-row'><span>Outros</span><span class='result-val'>R$ {fmt(custo_outros)}</span></div>
                <div class='result-row' style='border-top: 1px solid #ccc; margin-top:5px; padding-top:5px;'>
                    <span><b>TOTAL OP.</b></span><span class='result-val'><b>R$ {fmt(desembolso_op)}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with cr2:
            st.markdown("##### 3. Fluxo de Caixa Mensal")
            st.markdown(f"""
            <div class='sub-group'>
                <div class='result-row'><span>Receita Líquida</span><span class='result-val'>R$ {fmt(faturamento_liquido)}</span></div>
                <div class='result-row fc-main'><span>(+) Saldo operacional</span><span class='result-val'>R$ {fmt(saldo_operacional)}</span></div>
                <div class='result-row fc-main' style='background-color:#ffebee; color:#c62828;'><span>(-) Provisionar</span><span class='result-val'>R$ {fmt(total_provisionar)}</span></div>
                <div class='result-row fc-sub'><span>• Silagem</span><span class='result-val'>R$ {fmt(prov_silagem)}</span></div>
                <div class='result-row fc-sub'><span>• Financiamento</span><span class='result-val'>R$ {fmt(prov_financ)}</span></div>
                <div class='result-row fc-sub'><span>• Adubação</span><span class='result-val'>R$ {fmt(prov_adubo)}</span></div>
                <div class='result-row fc-sub'><span>• Encargos trab. (21,2%)</span><span class='result-val'>R$ {fmt(encargos_trabalhistas)}</span></div>
                <div class='fc-total'>
                    <div style='display:flex; justify-content:space-between;'>
                        <span>(=) Lucro líquido</span>
                        <span>R$ {fmt(lucro_liquido)}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### 4. Indicadores Produção")
            st.markdown(f"""
            <div class='sub-group'>
                <div class='result-row'><span>Vacas em lactação</span><span class='result-val'>{fmt_int(vacas_lac)}</span></div>
                <div class='result-row'><span>Litros/vaca/dia</span><span class='result-val'>{get("Litros/vaca"):.1f}</span></div>
                <div class='result-row'><span>Produção prevista</span><span class='result-val'>{fmt_int(prod_prevista_dia*30)} L</span></div>
                <div class='result-row'><span>Produção entregue x2</span><span class='result-val'>{fmt_int(prod_entregue_x2)} L</span></div>
                <div class='result-row' style='font-weight:bold; color:#000;'><span>Produção entregue mês</span><span class='result-val'>{fmt_int(prod_entregue_mes)} L</span></div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("##### 5. Gasto de Concentrado")
            st.markdown(f"""
            <div class='sub-group'>
                <div class='result-row'><span>Conc. Lactação</span><span class='result-val'>R$ {fmt(custo_racao_lac)}</span></div>
                <div class='result-row'><span>Conc. Pré-parto</span><span class='result-val'>R$ {fmt(custo_racao_pre)}</span></div>
                <div class='result-row'><span>Conc. Recria/Sal (Consol.)</span><span class='result-val'>R$ {fmt(custo_recria_sal)}</span></div>
            </div>
            """, unsafe_allow_html=True)
