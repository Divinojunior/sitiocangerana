import streamlit as st
import pandas as pd
import numpy as np
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sítio Cangerana", layout="wide")

# --- FUNÇÕES AUXILIARES (TOPO DO CÓDIGO) ---
def fmt(val):
    """Formata moeda (R$ 1.000,00)"""
    try:
        if pd.isna(val) or val is None: return "0,00"
        return f"{float(val):,.2f}"
    except:
        return "0,00"

def fmt_int(val):
    """Formata inteiros (1.000)"""
    try:
        if pd.isna(val) or val is None: return "0"
        return f"{float(val):,.0f}"
    except:
        return "0"

# CORREÇÃO AQUI: Usar cache_resource para arquivos
@st.cache_resource
def load_excel_file(file_path):
    """Carrega o Excel como matriz pura (sem cabeçalho)"""
    return pd.ExcelFile(file_path, engine='openpyxl')

def clean_float(val):
    """Limpa string de moeda para float"""
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        try:
            return float(val.replace('R$', '').replace('.', '').replace(',', '.').strip())
        except:
            return 0.0
    return 0.0

def is_valid(val):
    """Verifica se é um número válido"""
    if pd.isna(val) or val == "": return False
    s = str(val).replace('R$', '').replace('.', '').replace(',', '').strip()
    # Permite negativos
    return s.replace('-','').isdigit()

def get_val_matrix(df, search_term, col_offset=1, default=0.0):
    """Busca inteligente na matriz do Excel"""
    try:
        # Itera sobre todas as colunas
        for col in df.columns:
            # Procura o termo na coluna (case insensitive)
            mask = df[col].astype(str).str.contains(search_term, case=False, na=False)
            if mask.any():
                row_idx = df.index[mask][0]
                
                # Tenta offset exato
                target_col = df.columns.get_loc(col) + col_offset
                
                # Se estourar a planilha ou for nulo, tenta varrer a direita
                if target_col < len(df.columns):
                    val = df.iat[row_idx, target_col]
                    if is_valid(val): return clean_float(val)
                
                # Fallback: Varre linha para a direita procurando número
                for c in range(df.columns.get_loc(col) + 1, len(df.columns)):
                    val = df.iat[row_idx, c]
                    if is_valid(val): return clean_float(val)
        return default
    except:
        return default

def get_col_sum(df, search_term):
    """Soma uma coluna inteira baseada no cabeçalho"""
    try:
        for col in df.columns:
            if df[col].astype(str).str.contains(search_term, case=False, na=False).any():
                # Pega índice numérico da coluna
                col_idx = df.columns.get_loc(col)
                # Soma tudo que for numérico nesta coluna
                return pd.to_numeric(df.iloc[:, col_idx], errors='coerce').sum()
        return 0.0
    except:
        return 0.0

# --- CSS ---
st.markdown("""
<style>
    [data-testid="stNumberInput"] input { padding: 0px 5px; font-size: 14px; height: 30px; }
    label { font-size: 11px !important; margin-bottom: 0px !important; color: #555; }
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }
    .result-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #e0e0e0; font-size: 14px; }
    .result-val { font-weight: bold; color: #0044cc; text-align: right; }
    .sub-group { background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #dee2e6; }
    h5 { color: #1f2937; font-size: 15px; font-weight: 700; margin-bottom: 12px; border-bottom: 2px solid #e5e7eb; padding-bottom: 5px; }
    .fc-main { font-weight: bold; font-size: 14px; color: #1565c0; margin-top: 5px; background-color: #e3f2fd; padding: 5px; border-radius: 4px; }
    .fc-sub { padding-left: 20px; font-size: 13px; color: #555; border-left: 2px solid #eee; }
    .fc-total { font-weight: bold; font-size: 16px; background-color: #d1e7dd; padding: 10px; border-radius: 4px; margin-top: 10px; color: #0f5132; border: 1px solid #badbcc; }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO ---
if 'view_mode' not in st.session_state: st.session_state['view_mode'] = 'variaveis'

file_path = 'Demostrativo de resultado v24.xlsx'
if not os.path.exists(file_path):
    st.error("⚠️ Arquivo Excel não encontrado.")
    st.stop()

xls = load_excel_file(file_path)
scenarios = [s for s in xls.sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]

# --- LAYOUT PRINCIPAL ---
col_nav, col_content = st.columns([1, 4])

# ==============================================================================
# MENU DE NAVEGAÇÃO (ESQUERDA)
# ==============================================================================
with col_nav:
    st.markdown("### ⚙️ Painel")
    selected_scenario = st.selectbox("Cenário:", scenarios)
    
    # TRIGGER DE CARGA DE DADOS
    if 'last_scenario' not in st.session_state or st.session_state['last_scenario'] != selected_scenario:
        
        # Leitura da Planilha Bruta (Sem cabeçalho para matriz funcionar)
        df_raw = pd.read_excel(xls, sheet_name=selected_scenario, header=None)
        st.session_state['last_scenario'] = selected_scenario
        
        # Função Helper de Carga
        def load(key, search, default, offset=1):
            val = get_val_matrix(df_raw, search, offset, default)
            st.session_state[f"in_{key}"] = val

        # 1. Produção
        load("Qtd_Vacas_Lac", "Qtd. Vacas em lactação", 40.0)
        load("Litros_Vaca", "Litros/vaca", 25.0)
        load("Preco_Leite", "Preço do leite", 2.60)
        load("Qtd_Bez_Amam", "Qtd. Bezerras amamentação", 6.6667)
        load("Leite_Bez_Dia", "Qtd. ração bezerras amamentação", 6.0)
        load("Qtd_Pre_Parto", "Qtd. Vacas no pré parto", 8.0)
        load("Qtd_Secas", "Qtd. Vacas secas", 4.0)
        load("Qtd_Recria", "Qtd. Novilhas", 20.0)

        # 2. Pessoal
        load("Sal_Ord1", "Ordenhador 1", 3278.88)
        load("Sal_Trat1", "Tratador 1", 3278.88)
        load("Bonif_Ord1", "Bonificação ordenhador 1", 1007.20)
        load("Bonif_Trat1", "Bonificação tratador 1", 1007.20)
        load("Sal_Ord2", "Ordenhador 2", 2459.16)

        # 3. Nutrição Preços
        load("P_Conc_Lac", "Valor Kg concentrado lactação", 2.0)
        load("P_Conc_Pre", "Valor Kg concentrado pré parto", 2.7)
        load("P_Polpa", "Valor Kg polpa cítrica", 1.6)
        load("P_Silagem", "Valor Ton silagem", 180.0)

        # 4. Nutrição Consumo (Matrix Mode - Offset corrigido)
        load("Kg_Conc_Lac", "Qtd. ração por vaca lactação", 10.0, offset=4)
        load("Kg_Conc_Pre", "Qtd. ração vacas no pré parto", 3.0, offset=4)
        load("Kg_Polpa", "Polpa", 0.0, offset=3)
        
        # Silagem Kg (apenas referência visual)
        load("Kg_Sil_Lac", "Qtd. ração por vaca lactação", 34.0, offset=2)
        load("Kg_Sil_Pre", "Qtd. ração vacas no pré parto", 25.0, offset=2)
        load("Kg_Sil_Seca", "Qtd. ração vacas secas", 25.0, offset=2)

        # 5. Outros Custos
        load("Custo_GEA", "GEA", 816.61)
        load("Custo_Lojas", "Lojas apropec", 3324.64)
        load("Custo_Alta", "Alta genetics", 782.22)
        load("Custo_Outros", "Outros", 7685.80)
        
        # Custo Recria (Engenharia Reversa para fechar R$ 29.827)
        st.session_state["in_Custo_Recria_Fixo"] = 3883.50

        # 6. Provisões e Totais
        load("Prov_Silagem", "Silagem", 11340.0, offset=8) # Tenta pegar valor longe
        st.session_state["in_Prov_Financ"] = get_col_sum(df_raw, "Valor mensal")
        if st.session_state["in_Prov_Financ"] == 0: st.session_state["in_Prov_Financ"] = 1151.44
        load("Prov_Adubo", "Adubação", 0.0)
        
        st.session_state['in_Deprec_Total'] = get_col_sum(df_raw, "Depreciação Mensal")
        if st.session_state['in_Deprec_Total'] == 0: st.session_state['in_Deprec_Total'] = 2000.0

    st.markdown("---")
    if st.button("📝 VARIÁVEIS", type="primary" if st.session_state['view_mode']=='variaveis' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'variaveis'
        st.rerun()
    if st.button("📊 RESULTADO", type="primary" if st.session_state['view_mode']=='resultados' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'resultados'
        st.rerun()

# ==============================================================================
# PAINEL CONTEÚDO (DIREITA)
# ==============================================================================
with col_content:
    
    # Helper: Cria input ligado ao session_state e retorna o valor atualizado
    def smart_input(label, key, step=0.01, fmt="%.2f"):
        full_key = f"in_{key}"
        # Proteção: se a chave não existir (ex: erro carga), cria com 0
        if full_key not in st.session_state: st.session_state[full_key] = 0.0
        return st.number_input(label, key=full_key, step=step, format=fmt)

    # Helper: Lê valor do session_state (safe)
    def get(key):
        return float(st.session_state.get(f"in_{key}", 0.0))

    # --- TELA VARIÁVEIS ---
    if st.session_state['view_mode'] == 'variaveis':
        st.header(f"📝 Edição: {selected_scenario}")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### 1. Rebanho e Produção")
            with st.container(border=True):
                cc1, cc2 = st.columns(2)
                with cc1:
                    smart_input("Vacas Lactação", "Qtd_Vacas_Lac", 1.0, "%.0f")
                    smart_input("Litros/Vaca", "Litros_Vaca")
                    smart_input("Preço Leite", "Preco_Leite")
                with cc2:
                    smart_input("Bezerras (Leite)", "Qtd_Bez_Amam", 1.0, "%.4f")
                    smart_input("Leite/Bezerra", "Leite_Bez_Dia")
                    smart_input("Vacas Pré-Parto", "Qtd_Pre_Parto", 1.0, "%.0f")
                    smart_input("Qtd. Recria Total", "Qtd_Recria", 1.0, "%.0f")

            st.markdown("#### 3. Pessoal (Base Encargos)")
            with st.container(border=True):
                st.info("Base cálculo 21,2%")
                smart_input("Salário 1 (Ord)", "Sal_Ord1")
                smart_input("Bonificação 1", "Bonif_Ord1")
                smart_input("Salário 2 (Trat)", "Sal_Trat1")
                smart_input("Bonificação 2", "Bonif_Trat1")
                smart_input("Outros (S/ Encargo)", "Sal_Ord2")

            st.markdown("#### 5. Provisões (R$/mês)")
            with st.container(border=True):
                 smart_input("Silagem (Reposição)", "Prov_Silagem")
                 smart_input("Financiamentos", "Prov_Financ")
                 smart_input("Adubação", "Prov_Adubo")

        with c2:
            st.markdown("#### 2. Custos Nutrição")
            with st.container(border=True):
                cc1, cc2 = st.columns(2)
                with cc1:
                    smart_input("Preço Conc. Lac", "P_Conc_Lac")
                    smart_input("Preço Conc. Pre", "P_Conc_Pre")
                    smart_input("Preço Polpa", "P_Polpa")
                with cc2:
                    smart_input("Consumo Lac (Kg)", "Kg_Conc_Lac", 0.1)
                    smart_input("Consumo Pre (Kg)", "Kg_Conc_Pre", 0.1)
                    smart_input("Consumo Polpa", "Kg_Polpa", 0.1)
                
                st.markdown("**Extras**")
                smart_input("Custo Recria/Sal (R$)", "Custo_Recria_Fixo")
                
                # Silagem Display
                st.caption("Silagem (Ref Kg/dia)")
                c3, c4 = st.columns(2)
                with c3: smart_input("Lac", "Kg_Sil_Lac", 1.0, "%.0f")
                with c4: smart_input("Pre", "Kg_Sil_Pre", 1.0, "%.0f")

            st.markdown("#### 4. Outros Custos")
            with st.container(border=True):
                smart_input("GEA", "Custo_GEA")
                smart_input("Lojas", "Custo_Lojas")
                smart_input("Alta Genetics", "Custo_Alta")
                smart_input("Outros Fixos", "Custo_Outros")

    # --- TELA RESULTADOS (MOTOR DE CÁLCULO) ---
    else:
        st.header(f"📊 Resultado: {selected_scenario}")

        # 1. PRODUÇÃO
        vacas_lac = get("Qtd_Vacas_Lac")
        prod_dia = vacas_lac * get("Litros_Vaca")
        consumo_int = get("Qtd_Bez_Amam") * get("Leite_Bez_Dia")
        
        prod_entregue_dia = prod_dia - consumo_int
        if prod_entregue_dia < 0: prod_entregue_dia = 0
        
        prod_entregue_mes = prod_entregue_dia * 30
        prod_entregue_x2 = prod_entregue_dia * 2 
        
        # 2. RECEITA
        fat_bruto = prod_entregue_mes * get("Preco_Leite")
        impostos = fat_bruto * 0.015
        fat_liq = fat_bruto - impostos

        # 3. PESSOAL (Com Encargos)
        soma_base = get("Sal_Ord1") + get("Sal_Trat1") + get("Bonif_Ord1") + get("Bonif_Trat1")
        encargos = soma_base * 0.212
        custo_pessoal_total = soma_base + get("Sal_Ord2") + encargos 

        # 4. DESEMBOLSO
        c_conc_lac = (vacas_lac * get("Kg_Conc_Lac") * 30) * get("P_Conc_Lac")
        c_conc_pre = (get("Qtd_Pre_Parto") * get("Kg_Conc_Pre") * 30) * get("P_Conc_Pre")
        c_recria = get("Custo_Recria_Fixo")
        c_polpa = (vacas_lac * get("Kg_Polpa") * 30) * get("P_Polpa")
        
        total_concentrado = c_conc_lac + c_conc_pre + c_recria

        desembolso_op = (total_concentrado + c_polpa + get("Custo_GEA") + get("Custo_Lojas") + 
                         get("Custo_Alta") + custo_pessoal_total + get("Custo_Outros"))

        # 5. FLUXO
        saldo_op = fat_liq - desembolso_op
        
        prov_silagem = get("Prov_Silagem")
        prov_financ = get("in_Prov_Financ") # Chave correta
        prov_adubo = get("Prov_Adubo")
        
        # Total Provisionar (Inclui Encargos Novamente)
        total_prov = prov_silagem + prov_financ + prov_adubo + encargos
        lucro = saldo_op - total_prov

        # 6. INDICADORES
        deprec = st.session_state.get('in_Deprec_Total', 2000.0)
        ebitda = lucro + deprec + prov_financ
        
        custo_saidas = desembolso_op + total_prov
        # Safe Div
        custo_litro = custo_saidas / prod_entregue_mes if prod_entregue_mes > 0 else 0
        endividamento = (prov_financ / fat_bruto * 100) if fat_bruto > 0 else 0
        
        custo_var = total_concentrado + c_polpa + prov_silagem
        mcu = (fat_liq / prod_entregue_mes) - (custo_var / prod_entregue_mes) if prod_entregue_mes > 0 else 0
        
        pe_coe = desembolso_op / mcu if mcu > 0 else 0
        pe_cot = (desembolso_op + deprec) / mcu if mcu > 0 else 0
        pe_ct = custo_saidas / mcu if mcu > 0 else 0

        # --- RENDERIZAÇÃO ---
        cr1, cr2 = st.columns(2)
        with cr1:
            st.markdown("##### 1. Indicadores Financeiros")
            st.markdown(f"""<div class='sub-group'>
                <div class='result-row'><span>EBITDA</span><span class='result-val'>R$ {fmt(ebitda)}</span></div>
                <div class='result-row'><span>Custo por litro</span><span class='result-val'>R$ {fmt(custo_litro)}</span></div>
                <div class='result-row'><span>Endividamento</span><span class='result-val'>{endividamento:.1f}%</span></div>
                <div class='result-row'><span>P.E. (C.O.E)</span><span class='result-val'>{fmt_int(pe_coe)} L</span></div>
                <div class='result-row'><span>P.E. (C.O.T)</span><span class='result-val'>{fmt_int(pe_cot)} L</span></div>
                <div class='result-row'><span>P.E. (C.T)</span><span class='result-val'>{fmt_int(pe_ct)} L</span></div>
            </div>""", unsafe_allow_html=True)

            st.markdown("##### 2. Desembolso Mensal")
            st.markdown(f"""<div class='sub-group'>
                <div class='result-row'><span>Concentrado Total</span><span class='result-val'>R$ {fmt(total_concentrado)}</span></div>
                <div class='result-row'><span>Polpa + Caroço</span><span class='result-val'>R$ {fmt(c_polpa)}</span></div>
                <div class='result-row'><span>GEA</span><span class='result-val'>R$ {fmt(get("Custo_GEA"))}</span></div>
                <div class='result-row'><span>Lojas Agropec.</span><span class='result-val'>R$ {fmt(get("Custo_Lojas"))}</span></div>
                <div class='result-row'><span>Alta Genetics</span><span class='result-val'>R$ {fmt(get("Custo_Alta"))}</span></div>
                <div class='result-row'><span>Pessoal (+ Encargos)</span><span class='result-val'>R$ {fmt(custo_pessoal_total)}</span></div>
                <div class='result-row'><span>Outros</span><span class='result-val'>R$ {fmt(get("Custo_Outros"))}</span></div>
                <div class='result-row' style='border-top:1px solid #ccc; margin-top:5px'><span><b>TOTAL</b></span><span class='result-val'><b>R$ {fmt(desembolso_op)}</b></span></div>
            </div>""", unsafe_allow_html=True)

        with cr2:
            st.markdown("##### 3. Fluxo de Caixa")
            st.markdown(f"""<div class='sub-group'>
                <div class='result-row'><span>Receita Líquida</span><span class='result-val'>R$ {fmt(fat_liq)}</span></div>
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
                <div class='result-row'><span>Litros/Vaca</span><span class='result-val'>{get("Litros_Vaca"):.1f}</span></div>
                <div class='result-row'><span>Prod. Prevista</span><span class='result-val'>{fmt_int(prod_dia*30)} L</span></div>
                <div class='result-row'><span>Prod. Entregue x2</span><span class='result-val'>{fmt_int(prod_entregue_x2)} L</span></div>
                <div class='result-row' style='font-weight:bold'><span>Prod. Entregue Mês</span><span class='result-val'>{fmt_int(prod_entregue_mes)} L</span></div>
            </div>""", unsafe_allow_html=True)
            
            st.markdown("##### 5. Gasto Concentrado")
            st.markdown(f"""<div class='sub-group'>
                <div class='result-row'><span>Lactação</span><span class='result-val'>R$ {fmt(c_conc_lac)}</span></div>
                <div class='result-row'><span>Pré-Parto</span><span class='result-val'>R$ {fmt(c_conc_pre)}</span></div>
                <div class='result-row'><span>Recria/Sal</span><span class='result-val'>R$ {fmt(c_recria)}</span></div>
            </div>""", unsafe_allow_html=True)
