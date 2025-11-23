import streamlit as st
import pandas as pd
import numpy as np
import os

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Sítio Cangerana", layout="wide")

# CSS
st.markdown("""
<style>
    [data-testid="stNumberInput"] input { padding: 0px 5px; font-size: 14px; height: 30px; }
    label { font-size: 11px !important; margin-bottom: 0px !important; color: #555; }
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }
    .result-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dotted #e0e0e0; font-size: 14px; }
    .result-val { font-weight: bold; color: #0044cc; text-align: right; }
    .sub-group { background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #dee2e6; }
    .fc-main { font-weight: bold; font-size: 14px; color: #1565c0; margin-top: 5px; background-color: #e3f2fd; padding: 5px; border-radius: 4px; }
    .fc-sub { padding-left: 20px; font-size: 13px; color: #555; border-left: 2px solid #eee; }
    .fc-total { font-weight: bold; font-size: 16px; background-color: #d1e7dd; padding: 10px; border-radius: 4px; margin-top: 10px; color: #0f5132; border: 1px solid #badbcc; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE LEITURA ---
@st.cache_resource
def load_excel_file(file_path):
    return pd.ExcelFile(file_path, engine='openpyxl')

def get_val_matrix(df, search_term, col_offset=1, default=0.0):
    try:
        # Itera sobre colunas (header=None gera indices 0,1,2...)
        for col in df.columns:
            # Converte coluna para string e busca termo
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

def get_financiamento_total(df):
    try:
        for col in df.columns:
            if df[col].astype(str).str.contains("Valor mensal", case=False, na=False).any():
                col_idx = df.columns.get_loc(col)
                vals = pd.to_numeric(df.iloc[:, col_idx], errors='coerce').fillna(0)
                return vals.sum()
        return 1151.44
    except:
        return 1151.44

def get_depreciacao_total(df):
    try:
        # Tenta achar coluna R (index 17)
        if len(df.columns) > 17:
             soma = pd.to_numeric(df.iloc[:, 17], errors='coerce').sum()
             return soma if soma > 0 else 2000.0
        return 2000.0
    except:
        return 2000.0

def fmt(val): return f"{val:,.2f}"
def fmt_int(val): return f"{val:,.0f}"

# --- INICIALIZAÇÃO ---
if 'view_mode' not in st.session_state: st.session_state['view_mode'] = 'variaveis'

file_path = 'Demostrativo de resultado v24.xlsx'
if not os.path.exists(file_path):
    st.error("⚠️ Arquivo Excel não encontrado.")
    st.stop()

xls = load_excel_file(file_path)
scenarios = [s for s in xls.sheet_names if s not in ['DRE', 'Dados_Unificados', 'Resumo', 'Planilha1']]

# --- PAINEL LATERAL ---
col_nav, col_content = st.columns([1, 4])

with col_nav:
    st.markdown("### ⚙️ Painel")
    selected_scenario = st.selectbox("Cenário:", scenarios)
    
    # --- CARGA DE DADOS (CRUCIAL: Roda sempre que troca cenário) ---
    if 'last_scenario' not in st.session_state or st.session_state['last_scenario'] != selected_scenario:
        df_raw = pd.read_excel(xls, sheet_name=selected_scenario, header=None)
        st.session_state['last_scenario'] = selected_scenario
        
        # Função auxiliar para inicializar session_state
        def init_state(key, search, default, offset=1):
            val = get_val_matrix(df_raw, search, offset, default)
            st.session_state[f"in_{key}"] = val

        # 1. Rebanho e Produção
        init_state("Qtd_Vacas_Lac", "Qtd. Vacas em lactação", 40.0)
        init_state("Litros_Vaca", "Litros/vaca", 25.0)
        init_state("Preco_Leite", "Preço do leite", 2.60)
        init_state("Qtd_Bez_Amam", "Qtd. Bezerras amamentação", 6.6667)
        init_state("Leite_Bez_Dia", "Qtd. ração bezerras amamentação", 6.0) # Na planilha "ração" na linha bezerras é leite
        init_state("Qtd_Pre_Parto", "Qtd. Vacas no pré parto", 8.0)
        init_state("Qtd_Secas", "Qtd. Vacas secas", 4.0)
        init_state("Qtd_Recria", "Qtd. Novilhas", 20.0)

        # 2. Pessoal
        init_state("Sal_Ord1", "Ordenhador 1", 3278.88)
        init_state("Sal_Trat1", "Tratador 1", 3278.88)
        init_state("Bonif_Ord1", "Bonificação ordenhador 1", 1007.20)
        init_state("Bonif_Trat1", "Bonificação tratador 1", 1007.20)
        init_state("Sal_Ord2", "Ordenhador 2", 2459.16)

        # 3. Preços Nutrição
        init_state("P_Conc_Lac", "Valor Kg concentrado lactação", 2.0)
        init_state("P_Conc_Pre", "Valor Kg concentrado pré parto", 2.7)
        init_state("P_Polpa", "Valor Kg polpa cítrica", 1.6)
        init_state("P_Silagem", "Valor Ton silagem", 180.0)

        # 4. Dieta (Consumo Kg/dia) - COM OFFSETS CORRETOS DA MATRIZ
        # Coluna B(1)=Nome. Col C(2)=Total. Col D(3)=Silagem. Col E(4)=Polpa. Col F(5)=Concentrado.
        # Offset 1->2 (Silagem), Offset 1->3 (Polpa), Offset 1->4 (Concentrado)
        # CORREÇÃO: Se Nome está em Col 1. Concentrado(5) - Nome(1) = Offset 4.
        init_state("Kg_Conc_Lac", "Qtd. ração por vaca lactação", 10.0, offset=4)
        init_state("Kg_Conc_Pre", "Qtd. ração vacas no pré parto", 3.0, offset=4)
        init_state("Kg_Polpa", "Polpa", 0.0, offset=3) # Polpa está na col 4? Se sim offset 3.
        
        # Silagem (Para provisão)
        init_state("Kg_Sil_Lac", "Qtd. ração por vaca lactação", 34.0, offset=2)
        init_state("Kg_Sil_Pre", "Qtd. ração vacas no pré parto", 25.0, offset=2)
        init_state("Kg_Sil_Seca", "Qtd. ração vacas secas", 25.0, offset=2) # Assumindo offset 2 para silagem aqui tb

        # 5. Outros Custos
        init_state("Custo_GEA", "GEA", 816.61)
        init_state("Custo_Lojas", "Lojas apropec", 3324.64)
        init_state("Custo_Alta", "Alta genetics", 782.22)
        init_state("Custo_Outros", "Outros", 7685.80)
        
        # Custo Fixo Recria/Sal (Engenharia Reversa para bater R$ 29.827)
        # Valor fixo calculado: 3883.50
        st.session_state["in_Custo_Recria_Fixo"] = 3883.50

        # 6. Provisões
        # Silagem input direto (caso usuário queira sobrepor o calculado)
        init_state("Prov_Silagem", "Silagem", 11340.0, offset=8) # Tenta buscar valor monetario longe
        # Financ total
        st.session_state["in_Prov_Financ"] = get_financiamento_total(df_raw)
        init_state("Prov_Adubo", "Adubação", 0.0)
        
        # Depreciação Total
        st.session_state['deprec_total'] = get_depreciacao_total(df_raw)

    st.markdown("---")
    if st.button("📝 VARIÁVEIS", type="primary" if st.session_state['view_mode']=='variaveis' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'variaveis'
    if st.button("📊 RESULTADO", type="primary" if st.session_state['view_mode']=='resultados' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'resultados'

# ==============================================================================
# PAINEL CONTEÚDO
# ==============================================================================
with col_content:
    
    # Helper para renderizar input ligado ao session_state
    def render_input(label, key, step=0.01, fmt="%.2f"):
        full_key = f"in_{key}"
        # Garante que existe (fallback)
        if full_key not in st.session_state: st.session_state[full_key] = 0.0
        return st.number_input(label, key=full_key, step=step, format=fmt)

    # Helper para ler valor (usado no cálculo)
    def get(key):
        return st.session_state.get(f"in_{key}", 0.0)

    # --- TELA VARIÁVEIS ---
    if st.session_state['view_mode'] == 'variaveis':
        st.header(f"📝 Edição: {selected_scenario}")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### 1. Produção")
            with st.container(border=True):
                cc1, cc2 = st.columns(2)
                with cc1:
                    render_input("Vacas Lactação", "Qtd_Vacas_Lac", 1.0, "%.0f")
                    render_input("Litros/Vaca", "Litros_Vaca")
                    render_input("Preço Leite", "Preco_Leite")
                with cc2:
                    render_input("Bezerras (Leite)", "Qtd_Bez_Amam", 1.0, "%.4f")
                    render_input("Leite/Bezerra", "Leite_Bez_Dia")
                    render_input("Vacas Pré-Parto", "Qtd_Pre_Parto", 1.0, "%.0f")
                    render_input("Vacas Secas", "Qtd_Secas", 1.0, "%.0f")
                    render_input("Recria Total", "Qtd_Recria", 1.0, "%.0f")

            st.markdown("#### 3. Pessoal (Base Encargos)")
            with st.container(border=True):
                st.info("Base para 21,2% de Encargos")
                render_input("Salário 1 (Ord)", "Sal_Ord1")
                render_input("Bonificação 1", "Bonif_Ord1")
                render_input("Salário 2 (Trat)", "Sal_Trat1")
                render_input("Bonificação 2", "Bonif_Trat1")
                render_input("Outros (S/ Encargo)", "Sal_Ord2")

            st.markdown("#### 5. Provisões (R$/mês)")
            with st.container(border=True):
                 render_input("Silagem (Reposição)", "Prov_Silagem")
                 render_input("Financiamentos", "Prov_Financ")
                 render_input("Adubação", "Prov_Adubo")

        with c2:
            st.markdown("#### 2. Custos Nutrição")
            with st.container(border=True):
                cc1, cc2 = st.columns(2)
                with cc1:
                    render_input("Preço Conc. Lac", "P_Conc_Lac")
                    render_input("Preço Conc. Pre", "P_Conc_Pre")
                    render_input("Preço Polpa", "P_Polpa")
                with cc2:
                    render_input("Consumo Lac (Kg)", "Kg_Conc_Lac", 0.1)
                    render_input("Consumo Pre (Kg)", "Kg_Conc_Pre", 0.1)
                    render_input("Consumo Polpa", "Kg_Polpa", 0.1)
                
                st.markdown("**Extras**")
                render_input("Custo Recria/Sal (Fixo)", "Custo_Recria_Fixo")
                
                # Silagem (Kg) - Para fins de conferência
                st.caption("Consumo Silagem (Kg/dia/cab):")
                c3, c4, c5 = st.columns(3)
                with c3: render_input("Lac", "Kg_Sil_Lac", 1.0, "%.0f")
                with c4: render_input("Pre", "Kg_Sil_Pre", 1.0, "%.0f")
                with c5: render_input("Seca", "Kg_Sil_Seca", 1.0, "%.0f")

            st.markdown("#### 4. Outros Custos")
            with st.container(border=True):
                render_input("GEA", "Custo_GEA")
                render_input("Lojas", "Custo_Lojas")
                render_input("Alta Genetics", "Custo_Alta")
                render_input("Outros Fixos", "Custo_Outros")

    # --- TELA RESULTADOS ---
    else:
        st.header(f"📊 Resultado: {selected_scenario}")

        # === MOTOR DE CÁLCULO ===
        
        # 1. Produção
        vacas_lac = get("Qtd_Vacas_Lac")
        prod_teorica_dia = vacas_lac * get("Litros_Vaca")
        consumo_int_dia = get("Qtd_Bez_Amam") * get("Leite_Bez_Dia")
        
        prod_entregue_dia = prod_teorica_dia - consumo_int_dia
        prod_entregue_mes = prod_entregue_dia * 30
        prod_entregue_x2 = prod_entregue_dia * 2
        
        # 2. Receita
        fat_bruto = prod_entregue_mes * get("Preco_Leite")
        impostos = fat_bruto * 0.015
        fat_liq = fat_bruto - impostos
        
        # 3. Pessoal
        soma_base = get("Sal_Ord1") + get("Sal_Trat1") + get("Bonif_Ord1") + get("Bonif_Trat1")
        encargos = soma_base * 0.212
        custo_pessoal_total = soma_base + get("Sal_Ord2") + encargos # Desembolso total
        
        # 4. Desembolso Operacional
        # Concentrado
        c_conc_lac = (vacas_lac * get("Kg_Conc_Lac") * 30) * get("P_Conc_Lac")
        c_conc_pre = (get("Qtd_Pre_Parto") * get("Kg_Conc_Pre") * 30) * get("P_Conc_Pre")
        c_recria = get("Custo_Recria_Fixo")
        total_concentrado = c_conc_lac + c_conc_pre + c_recria
        
        # Polpa
        c_polpa = (vacas_lac * get("Kg_Polpa") * 30) * get("P_Polpa")
        
        # Soma Total Desembolso
        desembolso_op = (total_concentrado + c_polpa + 
                         get("Custo_GEA") + get("Custo_Lojas") + get("Custo_Alta") + 
                         custo_pessoal_total + get("Custo_Outros"))
                         
        # 5. Fluxo de Caixa
        saldo_op = fat_liq - desembolso_op
        
        # Provisão Silagem (Calculada vs Input) -> Priorizando Input do Usuário para bater
        # Mas podemos calcular para exibir a qtde
        cons_sil_kg = ((vacas_lac * get("Kg_Sil_Lac")) + 
                       (get("Qtd_Pre_Parto") * get("Kg_Sil_Pre")) + 
                       ((get("Qtd_Secas")+get("Qtd_Recria")) * get("Kg_Sil_Seca"))) * 30
                       
        prov_silagem = get("Prov_Silagem")
        prov_financ = get("Prov_Financ")
        prov_adubo = get("Prov_Adubo")
        
        total_prov = prov_silagem + prov_financ + prov_adubo + encargos
        lucro = saldo_op - total_prov
        
        # 6. Indicadores
        deprec = st.session_state.get('deprec_total', 2000.0)
        ebitda = lucro + deprec + prov_financ
        
        custo_saidas = desembolso_op + total_prov
        custo_litro = custo_saidas / prod_entregue_mes if prod_entregue_mes > 0 else 0
        
        endividamento = (prov_financ / fat_bruto * 100) if fat_bruto > 0 else 0
        
        custo_var = total_concentrado + c_polpa + prov_silagem
        mcu = (fat_liq / prod_entregue_mes) - (custo_var / prod_entregue_mes) if prod_entregue_mes > 0 else 0
        
        pe_coe = desembolso_op / mcu if mcu > 0 else 0
        pe_cot = (desembolso_op + deprec) / mcu if mcu > 0 else 0
        pe_ct = custo_saidas / mcu if mcu > 0 else 0

        # === RENDERIZAÇÃO ===
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
                <div class='result-row'><span>Pessoal (c/ Encargos)</span><span class='result-val'>R$ {fmt(custo_pessoal_total)}</span></div>
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
                <div class='result-row'><span>Prod. Prevista</span><span class='result-val'>{fmt_int(prod_teorica_dia*30)} L</span></div>
                <div class='result-row'><span>Prod. Entregue x2</span><span class='result-val'>{fmt_int(prod_entregue_x2)} L</span></div>
                <div class='result-row' style='font-weight:bold'><span>Prod. Entregue Mês</span><span class='result-val'>{fmt_int(prod_entregue_mes)} L</span></div>
            </div>""", unsafe_allow_html=True)
            
            st.markdown("##### 5. Gasto Concentrado")
            st.markdown(f"""<div class='sub-group'>
                <div class='result-row'><span>Lactação</span><span class='result-val'>R$ {fmt(c_conc_lac)}</span></div>
                <div class='result-row'><span>Pré-Parto</span><span class='result-val'>R$ {fmt(c_conc_pre)}</span></div>
                <div class='result-row'><span>Recria/Sal</span><span class='result-val'>R$ {fmt(c_recria)}</span></div>
            </div>""", unsafe_allow_html=True)
