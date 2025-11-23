import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sítio Cangerana", layout="wide")

# CSS para botões e layout
st.markdown("""
<style>
    [data-testid="stNumberInput"] input { padding: 0px 5px; font-size: 14px; height: 30px; }
    label { font-size: 12px !important; margin-bottom: 0px !important; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .nav-btn { width: 100%; margin-bottom: 10px; }
    div.stButton > button { width: 100%; border-radius: 5px; height: 50px; font-weight: bold; }
    .result-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #eee; font-size: 14px; }
    .result-val { font-weight: bold; color: #0044cc; }
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

# --- INICIALIZAÇÃO DE ESTADO ---
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = 'variaveis' # Começa vendo variáveis

if 'inputs' not in st.session_state:
    st.session_state['inputs'] = {}

# --- CARREGAMENTO ---
file_path = 'Demostrativo de resultado v24.xlsx'
if not os.path.exists(file_path):
    st.error("Arquivo Excel não encontrado.")
    st.stop()

xls = load_data(file_path)
scenarios = [s for s in xls.sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]

# --- LAYOUT GERAL: MENU ESQUERDO (NAV) x CONTEÚDO DIREITO ---
col_nav, col_content = st.columns([1, 4])

# ==============================================================================
# COLUNA DA ESQUERDA: NAVEGAÇÃO
# ==============================================================================
with col_nav:
    st.markdown("### 🕹️ Controle")
    
    # 1. Seletor de Cenário
    selected_scenario = st.selectbox("Cenário Base:", scenarios)
    
    # Carregar dados do cenário (apenas se mudou ou se é a primeira vez)
    # Usamos session_state para controlar se precisamos recarregar os valores padrão
    if 'last_scenario' not in st.session_state or st.session_state['last_scenario'] != selected_scenario:
        df_raw = pd.read_excel(xls, sheet_name=selected_scenario)
        st.session_state['last_scenario'] = selected_scenario
        st.session_state['df_raw'] = df_raw # Salva o dataframe bruto
        # Força recarregar inputs padrão na próxima renderização
        st.session_state['reload_defaults'] = True 
    else:
        df_raw = st.session_state['df_raw']
        st.session_state['reload_defaults'] = False

    st.markdown("---")
    
    # 2. Botões de Navegação
    # Usamos callbacks para mudar a tela
    def set_view_vars(): st.session_state['view_mode'] = 'variaveis'
    def set_view_res(): st.session_state['view_mode'] = 'resultados'

    # Botão Variáveis (Destaca se estiver ativo)
    type_var = "primary" if st.session_state['view_mode'] == 'variaveis' else "secondary"
    st.button("📝 VARIÁVEIS", on_click=set_view_vars, type=type_var, use_container_width=True)
    
    # Botão Resultados
    type_res = "primary" if st.session_state['view_mode'] == 'resultados' else "secondary"
    st.button("📊 RESULTADO", on_click=set_view_res, type=type_res, use_container_width=True)

    st.info("👆 Use os botões acima para alternar entre edição e análise.")

# ==============================================================================
# COLUNA DA DIREITA: CONTEÚDO DINÂMICO
# ==============================================================================
with col_content:
    
    # Dicionário auxiliar para inputs (lê/escreve no session_state para persistência)
    # Se 'reload_defaults' for True, pegamos do Excel. Se False, mantemos o que está na memória (o que o usuário digitou).
    def smart_input(label, key_search, default_val, step=0.01, fmt="%.2f"):
        # Chave única para o widget
        k = f"in_{key_search}"
        
        # Se mudou de cenário, reseta para o valor do Excel
        if st.session_state.get('reload_defaults', False):
            val_excel = get_val(df_raw, key_search, default_val)
            st.session_state[k] = val_excel
        
        # Se a chave ainda não existe, cria
        if k not in st.session_state:
            val_excel = get_val(df_raw, key_search, default_val)
            st.session_state[k] = val_excel

        # Se estamos na tela de VARIÁVEIS, mostramos o input
        if st.session_state['view_mode'] == 'variaveis':
            return st.number_input(label, value=st.session_state[k], step=step, format=fmt, key=k)
        else:
            # Se estamos na tela de RESULTADOS, apenas retornamos o valor da memória (sem mostrar input)
            return st.session_state[k]

    # --- TELA 1: VARIÁVEIS (INPUTS) ---
    if st.session_state['view_mode'] == 'variaveis':
        st.header(f"📝 Edição de Variáveis: {selected_scenario}")
        
        # Grupo 1
        with st.container(border=True):
            st.subheader("1. Dados Principais")
            c1, c2, c3, c4 = st.columns(4)
            with c1: smart_input("Litros/vaca", "Litros/vaca", 20.0, 0.5)
            with c2: smart_input("Preço do leite", "Preço do leite", 2.50)
            with c3: smart_input("Qtd. Vacas total", "Qtd. Vacas total", 60.0, 1.0, "%.0f")
            with c4: smart_input("Vacas em lactação", "Qtd. Vacas em lactação", 40.0, 1.0, "%.0f")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: smart_input("Vacas pré-parto", "Qtd. Vacas no pré parto", 5.0, 1.0, "%.0f")
            with c2: smart_input("Vacas secas", "Qtd. Vacas secas", 10.0, 1.0, "%.0f")
            with c3: smart_input("Novilhas", "Qtd. Novilhas", 15.0, 1.0, "%.0f")
            with c4: smart_input("Bezerras", "Qtd. Bezerras", 10.0, 1.0, "%.0f")

        # Grupo 2
        with st.container(border=True):
            st.subheader("2. Dados Adicionais (Nutrição)")
            c1, c2, c3, c4 = st.columns(4)
            with c1: smart_input("R$ Kg Conc. Lactação", "Valor Kg concentrado lactação", 2.0)
            with c2: smart_input("R$ Kg Conc. Pré", "Valor Kg concentrado pré parto", 2.5)
            with c3: smart_input("R$ Kg Raç. Bezerra", "Valor Kg ração bezerra", 3.0)
            with c4: smart_input("R$ Kg Raç. Novilha", "Valor Kg ração novilha", 2.2)
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: smart_input("R$ Kg Polpa", "Valor Kg polpa cítrica", 1.5)
            with c2: smart_input("R$ Kg Caroço", "Valor Kg caroço algodão", 1.8)
            with c3: smart_input("R$ Kg Silagem", "Valor Kg silagem", 0.2)
            with c4: smart_input("Relação Leite:Conc", "Relação leite x concentrado", 3.0)

        # Grupo 3
        with st.container(border=True):
            st.subheader("3. Limpeza e Sanidade")
            c1, c2, c3 = st.columns(3)
            with c1: smart_input("Iodo (Dipping)", "Iodo para dipping", 13.96)
            with c2: smart_input("Papel Toalha", "Papel toalha", 19.50)
            with c3: smart_input("Luvas Látex", "Luvas de látex", 33.00)
            
            c1, c2, c3 = st.columns(3)
            with c1: smart_input("Det. Alcalino", "Detergente alcalino", 100.0)
            with c2: smart_input("Det. Ácido", "Detergente ácido", 80.0)
            with c3: smart_input("Desinfetante", "Desinfetante", 50.0)

        # Grupo 4
        with st.container(border=True):
            st.subheader("4. Financeiro")
            c1, c2, c3 = st.columns(3)
            with c1: smart_input("Salário Mínimo", "Salário mínimo", 1412.0)
            with c2: smart_input("Valor Benfeitorias", "Valor das benfeitorias", 100000.0)
            with c3: 
                v_trator = get_val(df_raw, "Trator", 50000.0)
                v_vagao = get_val(df_raw, "Vagão", 20000.0)
                # Input especial combinado
                st.session_state['in_Maquinario'] = st.number_input("Valor Maquinário", value=st.session_state.get('in_Maquinario', v_trator + v_vagao))
            
            c1, c2 = st.columns(2)
            with c1: 
                v_mensal = get_val(df_raw, "Valor mensal", 0.0)
                v_financ = get_val(df_raw, "Financiamento", 0.0)
                st.session_state['in_Financ_Mensal'] = st.number_input("Financ. (Mensal)", value=st.session_state.get('in_Financ_Mensal', v_mensal + v_financ))
            with c2: 
                st.session_state['in_Outros_Fixos'] = st.number_input("Outros Custos Fixos", value=st.session_state.get('in_Outros_Fixos', 2000.0))

    # --- TELA 2: RESULTADOS (CÁLCULOS + VISUALIZAÇÃO) ---
    else:
        st.header(f"📊 Resultados Simulados: {selected_scenario}")
        
        # --- MOTOR DE CÁLCULO (Recuperando do session_state mesmo que inputs estejam ocultos) ---
        # Função helper para ler do estado
        def get_in(key): return st.session_state.get(f"in_{key}", 0.0)
        
        # 1. Produção
        prod_dia = get_in("Litros/vaca") * get_in("Qtd. Vacas em lactação")
        prod_mes = prod_dia * 30
        receita_bruta = prod_mes * get_in("Preço do leite")

        # 2. Concentrados
        relacao = get_in("Relação leite x concentrado")
        kg_conc_lac_dia = prod_dia / relacao if relacao > 0 else 0
        gasto_conc_lac = kg_conc_lac_dia * 30 * get_in("Valor Kg concentrado lactação")
        
        gasto_conc_pre = get_in("Qtd. Vacas no pré parto") * 3 * 30 * get_in("Valor Kg concentrado pré parto")
        gasto_conc_nov = get_in("Qtd. Novilhas") * 2 * 30 * get_in("Valor Kg ração novilha")
        gasto_conc_bez = get_in("Qtd. Bezerras") * 1 * 30 * get_in("Valor Kg ração bezerra")
        
        total_concentrado = gasto_conc_lac + gasto_conc_pre + gasto_conc_nov + gasto_conc_bez

        # 3. Outros (Polpa/Caroço)
        gasto_polpa_caroco = (prod_dia * 0.5 * 30 * get_in("Valor Kg polpa cítrica")) 

        # 4. Operacional
        custo_pessoal = get_in("Salário mínimo") * 3.5
        custo_gea = get_val(df_raw, "GEA", 500.0)
        custo_lojas = get_val(df_raw, "Lojas apropec", 1000.0)
        custo_alta = get_val(df_raw, "Alta genetics", 300.0)
        custo_outros = st.session_state.get('in_Outros_Fixos', 2000.0)

        desembolso_operacional = total_concentrado + gasto_polpa_caroco + custo_gea + custo_lojas + custo_alta + custo_pessoal + custo_outros

        # 5. Provisões
        prov_silagem = get_in("Qtd. Vacas total") * 30 * 30 * get_in("Valor Kg silagem")
        prov_financ = st.session_state.get('in_Financ_Mensal', 0.0)
        prov_adubo = get_val(df_raw, "Adubação", 1000.0)

        total_saidas_caixa = desembolso_operacional + prov_silagem + prov_financ + prov_adubo
        lucro_liquido = receita_bruta - total_saidas_caixa

        # 6. Indicadores
        depreciacao = (get_in("Valor das benfeitorias") + st.session_state.get('in_Maquinario', 70000)) * 0.04 / 12
        ebitda = lucro_liquido + depreciacao + prov_financ 
        custo_por_litro = total_saidas_caixa / prod_mes if prod_mes > 0 else 0
        
        custo_var_unit = (total_concentrado + gasto_polpa_caroco) / prod_mes if prod_mes > 0 else 0
        margem_unit = get_in("Preço do leite") - custo_var_unit
        
        pe_coe = desembolso_operacional / margem_unit if margem_unit > 0 else 0
        pe_cot = (desembolso_operacional + depreciacao) / margem_unit if margem_unit > 0 else 0
        pe_ct = (total_saidas_caixa + depreciacao) / margem_unit if margem_unit > 0 else 0

        # --- EXIBIÇÃO DOS RESULTADOS (5 GRUPOS) ---
        
        col_res1, col_res2 = st.columns(2)
        
        with col_res1:
            # GRUPO 1: INDICADORES FINANCEIROS
            with st.container(border=True):
                st.subheader("1. Indicadores Financeiros")
                st.markdown(f"""
                <div class='result-row'><span>EBITDA</span><span class='result-val'>R$ {fmt(ebitda)}</span></div>
                <div class='result-row'><span>Custo por Litro</span><span class='result-val'>R$ {fmt(custo_por_litro)}</span></div>
                <div class='result-row'><span>Endividamento</span><span class='result-val'>{prov_financ/receita_bruta*100:.1f}%</span></div>
                <div class='result-row'><span>P.E. (C.O.E)</span><span class='result-val'>{fmt_int(pe_coe)} L</span></div>
                <div class='result-row'><span>P.E. (C.T.)</span><span class='result-val'>{fmt_int(pe_ct)} L</span></div>
                """, unsafe_allow_html=True)

            # GRUPO 2: DESEMBOLSO MENSAL
            with st.container(border=True):
                st.subheader("2. Desembolso Mensal")
                st.markdown(f"""
                <div class='result-row'><span>Concentrado Total</span><span class='result-val'>R$ {fmt(total_concentrado)}</span></div>
                <div class='result-row'><span>Polpa + Caroço</span><span class='result-val'>R$ {fmt(gasto_polpa_caroco)}</span></div>
                <div class='result-row'><span>Manutenção (GEA)</span><span class='result-val'>R$ {fmt(custo_gea)}</span></div>
                <div class='result-row'><span>Lojas / Insumos</span><span class='result-val'>R$ {fmt(custo_lojas)}</span></div>
                <div class='result-row'><span>Genética (Alta)</span><span class='result-val'>R$ {fmt(custo_alta)}</span></div>
                <div class='result-row'><span>Mão de Obra</span><span class='result-val'>R$ {fmt(custo_pessoal)}</span></div>
                <div class='result-row' style='background-color: #f0f8ff; font-weight: bold;'><span>TOTAL</span><span>R$ {fmt(desembolso_operacional)}</span></div>
                """, unsafe_allow_html=True)

        with col_res2:
            # GRUPO 3: FLUXO DE CAIXA
            with st.container(border=True):
                st.subheader("3. Fluxo de Caixa")
                st.markdown(f"""
                <div class='result-row'><span>(+) Receita Bruta</span><span class='result-val' style='color:green'>R$ {fmt(receita_bruta)}</span></div>
                <div class='result-row'><span>(-) Prov. Silagem</span><span class='result-val' style='color:red'>R$ {fmt(prov_silagem)}</span></div>
                <div class='result-row'><span>(-) Prov. Bancos</span><span class='result-val' style='color:red'>R$ {fmt(prov_financ)}</span></div>
                <div class='result-row'><span>(-) Prov. Adubo</span><span class='result-val' style='color:red'>R$ {fmt(prov_adubo)}</span></div>
                <div class='result-row'><span>(-) Desembolso Op.</span><span class='result-val' style='color:red'>R$ {fmt(desembolso_operacional)}</span></div>
                <div class='result-row' style='font-size:16px; margin-top:5px; border-top: 2px solid #ddd;'><span>(=) LUCRO LÍQUIDO</span><span class='result-val'>{fmt(lucro_liquido)}</span></div>
                """, unsafe_allow_html=True)

            # GRUPO 4: PRODUÇÃO
            with st.container(border=True):
                st.subheader("4. Indicadores Produção")
                st.markdown(f"""
                <div class='result-row'><span>Vacas Lactação</span><span class='result-val'>{fmt_int(get_in("Qtd. Vacas em lactação"))}</span></div>
                <div class='result-row'><span>Litros/Vaca/Dia</span><span class='result-val'>{get_in("Litros/vaca"):.1f}</span></div>
                <div class='result-row'><span>Prod. Prevista</span><span class='result-val'>{fmt_int(prod_mes)} L</span></div>
                <div class='result-row'><span>Prod. Entregue (Mês)</span><span class='result-val'>{fmt_int(prod_mes * 0.98)} L</span></div>
                """, unsafe_allow_html=True)
            
            # GRUPO 5: CONCENTRADO DETALHE
            with st.container(border=True):
                st.subheader("5. Gasto Concentrado")
                st.markdown(f"""
                <div class='result-row'><span>Lactação</span><span class='result-val'>R$ {fmt(gasto_conc_lac)}</span></div>
                <div class='result-row'><span>Pré-Parto</span><span class='result-val'>R$ {fmt(gasto_conc_pre)}</span></div>
                <div class='result-row'><span>Recria (Nov/Bez)</span><span class='result-val'>R$ {fmt(gasto_conc_nov + gasto_conc_bez)}</span></div>
                """, unsafe_allow_html=True)
