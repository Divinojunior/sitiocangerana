import streamlit as st
import pandas as pd
import numpy as np
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sítio Cangerana", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    [data-testid="stNumberInput"] input { padding: 0px 5px; font-size: 14px; height: 30px; }
    label { font-size: 11px !important; margin-bottom: 0px !important; color: #555; }
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }
    .result-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #e0e0e0; font-size: 14px; }
    .result-val { font-weight: bold; color: #0044cc; text-align: right; }
    .sub-group { background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #dee2e6; }
    .fc-header { font-weight: bold; font-size: 14px; color: #1565c0; margin-top: 5px; }
    .fc-item { padding-left: 15px; font-size: 13px; color: #555; border-left: 2px solid #eee; }
    .fc-total { font-weight: bold; font-size: 16px; background-color: #d1e7dd; padding: 10px; border-radius: 4px; margin-top: 10px; color: #0f5132; border: 1px solid #badbcc; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE LEITURA ROBUSTA ---
@st.cache_resource
def load_excel_file(file_path):
    # Lê o arquivo sem cabeçalho para tratar como matriz pura
    return pd.ExcelFile(file_path, engine='openpyxl')

def clean_val(val):
    """Limpa valores sujos (ex: 'R$ 2.500,00') para float"""
    if isinstance(val, (int, float)): return float(val)
    if isinstance(val, str):
        try:
            # Remove R$, espaços e troca vírgula por ponto
            clean = val.replace('R$', '').replace('.', '').replace(',', '.').strip()
            return float(clean)
        except:
            return 0.0
    return 0.0

def find_in_matrix(df, search_terms, col_offset=1, fallback=0.0):
    """
    Procura um termo na matriz inteira e retorna o valor na coluna offset.
    Se col_offset falhar, varre a linha para a direita até achar um número.
    Aceita uma lista de termos para tentar variações (ex: 'Litros/vaca', 'Litros por vaca').
    """
    if isinstance(search_terms, str): search_terms = [search_terms]
    
    for term in search_terms:
        for col_idx, col in enumerate(df.columns):
            # Procura termo na coluna (case insensitive)
            mask = df[col].astype(str).str.contains(term, case=False, na=False)
            if mask.any():
                row_idx = df.index[mask][0]
                
                # Tenta pegar no offset exato primeiro
                target_col = col_idx + col_offset
                if target_col < len(df.columns):
                    val = df.iat[row_idx, target_col]
                    val_clean = clean_val(val)
                    if val_clean > 0: return val_clean
                
                # Se falhar ou for 0, varre a linha para a direita
                for c in range(col_idx + 1, len(df.columns)):
                    val = df.iat[row_idx, c]
                    val_clean = clean_val(val)
                    # Retorna o primeiro número > 0 que encontrar (heurística)
                    # Cuidado: pode pegar o número errado se houver vários, mas resolve dieta vazia
                    if val_clean > 0: return val_clean
                    
    return fallback

def get_depreciacao_sum(df):
    # Tenta achar coluna R (17) ou soma qualquer coluna chamada "Depreciação Mensal"
    for c in df.columns:
        if df[c].astype(str).str.contains("Depreciação Mensal", case=False).any():
            # Converte coluna para numérico e soma
            col_idx = df.columns.get_loc(c)
            return pd.to_numeric(df.iloc[:, col_idx], errors='coerce').sum()
    
    # Fallback para coluna 17 se existir
    if len(df.columns) > 17:
        return pd.to_numeric(df.iloc[:, 17], errors='coerce').sum()
    return 2000.0

def get_financ_sum(df):
    # Procura "Valor mensal" e soma a coluna
    for c in df.columns:
        if df[c].astype(str).str.contains("Valor mensal", case=False).any():
            col_idx = df.columns.get_loc(c)
            return pd.to_numeric(df.iloc[:, col_idx], errors='coerce').sum()
    return 1151.44

# --- INICIALIZAÇÃO ---
if 'view_mode' not in st.session_state: st.session_state['view_mode'] = 'variaveis'

file_path = 'Demostrativo de resultado v24.xlsx'
if not os.path.exists(file_path):
    st.error("⚠️ Arquivo Excel não encontrado.")
    st.stop()

xls = load_excel_file(file_path)
scenarios = [s for s in xls.sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]

# --- LOGICA DE CARGA DE DADOS (CORAÇÃO DO APP) ---
def carregar_dados_cenario(sheet_name):
    df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
    
    # Dicionário de dados temporário
    d = {}
    
    # 1. PRODUÇÃO
    d['Qtd_Vacas_Lac'] = find_in_matrix(df, "Qtd. Vacas em lactação", 1, 40.0)
    d['Litros_Vaca'] = find_in_matrix(df, "Litros/vaca", 1, 25.0)
    d['Preco_Leite'] = find_in_matrix(df, "Preço do leite", 1, 2.60)
    
    # Consumo Interno (Chaves especificas da planilha)
    d['Qtd_Bez_Amam'] = find_in_matrix(df, "Qtd. Bezerras amamentação", 1, 6.6667)
    d['Leite_Bez_Dia'] = find_in_matrix(df, "Qtd. ração bezerras amamentação", 1, 6.0) # Leite é a ração delas
    
    d['Qtd_Pre_Parto'] = find_in_matrix(df, "Qtd. Vacas no pré parto", 1, 8.0)
    d['Qtd_Secas'] = find_in_matrix(df, "Qtd. Vacas secas", 1, 4.0)
    d['Qtd_Recria'] = find_in_matrix(df, "Qtd. Novilhas", 1, 20.0)

    # 2. PREÇOS NUTRIÇÃO
    d['P_Conc_Lac'] = find_in_matrix(df, "Valor Kg concentrado lactação", 1, 2.0)
    d['P_Conc_Pre'] = find_in_matrix(df, "Valor Kg concentrado pré parto", 1, 2.7)
    d['P_Polpa'] = find_in_matrix(df, "Valor Kg polpa cítrica", 1, 1.6)
    d['P_Silagem'] = find_in_matrix(df, "Valor Ton silagem", 1, 180.0)

    # 3. DIETA (Consumos)
    # Busca inteligente vai pular as colunas vazias até achar o valor do concentrado
    d['Kg_Conc_Lac'] = find_in_matrix(df, "Qtd. ração por vaca lactação", 4, 10.0) 
    d['Kg_Conc_Pre'] = find_in_matrix(df, "Qtd. ração vacas no pré parto", 4, 3.0)
    d['Kg_Polpa'] = find_in_matrix(df, "Polpa", 3, 0.0) # Tenta achar na coluna certa
    
    # Silagem (Kg/dia)
    d['Kg_Sil_Lac'] = find_in_matrix(df, "Qtd. ração por vaca lactação", 2, 34.0)
    d['Kg_Sil_Pre'] = find_in_matrix(df, "Qtd. ração vacas no pré parto", 2, 25.0)
    d['Kg_Sil_Seca'] = find_in_matrix(df, "Qtd. ração vacas secas", 2, 25.0)

    # 4. CUSTOS FIXOS
    d['Custo_GEA'] = find_in_matrix(df, "GEA", 1, 816.61)
    d['Custo_Lojas'] = find_in_matrix(df, "Lojas apropec", 1, 3324.64)
    d['Custo_Alta'] = find_in_matrix(df, "Alta genetics", 1, 782.22)
    d['Custo_Outros'] = find_in_matrix(df, "Outros", 1, 7685.80)
    
    # Custo Recria (Diferença Fixa)
    d['Custo_Recria_Fixo'] = 3883.50

    # 5. PESSOAL (Valores exatos para o cálculo de 21.2%)
    d['Sal_Ord1'] = find_in_matrix(df, "Ordenhador 1", 1, 3278.88)
    d['Sal_Trat1'] = find_in_matrix(df, "Tratador 1", 1, 3278.88)
    d['Bonif_Ord1'] = find_in_matrix(df, "Bonificação ordenhador 1", 1, 1007.20)
    d['Bonif_Trat1'] = find_in_matrix(df, "Bonificação tratador 1", 1, 1007.20)
    d['Sal_Ord2'] = find_in_matrix(df, "Ordenhador 2", 1, 2459.16)

    # 6. PROVISÕES
    d['Prov_Silagem'] = find_in_matrix(df, "Silagem", 1, 11340.0)
    d['Prov_Financ'] = get_financ_sum(df)
    d['Prov_Adubo'] = find_in_matrix(df, "Adubação", 1, 0.0)
    
    # 7. TOTAIS
    d['Deprec_Total'] = get_depreciacao_sum(df)

    return d

# --- LAYOUT ---
col_nav, col_content = st.columns([1, 4])

with col_nav:
    st.markdown("### ⚙️ Painel")
    selected_scenario = st.selectbox("Cenário:", scenarios)
    
    # TRIGGER DE CARGA (Executa ao mudar cenário)
    if 'last_scenario' not in st.session_state or st.session_state['last_scenario'] != selected_scenario:
        # Carrega dados novos
        data = carregar_dados_cenario(selected_scenario)
        # Atualiza Session State (Cofre)
        for key, value in data.items():
            st.session_state[f"data_{key}"] = value
        
        st.session_state['last_scenario'] = selected_scenario

    st.markdown("---")
    if st.button("📝 VARIÁVEIS", type="primary" if st.session_state['view_mode']=='variaveis' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'variaveis'
        st.rerun()
    if st.button("📊 RESULTADO", type="primary" if st.session_state['view_mode']=='resultados' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'resultados'
        st.rerun()

# --- FUNÇÃO GET/SET SEGURA ---
def get_data(key):
    return st.session_state.get(f"data_{key}", 0.0)

def input_data(label, key, step=0.01, fmt="%.2f"):
    # O input lê e escreve direto na chave 'data_X'
    return st.number_input(label, key=f"data_{key}", step=step, format=fmt)

# --- CONTEÚDO ---
with col_content:
    
    if st.session_state['view_mode'] == 'variaveis':
        st.header(f"📝 Variáveis: {selected_scenario}")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### 1. Rebanho e Produção")
            with st.container(border=True):
                cc1, cc2 = st.columns(2)
                with cc1:
                    input_data("Vacas Lactação", "Qtd_Vacas_Lac", 1.0, "%.0f")
                    input_data("Litros/Vaca", "Litros_Vaca")
                    input_data("Preço Leite", "Preco_Leite")
                with cc2:
                    input_data("Bezerras (Leite)", "Qtd_Bez_Amam", 1.0, "%.4f")
                    input_data("Leite/Bezerra/Dia", "Leite_Bez_Dia")
                    input_data("Vacas Pré-Parto", "Qtd_Pre_Parto", 1.0, "%.0f")
                    input_data("Qtd. Recria Total", "Qtd_Recria", 1.0, "%.0f")

            st.markdown("#### 3. Pessoal (Base Encargos)")
            with st.container(border=True):
                st.info("Base cálculo 21,2%")
                input_data("Salário 1 (C66)", "Sal_Ord1")
                input_data("Bonificação 1 (C67)", "Bonif_Ord1")
                input_data("Salário 2 (C68)", "Sal_Trat1")
                input_data("Bonificação 2 (C69)", "Bonif_Trat1")
                input_data("Outros (C70)", "Sal_Ord2")

            st.markdown("#### 5. Provisões (R$/mês)")
            with st.container(border=True):
                 input_data("Silagem (Reposição)", "Prov_Silagem")
                 input_data("Financiamentos", "Prov_Financ")
                 input_data("Adubação", "Prov_Adubo")

        with c2:
            st.markdown("#### 2. Custos Nutrição")
            with st.container(border=True):
                cc1, cc2 = st.columns(2)
                with cc1:
                    input_data("Preço Conc. Lac", "P_Conc_Lac")
                    input_data("Preço Conc. Pre", "P_Conc_Pre")
                    input_data("Preço Polpa", "P_Polpa")
                with cc2:
                    input_data("Consumo Lac (Kg)", "Kg_Conc_Lac", 0.1)
                    input_data("Consumo Pre (Kg)", "Kg_Conc_Pre", 0.1)
                    input_data("Consumo Polpa", "Kg_Polpa", 0.1)
                
                st.markdown("**Custos Extras**")
                input_data("Custo Recria/Sal (Fixo)", "Custo_Recria_Fixo")
                
                # Silagem Display
                st.caption("Silagem (Kg/dia)")
                c3, c4, c5 = st.columns(3)
                with c3: input_data("Lac", "Kg_Sil_Lac", 1.0, "%.0f")
                with c4: input_data("Pre", "Kg_Sil_Pre", 1.0, "%.0f")
                with c5: input_data("Seca", "Kg_Sil_Seca", 1.0, "%.0f")

            st.markdown("#### 4. Outros Custos")
            with st.container(border=True):
                input_data("GEA", "Custo_GEA")
                input_data("Lojas", "Custo_Lojas")
                input_data("Alta Genetics", "Custo_Alta")
                input_data("Outros Fixos", "Custo_Outros")

    # --- CÁLCULOS E RESULTADOS ---
    else:
        st.header(f"📊 Resultado: {selected_scenario}")

        # 1. CÁLCULOS
        
        # Produção
        vacas_lac = get_data("Qtd_Vacas_Lac")
        prod_dia = vacas_lac * get_data("Litros_Vaca")
        # Consumo Interno Leite (Bezerras)
        consumo_interno = get_data("Qtd_Bez_Amam") * get_data("Leite_Bez_Dia")
        
        prod_entregue_dia = prod_dia - consumo_interno
        # Trava de segurança para não ficar negativo
        if prod_entregue_dia < 0: prod_entregue_dia = 0
        
        prod_entregue_mes = prod_entregue_dia * 30
        prod_entregue_x2 = prod_entregue_dia * 2 
        
        # Receita
        faturamento_bruto = prod_entregue_mes * get_data("Preco_Leite")
        impostos = faturamento_bruto * 0.015
        faturamento_liquido = faturamento_bruto - impostos

        # Pessoal
        soma_base = get_data("Sal_Ord1") + get_data("Bonif_Ord1") + get_data("Sal_Trat1") + get_data("Bonif_Trat1")
        encargos = soma_base * 0.212
        custo_pessoal_desembolso = soma_base + get_data("Sal_Ord2") + encargos 

        # Desembolso Operacional
        custo_conc_lac = (vacas_lac * get_data("Kg_Conc_Lac") * 30) * get_data("P_Conc_Lac")
        custo_conc_pre = (get_data("Qtd_Pre_Parto") * get_data("Kg_Conc_Pre") * 30) * get_data("P_Conc_Pre")
        custo_recria = get_data("Custo_Recria_Fixo")
        
        custo_polpa = (vacas_lac * get_data("Kg_Polpa") * 30) * get_data("P_Polpa")
        
        total_concentrado = custo_conc_lac + custo_conc_pre + custo_recria

        desembolso_op = (total_concentrado + custo_polpa + get_data("Custo_GEA") + 
                         get_data("Custo_Lojas") + get_data("Custo_Alta") + 
                         custo_pessoal_desembolso + get_data("Custo_Outros"))

        # Fluxo de Caixa
        saldo_op = faturamento_liquido - desembolso_op
        
        prov_silagem = get_data("Prov_Silagem")
        prov_financ = get_data("Prov_Financ")
        prov_adubo = get_data("Prov_Adubo")
        
        total_prov = prov_silagem + prov_financ + prov_adubo + encargos
        lucro = saldo_op - total_prov

        # Indicadores
        deprec = get_data("Deprec_Total")
        ebitda = lucro + deprec + prov_financ
        
        custo_saidas = desembolso_op + total_prov
        custo_litro = custo_saidas / prod_entregue_mes if prod_entregue_mes > 0 else 0
        endividamento = (prov_financ / faturamento_bruto * 100) if faturamento_bruto > 0 else 0
        
        # Break Even
        custo_var = total_concentrado + custo_polpa + prov_silagem
        mcu = (faturamento_liquido / prod_entregue_mes) - (custo_var / prod_entregue_mes) if prod_entregue_mes > 0 else 0
        
        pe_coe = desembolso_op / mcu if mcu > 0 else 0
        pe_cot = (desembolso_op + deprec) / mcu if mcu > 0 else 0
        pe_ct = custo_saidas / mcu if mcu > 0 else 0

        # 2. RENDERIZAÇÃO
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
                <div class='result-row'><span>Polpa + Caroço</span><span class='result-val'>R$ {fmt(custo_polpa)}</span></div>
                <div class='result-row'><span>GEA</span><span class='result-val'>R$ {fmt(get_data("Custo_GEA"))}</span></div>
                <div class='result-row'><span>Lojas Agropec.</span><span class='result-val'>R$ {fmt(get_data("Custo_Lojas"))}</span></div>
                <div class='result-row'><span>Alta Genetics</span><span class='result-val'>R$ {fmt(get_data("Custo_Alta"))}</span></div>
                <div class='result-row'><span>Pessoal (+ Encargos)</span><span class='result-val'>R$ {fmt(custo_pessoal_desembolso)}</span></div>
                <div class='result-row'><span>Outros</span><span class='result-val'>R$ {fmt(get_data("Custo_Outros"))}</span></div>
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
                <div class='result-row'><span>Litros/Vaca</span><span class='result-val'>{get_data("Litros_Vaca"):.1f}</span></div>
                <div class='result-row'><span>Prod. Prevista</span><span class='result-val'>{fmt_int(prod_dia*30)} L</span></div>
                <div class='result-row'><span>Prod. Entregue x2</span><span class='result-val'>{fmt_int(prod_entregue_x2)} L</span></div>
                <div class='result-row' style='font-weight:bold'><span>Prod. Entregue Mês</span><span class='result-val'>{fmt_int(prod_entregue_mes)} L</span></div>
            </div>""", unsafe_allow_html=True)
            
            st.markdown("##### 5. Gasto Concentrado")
            st.markdown(f"""<div class='sub-group'>
                <div class='result-row'><span>Lactação</span><span class='result-val'>R$ {fmt(custo_conc_lac)}</span></div>
                <div class='result-row'><span>Pré-Parto</span><span class='result-val'>R$ {fmt(custo_conc_pre)}</span></div>
                <div class='result-row'><span>Recria/Sal</span><span class='result-val'>R$ {fmt(custo_recria)}</span></div>
            </div>""", unsafe_allow_html=True)
