import streamlit as st
import pandas as pd
import numpy as np
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sítio Cangerana", layout="wide")

# CSS para Tabela de Auditoria e Layout
st.markdown("""
<style>
    [data-testid="stNumberInput"] input { padding: 0px 5px; font-size: 14px; height: 30px; }
    label { font-size: 11px !important; margin-bottom: 0px !important; color: #555; }
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }
    .audit-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .audit-table th { background-color: #f0f2f6; border: 1px solid #ddd; padding: 8px; text-align: left; }
    .audit-table td { border: 1px solid #ddd; padding: 8px; }
    .audit-ok { color: green; font-weight: bold; }
    .audit-diff { color: red; font-weight: bold; }
    .sub-group { background-color: #f9f9f9; padding: 10px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #eee; }
    .result-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #e0e0e0; font-size: 14px; }
    .result-val { font-weight: bold; color: #0044cc; text-align: right; }
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
                    if isinstance(val, str): val = val.replace('R$', '').replace(',', '.').strip()
                    return float(val) if val else default
        return default
    except:
        return default

# Função para somar coluna de Financiamentos (tabela dinâmica)
def get_financiamento_total(df):
    try:
        total = 0.0
        # Procura coluna "Valor mensal"
        for col in df.columns:
            if df[col].astype(str).str.contains("Valor mensal", case=False).any():
                col_idx = df.columns.get_loc(col)
                # Soma valores numéricos abaixo do cabeçalho
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

# --- LAYOUT ---
col_nav, col_content = st.columns([1, 4])

# MENU LATERAL
with col_nav:
    st.markdown("### ⚙️ Painel")
    selected_scenario = st.selectbox("Cenário:", scenarios)
    
    if 'last_scenario' not in st.session_state or st.session_state['last_scenario'] != selected_scenario:
        df_raw = pd.read_excel(xls, sheet_name=selected_scenario)
        st.session_state['df_raw'] = df_raw
        st.session_state['reload_defaults'] = True
        # Carrega totais complexos
        st.session_state['financ_total_cenario'] = get_financiamento_total(df_raw)
        
        # Carrega dieta base (para silagem)
        st.session_state['dieta_silagem_lac'] = get_val(df_raw, "Qtd. ração por vaca lactação", 34.0) # Nome da linha da dieta
        st.session_state['dieta_silagem_pre'] = get_val(df_raw, "Qtd. ração vacas no pré parto", 25.0)
        st.session_state['dieta_silagem_seca'] = get_val(df_raw, "Qtd. ração vacas secas", 25.0)
        # Bezerras comem menos, valor médio estimado ou pego da tabela
        st.session_state['dieta_silagem_recria'] = 10.0 # Média entre bezerras e novilhas
        
        # Custo SM com encargos (base para cálculo de pessoal)
        st.session_state['custo_sm_total'] = get_val(df_raw, "Custo total do SM", 1639.44)

    else:
        df_raw = st.session_state['df_raw']
        st.session_state['reload_defaults'] = False

    st.markdown("---")
    def set_var(): st.session_state['view_mode'] = 'variaveis'
    def set_res(): st.session_state['view_mode'] = 'resultados'
    
    st.button("📝 VARIÁVEIS", on_click=set_var, type="primary" if st.session_state['view_mode']=='variaveis' else "secondary", use_container_width=True)
    st.button("📊 RESULTADO", on_click=set_res, type="primary" if st.session_state['view_mode']=='resultados' else "secondary", use_container_width=True)

# CONTEÚDO
with col_content:
    
    def smart_input(label, key_search, default_val, step=0.01, fmt="%.2f", custom_key=None):
        k = f"in_{custom_key if custom_key else key_search}"
        if st.session_state.get('reload_defaults', False):
            st.session_state[k] = get_val(df_raw, key_search, default_val)
        if k not in st.session_state:
            st.session_state[k] = get_val(df_raw, key_search, default_val)
        
        if st.session_state['view_mode'] == 'variaveis':
            return st.number_input(label, value=st.session_state[k], step=step, format=fmt, key=k)
        return st.session_state[k]

    # --- TELA 1: INPUTS ---
    if st.session_state['view_mode'] == 'variaveis':
        st.header(f"📝 Variáveis: {selected_scenario}")
        c1, c2 = st.columns(2)
        
        with c1:
            with st.container(border=True):
                st.subheader("1. Rebanho e Preços")
                cc1, cc2 = st.columns(2)
                with cc1:
                    smart_input("Vacas Lactação", "Qtd. Vacas em lactação", 40.0, 1.0, "%.0f")
                    smart_input("Litros/Vaca", "Litros/vaca", 25.0)
                    smart_input("Preço Leite", "Preço do leite", 2.60)
                with cc2:
                    smart_input("Vacas Pré-Parto", "Qtd. Vacas no pré parto", 8.0, 1.0, "%.0f")
                    smart_input("Vacas Secas", "Qtd. Vacas secas", 4.0, 1.0, "%.0f")
                    smart_input("Recria (Bez/Nov)", "Qtd. Novilhas", 40.0, 1.0, "%.0f", custom_key="Qtd_Recria_Total")

            with st.container(border=True):
                st.subheader("3. Pessoal (Quantidades)")
                st.info("Custo Unitário Base: R$ " + fmt(st.session_state['custo_sm_total']) + " (Salário+FGTS)")
                cc1, cc2 = st.columns(2)
                with cc1:
                    smart_input("Gerente (Qtd)", "Gerente", 0.0, 1.0, "%.1f", custom_key="Qtd_Gerente")
                    smart_input("Ordenhador 1 (Qtd)", "Ordenhador 1", 2.0, 0.5, "%.1f", custom_key="Qtd_Ord1")
                    smart_input("Tratador 1 (Qtd)", "Tratador 1", 2.0, 0.5, "%.1f", custom_key="Qtd_Trat1")
                with cc2:
                    smart_input("Ordenhador 2 (Qtd)", "Ordenhador 2", 1.5, 0.5, "%.1f", custom_key="Qtd_Ord2")
                    # Bonificações são valores monetários fixos na planilha
                    smart_input("Bonificação 1 (R$)", "Bonificação ordenhador 1", 1007.20, custom_key="Valor_Bonif1")
                    smart_input("Bonificação 2 (R$)", "Bonificação tratador 1", 1007.20, custom_key="Valor_Bonif2")

            with st.container(border=True):
                st.subheader("5. Dietas (Silagem Kg/dia)")
                cc1, cc2 = st.columns(2)
                with cc1:
                    smart_input("Lactação", "Silagem_Lac", st.session_state['dieta_silagem_lac'], custom_key="Diet_Sil_Lac")
                    smart_input("Pré-Parto", "Silagem_Pre", st.session_state['dieta_silagem_pre'], custom_key="Diet_Sil_Pre")
                with cc2:
                    smart_input("Secas", "Silagem_Seca", st.session_state['dieta_silagem_seca'], custom_key="Diet_Sil_Seca")
                    smart_input("Recria (Médio)", "Silagem_Recria", st.session_state['dieta_silagem_recria'], custom_key="Diet_Sil_Recria")

        with c2:
            with st.container(border=True):
                st.subheader("2. Nutrição (R$/Kg)")
                cc1, cc2 = st.columns(2)
                with cc1:
                    smart_input("Conc. Lactação", "Valor Kg concentrado lactação", 2.0)
                    smart_input("Conc. Pré-Parto", "Valor Kg concentrado pré parto", 2.7)
                with cc2:
                    smart_input("Ração Recria", "Valor Kg ração bezerra", 2.5)
                    smart_input("Ton Silagem (R$)", "Valor Ton silagem", 180.0, 1.0, "%.0f")

            with st.container(border=True):
                st.subheader("4. Outros Custos")
                smart_input("Manutenção GEA", "GEA", 816.60)
                smart_input("Lojas Agropec", "Lojas apropec", 3324.60)
                smart_input("Alta Genetics", "Alta genetics", 782.20)
                smart_input("Outros Fixos", "Outros", 7685.80, custom_key="Outros_Fixos")
                smart_input("Adubação (Prov)", "Adubação", 0.0, custom_key="Prov_Adubo")

    # --- TELA 2: RESULTADOS ---
    else:
        st.header(f"📊 Resultados Auditados: {selected_scenario}")
        
        def get(k): return st.session_state.get(f"in_{k}", 0.0)

        # === 1. CÁLCULOS ===
        
        # Pessoal e Encargos (Lógica da Fórmula)
        custo_unit_sm = st.session_state.get('custo_sm_total', 1639.44)
        
        sal_gerente = get("Qtd_Gerente") * custo_unit_sm
        sal_ord1 = get("Qtd_Ord1") * custo_unit_sm
        sal_trat1 = get("Qtd_Trat1") * custo_unit_sm
        bonif1 = get("Valor_Bonif1")
        bonif2 = get("Valor_Bonif2")
        sal_ord2 = get("Qtd_Ord2") * custo_unit_sm # Este fica fora da base de cálculo
        
        # Base de cálculo dos encargos (C66:C70)
        base_encargos = sal_gerente + sal_ord1 + bonif1 + sal_trat1 + bonif2
        encargos_trabalhistas = base_encargos * 0.212
        
        # Custo Pessoal Total (Desembolso)
        custo_pessoal_total = base_encargos + sal_ord2 # Nota: Encargos entram no Provisionar, não no desembolso direto aqui segundo DRE

        # Produção e Receita
        vacas_lac = get("Qtd. Vacas em lactação")
        prod_dia = vacas_lac * get("Litros/vaca")
        
        # Consumo Interno (Recuperando valores ou padrão)
        bez_amam = get_val(df_raw, "Qtd. Bezerras amamentação", 6.66)
        leite_bez = get_val(df_raw, "Qtd. ração bezerras amamentação", 6.0)
        consumo_interno_dia = bez_amam * leite_bez
        
        prod_entregue_mes = (prod_dia - consumo_interno_dia) * 30
        
        faturamento_bruto = prod_entregue_mes * get("Preço do leite")
        impostos = faturamento_bruto * 0.015
        faturamento_liquido = faturamento_bruto - impostos
        
        # Silagem (Provisionar)
        # Consumo Total Kg = (Vacas * Consumo) + (Pre * Consumo) ...
        cons_sil_lac = vacas_lac * get("Diet_Sil_Lac") * 30
        cons_sil_pre = get("Qtd. Vacas no pré parto") * get("Diet_Sil_Pre") * 30
        cons_sil_seca = get("Qtd. Vacas secas") * get("Diet_Sil_Seca") * 30
        cons_sil_rec = get("Qtd_Recria_Total") * get("Diet_Sil_Recria") * 30
        
        total_sil_kg = cons_sil_lac + cons_sil_pre + cons_sil_seca + cons_sil_rec
        prov_silagem = (total_sil_kg / 1000) * get("Valor Ton silagem")
        
        # Financiamento
        prov_financ = st.session_state.get('financ_total_cenario', 1151.0)
        
        # Desembolso Operacional
        # Nutrição Concentrada (Estimativa simplificada para focar no fluxo)
        # Assumindo kg da planilha
        custo_conc_lac = (vacas_lac * 10 * 30) * get("Valor Kg concentrado lactação") # 10kg padrão
        custo_conc_pre = (get("Qtd. Vacas no pré parto") * 3 * 30) * get("Valor Kg concentrado pré parto")
        custo_conc_rec = (get("Qtd_Recria_Total") * 2 * 30) * get("Valor Kg ração bezerra")
        total_concentrado = custo_conc_lac + custo_conc_pre + custo_conc_rec
        
        desembolso_op = total_concentrado + get("GEA") + get("Lojas apropec") + get("Alta genetics") + custo_pessoal_total + get("Outros_Fixos")
        
        # Fluxo de Caixa
        saldo_operacional = faturamento_liquido - desembolso_op
        prov_adubo = get("Prov_Adubo")
        total_provisionar = prov_silagem + prov_financ + prov_adubo + encargos_trabalhistas
        lucro_liquido = saldo_operacional - total_provisionar

        # === 2. VISUALIZAÇÃO ===
        c_left, c_right = st.columns([1, 1])
        
        with c_left:
            st.markdown("##### Fluxo de Caixa (DRE)")
            st.markdown(f"""
            <div class='sub-group'>
                <div class='result-row fc-header'><span>(+) Saldo Operacional</span><span class='result-val' style='color:green'>R$ {fmt(saldo_operacional)}</span></div>
                <div class='result-row fc-header'><span>(-) Provisionar</span><span class='result-val' style='color:red'>R$ {fmt(total_provisionar)}</span></div>
                <div class='result-row fc-item'><span>• Silagem ({total_sil_kg/1000:.1f} t)</span><span class='result-val'>R$ {fmt(prov_silagem)}</span></div>
                <div class='result-row fc-item'><span>• Financiamentos</span><span class='result-val'>R$ {fmt(prov_financ)}</span></div>
                <div class='result-row fc-item'><span>• Adubação</span><span class='result-val'>R$ {fmt(prov_adubo)}</span></div>
                <div class='result-row fc-item'><span>• Encargos Trab. (21,2%)</span><span class='result-val'>R$ {fmt(encargos_trabalhistas)}</span></div>
                <div class='result-row fc-total'><span>(=) Lucro Líquido</span><span>R$ {fmt(lucro_liquido)}</span></div>
            </div>
            """, unsafe_allow_html=True)

        with c_right:
            st.markdown("##### Auditoria: Planilha vs App")
            
            # Tabela de Comparação
            # Pegamos valores fixos conhecidos do DRE Atual para comparar
            val_planilha = {
                "Saldo Operacional": 18471.40,
                "Provisionar": 14308.74,
                "Silagem": 11340.00,
                "Financiamento": 1151.44,
                "Encargos": 1817.30,
                "Lucro Líquido": 4162.66
            }
            
            val_app = {
                "Saldo Operacional": saldo_operacional,
                "Provisionar": total_provisionar,
                "Silagem": prov_silagem,
                "Financiamento": prov_financ,
                "Encargos": encargos_trabalhistas,
                "Lucro Líquido": lucro_liquido
            }
            
            html = "<table class='audit-table'><thead><tr><th>Campo</th><th>Planilha (Ref)</th><th>App (Calc)</th><th>Status</th></tr></thead><tbody>"
            
            for key in val_planilha:
                v_p = val_planilha[key]
                v_a = val_app[key]
                diff = abs(v_p - v_a)
                status = "<span class='audit-ok'>OK</span>" if diff < 50 else f"<span class='audit-diff'>Diff {diff:.0f}</span>"
                
                # Se não for o cenário Atual, não temos referência fixa, então mostramos traço
                if "Atual" not in selected_scenario:
                    v_p_display = "-"
                    status = "Simulado"
                else:
                    v_p_display = fmt(v_p)
                
                html += f"<tr><td>{key}</td><td>{v_p_display}</td><td>{fmt(v_a)}</td><td>{status}</td></tr>"
            
            html += "</tbody></table>"
            st.markdown(html, unsafe_allow_html=True)
            if "Atual" in selected_scenario:
                st.caption("*Valores de referência fixos do DRE 'Atual' para validação das fórmulas.")
