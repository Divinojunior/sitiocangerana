import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sítio Cangerana", layout="wide")

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

# --- FUNÇÕES AUXILIARES ---
def fmt(val):
    try:
        if pd.isna(val) or val is None: return "0,00"
        return f"{float(val):,.2f}"
    except:
        return "0,00"

def fmt_int(val):
    try:
        if pd.isna(val) or val is None: return "0"
        return f"{float(val):,.0f}"
    except:
        return "0"

# --- INICIALIZAÇÃO DE DADOS (DADOS IMPORTADOS DO APP WEB) ---
if 'initialized' not in st.session_state:
    defaults = {
        "Qtd_Vacas_Lac": 40,
        "Litros_Vaca": 25,
        "Preco_Leite": 2.6,
        "Qtd_Bez_Amam": 6.6667,
        "Leite_Bez_Dia": 6,
        "Qtd_Pre_Parto": 8,
        "Qtd_Secas": 4,
        "Qtd_Recria": 20,
        
        "Sal_Ord1": 3278.88,
        "Sal_Trat1": 3278.88,
        "Bonif_Ord1": 1007.2,
        "Bonif_Trat1": 1007.2,
        "Sal_Ord2": 2459.16,
        
        "P_Conc_Lac": 2,
        "P_Conc_Pre": 2.7,
        "P_Polpa": 1.6,
        "P_Silagem": 180,
        
        "Kg_Conc_Lac": 10,
        "Kg_Conc_Pre": 3,
        "Kg_Polpa": 0,
        "Kg_Sil_Lac": 34,
        "Kg_Sil_Pre": 25,
        "Kg_Sil_Seca": 25,
        
        "Custo_GEA": 816.61,
        "Custo_Lojas": 3324.64,
        "Custo_Alta": 782.22,
        "Custo_Outros": 7685.8,
        "Custo_Recria_Fixo": 3883.5,
        
        "Prov_Silagem": 11340,
        "Prov_Financ": 1151.44,
        "Prov_Adubo": 0,
        "Deprec_Total": 2000
    }
    
    for key, val in defaults.items():
        st.session_state[f"in_{key}"] = val
    
    st.session_state['initialized'] = True

if 'view_mode' not in st.session_state: st.session_state['view_mode'] = 'resultados'

# --- LAYOUT PRINCIPAL ---
col_nav, col_content = st.columns([1, 4])

# --- FUNÇÕES UI ---
def smart_input(label, key, step=0.01, fmt="%.2f"):
    full_key = f"in_{key}"
    if full_key not in st.session_state: st.session_state[full_key] = 0.0
    return st.number_input(label, key=full_key, step=step, format=fmt)

def get(key):
    return float(st.session_state.get(f"in_{key}", 0.0))

# --- SIDEBAR ---
with col_nav:
    st.markdown("### ⚙️ Painel")
    st.info("Versão Web Gerada")
    st.markdown("---")
    if st.button("📝 VARIÁVEIS", type="primary" if st.session_state['view_mode']=='variaveis' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'variaveis'
        st.rerun()
    if st.button("📊 RESULTADO", type="primary" if st.session_state['view_mode']=='resultados' else "secondary", use_container_width=True):
        st.session_state['view_mode'] = 'resultados'
        st.rerun()

# --- CONTEÚDO ---
with col_content:
    if st.session_state['view_mode'] == 'variaveis':
        st.header(f"📝 Edição de Variáveis")
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
                 smart_input("Depreciação", "Deprec_Total")

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

    else:
        st.header(f"📊 Demonstrativo de Resultados")

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
        prov_financ = get("Prov_Financ")
        prov_adubo = get("Prov_Adubo")
        
        total_prov = prov_silagem + prov_financ + prov_adubo + encargos
        lucro = saldo_op - total_prov

        # 6. INDICADORES
        deprec = get("Deprec_Total")
        ebitda = lucro + deprec + prov_financ
        
        custo_saidas = desembolso_op + total_prov
        
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
