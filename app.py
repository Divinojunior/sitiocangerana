import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# Configuração da Página
st.set_page_config(page_title="Sítio Cangerana - Simulador", layout="wide")

# --- FUNÇÃO PARA CARREGAR DADOS ---
@st.cache_data
def load_data(file_path):
    # Lê todas as abas do Excel
    # Importante: O engine='openpyxl' é necessário para arquivos .xlsx
    xls = pd.ExcelFile(file_path, engine='openpyxl')
    return xls

# --- TÍTULO E CABEÇALHO ---
st.title("🌱 Sítio Cangerana: Simulador de Cenários")
st.markdown("---")

# --- BARRA LATERAL (CONFIGURAÇÕES) ---
st.sidebar.header("1. Escolha o Cenário Base")

# Tentar carregar o arquivo. Se não achar, avisa o usuário.
try:
    file_path = 'Demostrativo de resultado v24.xlsx'
    xls = load_data(file_path)
    all_sheet_names = xls.sheet_names
    
    # Remove a aba DRE da lista de cenários de input (se existir)
    scenarios = [s for s in all_sheet_names if s != 'DRE' and s != 'Dados_Unificados']
    
    selected_scenario = st.sidebar.selectbox("Carregar dados de:", scenarios)

    # Carrega os dados da aba selecionada
    df_raw = pd.read_excel(xls, sheet_name=selected_scenario)
    
    # --- PROCESSAMENTO DOS DADOS (Limpeza rápida para encontrar as variáveis) ---
    # Como a planilha tem formato livre, vamos buscar valores baseados na coluna "Descrição"
    # Transformamos em um dicionário para facilitar a busca: {'Litros/vaca': 25, ...}
    
    # Função auxiliar para buscar valor seguro
    def get_val(df, key_col, val_col, search_term, default=0.0):
        try:
            # Procura na coluna de descrição (key_col) o termo
            row = df[df[key_col].astype(str).str.contains(search_term, case=False, na=False)]
            if not row.empty:
                return float(row[val_col].values[0])
            return default
        except:
            return default

    # Identificando as colunas (baseado no CSV que você enviou, col 0 é descrição, col 1 é valor)
    # Ajuste os índices [0] e [1] se suas colunas mudarem de lugar
    data_dict = dict(zip(df_raw.iloc[:, 0], df_raw.iloc[:, 1]))

    st.sidebar.header("2. Ajuste as Variáveis (Simulação)")
    
    # INPUTS PRINCIPAIS - PRODUÇÃO
    st.sidebar.subheader("🐄 Produção")
    
    # Buscando valores iniciais da planilha (com valores padrão caso falhe)
    litros_vaca_init = get_val(df_raw, df_raw.columns[0], df_raw.columns[1], "Litros/vaca", 20.0)
    qtd_vacas_lac_init = get_val(df_raw, df_raw.columns[0], df_raw.columns[1], "Qtd. Vacas em lactação", 40.0)
    
    litros_vaca = st.sidebar.number_input("Litros/Vaca/Dia", value=litros_vaca_init, step=0.5)
    qtd_vacas_lactacao = st.sidebar.number_input("Vacas em Lactação", value=qtd_vacas_lac_init, step=1.0)
    
    # INPUTS PRINCIPAIS - MERCADO
    st.sidebar.subheader("💰 Mercado")
    preco_leite_init = get_val(df_raw, df_raw.columns[0], df_raw.columns[1], "Preço do leite", 2.50)
    preco_leite = st.sidebar.number_input("Preço do Leite (R$)", value=preco_leite_init, step=0.05)

    # INPUTS PRINCIPAIS - CUSTOS
    st.sidebar.subheader("📉 Custos Variáveis")
    custo_conc_init = get_val(df_raw, df_raw.columns[6], df_raw.columns[7], "Valor Kg concentrado lactação", 2.0) # Colunas H e I aprox
    custo_concentrado = st.sidebar.number_input("R$ Kg Concentrado", value=custo_conc_init, format="%.2f")
    
    # --- CÁLCULOS DO DRE (Lógica Reconstruída) ---
    # Aqui replicamos a lógica matemática para ser rápido
    
    # 1. Receitas
    producao_dia = litros_vaca * qtd_vacas_lactacao
    producao_mensal = producao_dia * 30
    receita_bruta = producao_mensal * preco_leite
    
    # 2. Custos (Simplificação para demonstração - você pode adicionar mais inputs)
    # Estimativa: Vacas comem X kg de concentrado baseado na produção (ex: 1kg pra cada 3L)
    consumo_conc_dia = (producao_dia / 3) * custo_concentrado # Exemplo de lógica
    custo_alimentacao_mensal = consumo_conc_dia * 30 
    
    # Outros custos fixos estimados da planilha (puxando um valor fixo ou % para simplificar o exemplo)
    custos_fixos_estimados = 15000.00 # Valor base, idealmente puxaria da planilha também
    
    custo_total = custo_alimentacao_mensal + custos_fixos_estimados
    lucro_operacional = receita_bruta - custo_total
    ebitda = lucro_operacional + 1000 # Adicionando depreciação ficticia de volta
    
    margem_lucro = (lucro_operacional / receita_bruta) * 100 if receita_bruta > 0 else 0

    # --- DASHBOARD PRINCIPAL ---
    
    # Linha de KPIs (Indicadores)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Produção Diária (L)", f"{producao_dia:,.0f}")
    col2.metric("Receita Bruta Mensal", f"R$ {receita_bruta:,.2f}")
    col3.metric("Custo Total Estimado", f"R$ {custo_total:,.2f}")
    col4.metric("Lucro Operacional", f"R$ {lucro_operacional:,.2f}", delta=f"{margem_lucro:.1f}%")

    # Gráficos
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("DRE Visual")
        fig = go.Figure(go.Waterfall(
            name = "20", orientation = "v",
            measure = ["relative", "relative", "total"],
            x = ["Receita Bruta", "Custos Totais", "Lucro"],
            textposition = "outside",
            text = [f"{receita_bruta/1000:.1f}k", f"-{custo_total/1000:.1f}k", f"{lucro_operacional/1000:.1f}k"],
            y = [receita_bruta, -custo_total, lucro_operacional],
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))
        fig.update_layout(title = "Formação do Resultado (R$)", showlegend = False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Ponto de Equilíbrio")
        # Calculo simples de ponto de equilíbrio (Custos Fixos / Margem Contribuição Unitária)
        # Simplificação: Considerando que o custo variável é 60% do preço
        margem_contribuicao_unit = preco_leite * 0.40 
        ponto_equilibrio_litros = custos_fixos_estimados / margem_contribuicao_unit if margem_contribuicao_unit > 0 else 0
        
        st.metric("Litros/Dia para Zero a Zero", f"{ponto_equilibrio_litros:,.0f} L")
        
        delta_pe = producao_dia - ponto_equilibrio_litros
        if delta_pe > 0:
            st.success(f"Você está {delta_pe:.0f} L acima do Ponto de Equilíbrio! 🚀")
        else:
            st.error(f"Faltam {-delta_pe:.0f} L para pagar as contas.")

    # --- BOTÃO DE DOWNLOAD ---
    st.markdown("### 💾 Salvar Simulação")
    
    # Criar um CSV com os resultados
    simulation_data = {
        'Parametro': ['Litros/Vaca', 'Preço Leite', 'Receita Bruta', 'Lucro'],
        'Valor': [litros_vaca, preco_leite, receita_bruta, lucro_operacional]
    }
    df_sim = pd.DataFrame(simulation_data)
    
    csv = df_sim.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="Baixar Relatório (CSV)",
        data=csv,
        file_name='simulacao_cangerana.csv',
        mime='text/csv',
    )

except FileNotFoundError:
    st.error("⚠️ Arquivo Excel não encontrado!")
    st.info(f"Certifique-se de que o arquivo 'Demostrativo de resultado v24.xlsx' está na mesma pasta que este script.")
except Exception as e:
    st.error(f"Ocorreu um erro ao ler a planilha: {e}")
    st.write("Dica: Verifique se o nome das abas ou colunas mudou.")