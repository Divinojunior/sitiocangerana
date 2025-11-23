import streamlit as st
import pandas as pd
import numpy as np
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sítio Cangerana", layout="wide")

# CSS Ajustado para Layout Limpo
st.markdown("""
<style>
    [data-testid="stNumberInput"] input { padding: 0px 5px; font-size: 14px; height: 30px; }
    label { font-size: 11px !important; margin-bottom: 0px !important; color: #555; }
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }
    .result-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #e0e0e0; font-size: 14px; }
    .result-val { font-weight: bold; color: #0044cc; text-align: right; }
    .sub-group { background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #dee2e6; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    h5 { color: #1f2937; font-size: 15px; font-weight: 700; margin-bottom: 12px; border-bottom: 2px solid #e5e7eb; padding-bottom: 5px; }
    
    /* Estilos específicos para o Fluxo de Caixa */
    .fc-main { font-weight: bold; font-size: 14px; color: #1565c0; margin-top: 5px; background-color: #e3f2fd; padding: 5px; border-radius: 4px; }
    .fc-sub { padding-left: 20px; font-size: 13px; color: #555; border-left: 2px solid #eee; }
    .fc-final { font-weight: bold; font-size: 16px; background-color: #d1e7dd; padding: 10px; border-radius: 4px; margin-top: 10px; color: #0f5132; border: 1px solid #badbcc; }
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

# Soma da coluna de depreciação mensal
def get_depreciacao_total(df):
    try:
        if len(df.columns) > 17: # Coluna R é index 17
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
if 'view_mode' not in st.session_state: st.session_state['view_mode'] = 'variaveis' # Padrão
if 'inputs' not in st.session_state: st.session_state['inputs'] = {}

file_path = 'Demostrativo de resultado v24.xlsx'
if not os.path.exists(file_path):
    st.error("⚠️ Arquivo Excel não encontrado.")
    st.stop()

xls = load_data(file_path)
scenarios = [s for s in xls.sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]

# --- LAYOUT PRINCIPAL ---
col_left, col_right = st.columns([1, 1.2]) # Direita ligeiramente maior

# ==============================================================================
# COLUNA ESQUERDA: VARIÁVEIS (INPUTS)
# ==============================================================================
with col_left:
    st.markdown("### ⚙️ Painel de Controle")
    selected_scenario = st.selectbox("Cenário:", scenarios)
    
    # Lógica de carga de dados
    if 'last_scenario' not in st.session_state or st.session_state['last_scenario'] != selected_scenario:
        df_raw = pd.read_excel(xls, sheet_name=selected_scenario)
        st.session_state['df_raw'] = df_raw
        st.session_state['reload_defaults'] = True
        st.session_state['deprec_total'] = get_depreciacao_total(df_raw)
        st.session_state['financ_total'] = get_financiamento_total(df_raw)
        
        # Dieta Default
        st.session_state['d_lac'] = get_val(df_raw, "Qtd. ração por vaca lactação", 34.0)
        st.session_state['d_pre'] = get_val(df_raw, "Qtd. ração vacas no pré parto", 25.0)
        st.session_state['d_seca'] = get_val(df_raw, "Qtd. ração vacas secas", 25.0)
        st.session_state['d_recria'] = 10.0
    else:
        df_raw = st.session_state['df_raw']
        st.session_state['reload_defaults'] = False

    # Botões de navegação
    st.markdown("---")
    c_btn1, c_btn2 = st.columns(2)
    if c_btn1.button("📝 VARIÁVEIS", type="primary" if st.session_state['view_mode']=='variaveis' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'variaveis'
    if c_btn2.button("📊 RESULTADO", type="primary" if st.session_state['view_mode']=='resultados' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'resultados'

    # Função Helper Input
    def smart_input(label, key_search, default_val, step=0.01, fmt="%.2f", custom_key=None):
        k = f"in_{custom_key if custom_key else key_search}"
        if st.session_state.get('reload_defaults', False):
            st.session_state[k] = get_val(df_raw, key_search, default_val)
        if k not in st.session_state:
            st.session_state[k] = get_val(df_raw, key_search, default_val)
        
        # Se estiver no modo variáveis, mostra o input. Se não, apenas guarda o valor.
        if st.session_state['view_mode'] == 'variaveis':
            return st.number_input(label, value=st.session_state[k], step=step, format=fmt, key=k)
        return st.session_state[k]

    # --- RENDERIZAÇÃO DOS INPUTS ---
    if st.session_state['view_mode'] == 'variaveis':
        st.markdown("#### 1. Produção e Rebanho")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                smart_input("Vacas Lactação", "Qtd. Vacas em lactação", 40.0, 1.0, "%.0f")
                smart_input("Litros/Vaca", "Litros/vaca", 25.0)
                smart_input("Preço Leite", "Preço do leite", 2.60)
            with c2:
                smart_input("Bezerras (Leite)", "Qtd. Bezerras amamentação", 6.66, 1.0, "%.1f", custom_key="Qtd_Bezerras_Amam")
                smart_input("Leite/Bezerra/Dia", "Qtd. ração bezerras amamentação", 6.0, 0.5, custom_key="Leite_Bezerra_Dia")
                smart_input("Total Recria", "Qtd. Novilhas", 20.0, 1.0, "%.0f", custom_key="Qtd_Recria_Total") # Simplificado para recria geral
                smart_input("Vacas Pré-Parto", "Qtd. Vacas no pré parto", 8.0, 1.0, "%.0f")
                smart_input("Vacas Secas", "Qtd. Vacas secas", 4.0, 1.0, "%.0f")

        st.markdown("#### 2. Pessoal (Base Encargos)")
        with st.container(border=True):
            st.info("Preencha para calcular os 21.2% corretamente")
            c1, c2 = st.columns(2)
            with c1:
                smart_input("Salário 1 (Base)", "Ordenhador 1", 3278.88, custom_key="Sal_Base1")
                smart_input("Salário 2 (Base)", "Tratador 1", 3278.88, custom_key="Sal_Base2")
                smart_input("Bonificações (Base)", "Bonificação ordenhador 1", 2014.40, custom_key="Sal_Bonif")
            with c2:
                smart_input("Outros Salários (Sem Encargo)", "Ordenhador 2", 2459.16, custom_key="Sal_Outros")
                st.caption("Salários Base + Bonif * 21,2% = Encargos")

        st.markdown("#### 3. Nutrição e Dietas")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Preços (R$/Kg)**")
                smart_input("Conc. Lactação", "Valor Kg concentrado lactação", 2.0)
                smart_input("Conc. Pré-Parto", "Valor Kg concentrado pré parto", 2.7)
                smart_input("Ração Recria", "Valor Kg ração bezerra", 2.5)
                smart_input("Polpa/Caroço", "Valor Kg polpa cítrica", 1.6)
                smart_input("Silagem (Ton)", "Valor Ton silagem", 180.0, 1.0, "%.0f")
            with c2:
                st.markdown("**Consumo (Kg/dia)**")
                smart_input("Lactação (Ração)", "Qtd. ração por vaca lactação", 10.0, 0.1, custom_key="Kg_Lactacao")
                smart_input("Pré-Parto (Ração)", "Qtd. ração vacas no pré parto", 3.0, 0.1, custom_key="Kg_Pre")
                smart_input("Recria (Ração)", "Qtd. ração bezerra", 2.0, 0.1, custom_key="Kg_Recria")
                smart_input("Polpa (Lactação)", "Polpa", 0.0, 0.1, custom_key="Kg_Polpa")
                # Silagem Dieta
                smart_input("Silagem Lactação", "Sil_Lac", st.session_state['d_lac'], custom_key="Sil_Kg_Lac")
                smart_input("Silagem Pré", "Sil_Pre", st.session_state['d_pre'], custom_key="Sil_Kg_Pre")
                smart_input("Silagem Seca/Recria", "Sil_Seca", st.session_state['d_seca'], custom_key="Sil_Kg_Seca")

        st.markdown("#### 4. Custos Operacionais e Provisões")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                smart_input("Manutenção GEA", "GEA", 816.60)
                smart_input("Lojas Agropec", "Lojas apropec", 3324.60)
                smart_input("Alta Genetics", "Alta genetics", 782.20)
                smart_input("Outros Fixos", "Outros", 7685.80, custom_key="Outros_Fixos")
            with c2:
                smart_input("Financiamento (Mensal)", "Financ.", st.session_state['financ_total'], custom_key="Prov_Financ")
                smart_input("Adubação (Mensal)", "Adubação", 0.0, custom_key="Prov_Adubo")


# ==============================================================================
# COLUNA DIREITA: RESULTADOS (5 GRUPOS)
# ==============================================================================
with col_right:
    
    # --- CÁLCULOS MATEMÁTICOS ---
    
    # Helper para pegar inputs (mesmo ocultos)
    def get(k): return st.session_state.get(f"in_{k}", 0.0)

    # 1. PRODUÇÃO
    vacas_lac = get("Qtd. Vacas em lactação")
    prod_teorica_dia = vacas_lac * get("Litros/vaca")
    
    # Consumo Interno
    bez_amam = get("Qtd_Bezerras_Amam")
    leite_bez = get("Leite_Bezerra_Dia")
    consumo_interno_dia = bez_amam * leite_bez
    
    # Produção Entregue
    prod_entregue_dia = prod_teorica_dia - consumo_interno_dia
    prod_entregue_mes = prod_entregue_dia * 30
    prod_entregue_x2 = prod_entregue_dia * 2 
    
    # 2. RECEITA
    faturamento_bruto = prod_entregue_mes * get("Preço do leite")
    impostos = faturamento_bruto * 0.015 # 1.5% Imposto Venda
    faturamento_liquido = faturamento_bruto - impostos

    # 3. CUSTOS ALIMENTAÇÃO (DESEMBOLSO)
    custo_racao_lac = (vacas_lac * get("Kg_Lactacao") * 30) * get("Valor Kg concentrado lactação")
    custo_racao_pre = (get("Qtd. Vacas no pré parto") * get("Kg_Pre") * 30) * get("Valor Kg concentrado pré parto")
    custo_racao_recria = (get("Qtd_Recria_Total") * get("Kg_Recria") * 30) * get("Valor Kg ração bezerra")
    custo_polpa = (vacas_lac * get("Kg_Polpa") * 30) * get("Valor Kg polpa cítrica")
    
    total_concentrado = custo_racao_lac + custo_racao_pre + custo_racao_recria

    # 4. PESSOAL E ENCARGOS (A LÓGICA CHAVE)
    sal_base_encargo = get("Sal_Base1") + get("Sal_Base2") + get("Sal_Bonif")
    sal_outros = get("Sal_Outros")
    
    # Encargos (Apenas sobre a base definida)
    encargos_trabalhistas = sal_base_encargo * 0.212
    
    # Custo Pessoal (Dinheiro que sai no mês = Salários Líquidos totais)
    # Assumindo que o input já é o valor pago (líquido ou bruto acordado sem o imposto patronal)
    custo_pessoal_desembolso = sal_base_encargo + sal_outros

    # 5. DESEMBOLSO OPERACIONAL TOTAL
    desembolso_op = (total_concentrado + custo_polpa + 
                     get("GEA") + get("Lojas apropec") + get("Alta genetics") + 
                     custo_pessoal_desembolso + get("Outros_Fixos"))

    # 6. PROVISÕES (SILAGEM REPOSIÇÃO)
    # Consumo total de silagem em Kg * Preço Ton
    cons_sil_total_kg = ((vacas_lac * get("Sil_Kg_Lac")) + 
                         (get("Qtd. Vacas no pré parto") * get("Sil_Kg_Pre")) + 
                         ((get("Qtd. Vacas secas") + get("Qtd_Recria_Total")) * get("Sil_Kg_Seca"))) * 30
    
    prov_silagem = (cons_sil_total_kg / 1000) * get("Valor Ton silagem")
    prov_financ = get("Prov_Financ")
    prov_adubo = get("Prov_Adubo")

    # 7. FLUXO DE CAIXA (HIERARQUIA SOLICITADA)
    saldo_operacional = faturamento_liquido - desembolso_op
    
    # Total Provisionar (Silagem + Financ + Adubo + Encargos Trab)
    total_provisionar = prov_silagem + prov_financ + prov_adubo + encargos_trabalhistas
    
    lucro_liquido = saldo_operacional - total_provisionar

    # 8. INDICADORES FINANCEIROS
    deprec = st.session_state.get('deprec_total', 2000.0)
    ebitda = lucro_liquido + deprec + prov_financ # Definição clássica aprox
    
    custo_total_saidas = desembolso_op + total_provisionar
    custo_por_litro = custo_total_saidas / prod_entregue_mes if prod_entregue_mes > 0 else 0
    
    # PE (Margem Contribuição)
    custo_var_alim = total_concentrado + custo_polpa + prov_silagem
    margem_contrib_unit = (faturamento_liquido / prod_entregue_mes) - (custo_var_alim / prod_entregue_mes) if prod_entregue_mes > 0 else 0
    
    pe_coe = desembolso_op / margem_contrib_unit if margem_contrib_unit > 0 else 0
    pe_cot = (desembolso_op + deprec) / margem_contrib_unit if margem_contrib_unit > 0 else 0
    pe_ct = (custo_total_saidas) / margem_contrib_unit if margem_contrib_unit > 0 else 0


    # --- RENDERIZAÇÃO DOS GRUPOS ---
    if st.session_state['view_mode'] == 'resultados':
        st.header(f"📊 Resultado: {selected_scenario}")
        
        # Grupo 1: Indicadores Financeiros
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

        # Grupo 2: Desembolso Mensal
        st.markdown("##### 2. Desembolso Mensal")
        st.markdown(f"""
        <div class='sub-group'>
            <div class='result-row'><span>Concentrado Total</span><span class='result-val'>R$ {fmt(total_concentrado)}</span></div>
            <div class='result-row'><span>Polpa + Caroço</span><span class='result-val'>R$ {fmt(custo_polpa)}</span></div>
            <div class='result-row'><span>GEA (Manutenção)</span><span class='result-val'>R$ {fmt(get("GEA"))}</span></div>
            <div class='result-row'><span>Lojas Agropec.</span><span class='result-val'>R$ {fmt(get("Lojas apropec"))}</span></div>
            <div class='result-row'><span>Alta Genetics</span><span class='result-val'>R$ {fmt(get("Alta genetics"))}</span></div>
            <div class='result-row'><span>Pessoal (Líquido)</span><span class='result-val'>R$ {fmt(custo_pessoal_desembolso)}</span></div>
            <div class='result-row'><span>Outros</span><span class='result-val'>R$ {fmt(get("Outros_Fixos"))}</span></div>
            <div class='result-row' style='border-top: 1px solid #ccc; margin-top:5px; padding-top:5px;'>
                <span><b>TOTAL</b></span><span class='result-val'><b>R$ {fmt(desembolso_op)}</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Grupo 3: Fluxo de Caixa Mensal (Hierarquia Exata Solicitada)
        st.markdown("##### 3. Fluxo de Caixa Mensal")
        st.markdown(f"""
        <div class='sub-group'>
            <div class='result-row'><span>Receita Bruta (Venda Leite)</span><span class='result-val'>R$ {fmt(faturamento_liquido)}</span></div>
            <div class='result-row fc-main'><span>(+) Saldo operacional</span><span class='result-val'>R$ {fmt(saldo_operacional)}</span></div>
            <div class='result-row fc-main' style='background-color:#ffebee; color:#c62828;'><span>(-) Provisionar</span><span class='result-val'>R$ {fmt(total_provisionar)}</span></div>
            <div class='result-row fc-sub'><span>• Silagem</span><span class='result-val'>R$ {fmt(prov_silagem)}</span></div>
            <div class='result-row fc-sub'><span>• Financiamento</span><span class='result-val'>R$ {fmt(prov_financ)}</span></div>
            <div class='result-row fc-sub'><span>• Adubação</span><span class='result-val'>R$ {fmt(prov_adubo)}</span></div>
            <div class='result-row fc-sub'><span>• Encargos trabalhistas (21,2%)</span><span class='result-val'>R$ {fmt(encargos_trabalhistas)}</span></div>
            <div class='fc-final'>
                <div style='display:flex; justify-content:space-between;'>
                    <span>(=) Lucro líquido</span>
                    <span>R$ {fmt(lucro_liquido)}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Grupo 4: Indicadores de Produção
        st.markdown("##### 4. Indicadores de Produção")
        st.markdown(f"""
        <div class='sub-group'>
            <div class='result-row'><span>Vacas em lactação</span><span class='result-val'>{fmt_int(vacas_lac)}</span></div>
            <div class='result-row'><span>Litros/vaca/dia</span><span class='result-val'>{get("Litros/vaca"):.1f}</span></div>
            <div class='result-row'><span>Preço do leite</span><span class='result-val'>R$ {get("Preço do leite"):.2f}</span></div>
            <div class='result-row'><span>Produção prevista</span><span class='result-val'>{fmt_int(prod_teorica_dia*30)} L</span></div>
            <div class='result-row'><span>Produção entregue x2</span><span class='result-val'>{fmt_int(prod_entregue_x2)} L</span></div>
            <div class='result-row' style='font-weight:bold; color:#000;'><span>Produção entregue mês</span><span class='result-val'>{fmt_int(prod_entregue_mes)} L</span></div>
        </div>
        """, unsafe_allow_html=True)

        # Grupo 5: Gasto de Concentrado
        st.markdown("##### 5. Gasto de Concentrado")
        st.markdown(f"""
        <div class='sub-group'>
            <div class='result-row'><span>Concentrado lactação</span><span class='result-val'>R$ {fmt(custo_racao_lac)}</span></div>
            <div class='result-row'><span>Concentrado pré-parto</span><span class='result-val'>R$ {fmt(custo_racao_pre)}</span></div>
            <div class='result-row'><span>Concentrado recria</span><span class='result-val'>R$ {fmt(custo_racao_recria)}</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botão Download
        st.markdown("---")
        csv_data = pd.DataFrame([{'Cenário': selected_scenario, 'Lucro': lucro_liquido, 'Produção': prod_entregue_mes}]).to_csv(index=False).encode('utf-8')
        st.download_button("💾 Baixar Dados", csv_data, "resultado.csv", "text/csv")
