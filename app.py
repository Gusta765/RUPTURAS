import streamlit as st
import pandas as pd
import datetime
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuração da página
st.set_page_config(
    page_title="Análise de Ruptura de Estoque",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #34495e;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .upload-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<div class="main-header">📊 Análise de Ruptura de Estoque</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Identifique produtos que deveriam ter vendido mas não venderam</div>', unsafe_allow_html=True)

# Sidebar para instruções e configurações
with st.sidebar:
    st.header("📋 Instruções")
    st.markdown("""
    **Arquivos necessários:**
    
    1. **estoque_leadtime.csv**
       - Colunas: produto_id, quantidade_estoque
       - Separador: vírgula
    
    2. **VendasGerais.csv**
       - Colunas: id, data
       - Separador: ponto e vírgula (;)
    
    3. **ItensdeVendas.csv**
       - Colunas: produto_id, vendas_id, item_quantidade, valor_unitario
       - Separador: ponto e vírgula (;)
    """)
    
    st.header("⚙️ Configurações")
    dias_demanda = st.number_input(
        "Dias para análise da demanda:",
        min_value=1,
        max_value=365,
        value=30,
        help="Número de dias para calcular a demanda média dos produtos"
    )

# Função para processar dados
@st.cache_data
def processar_dados(tb_estoque, tb_vendas, tb_itens_vendas, dias_demanda):
    """
    Processa os dados e retorna produtos com ruptura de estoque
    """
    try:
        # Corrigir valor_unitario
        tb_itens_vendas['valor_unitario'] = (
            tb_itens_vendas['valor_unitario']
            .astype(str)
            .str.replace(',', '.', regex=False)
            .str.replace('R$', '', regex=False)
            .str.strip()
        )
        tb_itens_vendas['valor_unitario'] = pd.to_numeric(tb_itens_vendas['valor_unitario'], errors='coerce')
        
        # Unir itens de venda com a venda (para pegar a data)
        df = pd.merge(tb_itens_vendas, tb_vendas, left_on='vendas_id', right_on='id')
        
        # Converter a coluna de data para datetime
        df['data'] = pd.to_datetime(df['data'], format='%Y-%m-%d %H:%M:%S,%f', errors='coerce')
        
        # Definir intervalo de análise
        data_fim = df['data'].max()
        data_ini = data_fim - datetime.timedelta(days=dias_demanda)
        
        # Filtrar vendas no intervalo de análise
        df_periodo = df[df['data'].between(data_ini, data_fim)]
        
        # Calcular demanda diária por produto
        demanda_diaria = (
            df_periodo.groupby('produto_id')['item_quantidade']
            .sum()
            .div(dias_demanda)
            .reset_index()
            .rename(columns={'item_quantidade': 'DEMANDA_DIA'})
        )
        
        # Calcular última data de venda por produto
        ultima_venda = (
            df.groupby('produto_id')['data']
            .max()
            .reset_index()
            .rename(columns={'data': 'ultima_venda'})
        )
        ultima_venda['dias_sem_venda'] = (data_fim - ultima_venda['ultima_venda']).dt.days
        
        # Calcular valor unitário médio por produto
        valor_medio = (
            tb_itens_vendas.groupby('produto_id')['valor_unitario'].mean()
            .reset_index()
            .rename(columns={'valor_unitario': 'valor_unitario_medio'})
        )
        
        # Juntar tudo
        resultado = (
            tb_estoque
            .merge(demanda_diaria, on='produto_id', how='left')
            .merge(ultima_venda, on='produto_id', how='left')
            .merge(valor_medio, on='produto_id', how='left')
        )
        
        # Substituir valores nulos na demanda por zero
        resultado['DEMANDA_DIA'] = resultado['DEMANDA_DIA'].fillna(0)
        
        # Calcular dias esperados para 1 venda
        resultado['dias_esperados_para_1_venda'] = np.where(
            resultado['DEMANDA_DIA'] > 0,
            1 / resultado['DEMANDA_DIA'],
            np.nan
        )
        
        # Calcular dias excedentes
        resultado['dias_excedentes'] = resultado['dias_sem_venda'] - resultado['dias_esperados_para_1_venda']
        
        # Calcular unidades perdidas
        resultado['unidades_perdidas'] = np.where(
            resultado['dias_esperados_para_1_venda'].notna() & (resultado['dias_esperados_para_1_venda'] > 0),
            (resultado['dias_excedentes'] // resultado['dias_esperados_para_1_venda']).fillna(0).astype(int),
            0
        )
        
        # Calcular oportunidade perdida
        resultado['oportunidade_perdida'] = resultado['unidades_perdidas'] * resultado['valor_unitario_medio']
        
        # Filtrar produtos com estoque e ruptura
        ruptura = resultado[
            (resultado['quantidade_estoque'] > 0) &
            (resultado['dias_sem_venda'] > resultado['dias_esperados_para_1_venda'])
        ]
        
        # Adicionar recomendação
        ruptura['acao_recomendada'] = 'Verificar exposição / Validar estoque físico'
        
        # Selecionar colunas relevantes
        colunas_relevantes = [
            'produto_id', 'DEMANDA_DIA', 'dias_esperados_para_1_venda',
            'dias_sem_venda', 'unidades_perdidas', 'valor_unitario_medio',
            'oportunidade_perdida', 'quantidade_estoque', 'ultima_venda', 'acao_recomendada'
        ]
        
        ruptura = ruptura[colunas_relevantes].copy()
        ruptura = ruptura.sort_values(by='oportunidade_perdida', ascending=False)
        
        return ruptura, None
        
    except Exception as e:
        return None, str(e)

# Seção de upload de arquivos
st.header("📁 Upload dos Arquivos")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("Estoque")
    arquivo_estoque = st.file_uploader(
        "estoque_leadtime.csv",
        type=['csv'],
        key="estoque",
        help="Arquivo com produto_id e quantidade_estoque"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("Vendas Gerais")
    arquivo_vendas = st.file_uploader(
        "VendasGerais.csv",
        type=['csv'],
        key="vendas",
        help="Arquivo com id e data das vendas (separado por ;)"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("Itens de Vendas")
    arquivo_itens = st.file_uploader(
        "ItensdeVendas.csv",
        type=['csv'],
        key="itens",
        help="Arquivo com produto_id, vendas_id, item_quantidade, valor_unitario (separado por ;)"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Verificar se todos os arquivos foram carregados
if arquivo_estoque and arquivo_vendas and arquivo_itens:
    try:
        # Carregar os dados
        with st.spinner("Carregando dados..."):
            tb_estoque = pd.read_csv(arquivo_estoque)
            tb_vendas = pd.read_csv(arquivo_vendas, sep=';')
            tb_itens_vendas = pd.read_csv(arquivo_itens, sep=';')
        
        # Mostrar informações dos arquivos carregados
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.success("✅ Todos os arquivos foram carregados com sucesso!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Produtos no Estoque", len(tb_estoque))
        with col2:
            st.metric("Total de Vendas", len(tb_vendas))
        with col3:
            st.metric("Itens de Vendas", len(tb_itens_vendas))
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botão para processar análise
        if st.button("🔍 Analisar Ruptura de Estoque", type="primary", use_container_width=True):
            with st.spinner("Processando análise... Por favor, aguarde."):
                ruptura, erro = processar_dados(tb_estoque, tb_vendas, tb_itens_vendas, dias_demanda)
            
            if erro:
                st.error(f"❌ Erro ao processar dados: {erro}")
            elif ruptura is None or len(ruptura) == 0:
                st.balloons()
                st.success("✅ **Nenhum produto com ruptura identificada!**")
                st.info("Todos os produtos com estoque estão dentro do padrão esperado de vendas.")
            else:
                st.success(f"✅ Análise concluída! Encontrados **{len(ruptura)}** produtos com possível ruptura.")
                
                # Métricas principais
                st.header("📊 Resumo Executivo")
                
                total_oportunidade = ruptura['oportunidade_perdida'].sum()
                total_unidades = ruptura['unidades_perdidas'].sum()
                produtos_afetados = len(ruptura)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Produtos Afetados",
                        f"{produtos_afetados:,}",
                        delta=f"{(produtos_afetados/len(tb_estoque)*100):.1f}% do estoque"
                    )
                
                with col2:
                    st.metric(
                        "Unidades Perdidas",
                        f"{total_unidades:,}",
                        delta="unidades não vendidas"
                    )
                
                with col3:
                    st.metric(
                        "Oportunidade Perdida",
                        f"R$ {total_oportunidade:,.2f}",
                        delta="receita não realizada"
                    )
                
                with col4:
                    valor_medio_oportunidade = total_oportunidade / produtos_afetados if produtos_afetados > 0 else 0
                    st.metric(
                        "Perda Média/Produto",
                        f"R$ {valor_medio_oportunidade:,.2f}",
                        delta="por produto afetado"
                    )
                
                # Gráficos
                st.header("📈 Visualizações")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Top 10 produtos com maior oportunidade perdida
                    top_10 = ruptura.head(10)
                    fig_bar = px.bar(
                        top_10,
                        x='oportunidade_perdida',
                        y='produto_id',
                        orientation='h',
                        title='Top 10 - Maior Oportunidade Perdida',
                        labels={'oportunidade_perdida': 'Oportunidade Perdida (R$)', 'produto_id': 'ID Produto'},
                        color='oportunidade_perdida',
                        color_continuous_scale='Reds'
                    )
                    fig_bar.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col2:
                    # Distribuição dos dias sem venda
                    fig_hist = px.histogram(
                        ruptura,
                        x='dias_sem_venda',
                        nbins=20,
                        title='Distribuição - Dias sem Venda',
                        labels={'dias_sem_venda': 'Dias sem Venda', 'count': 'Quantidade de Produtos'},
                        color_discrete_sequence=['#e74c3c']
                    )
                    fig_hist.update_layout(height=400)
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                # Gráfico de dispersão
                fig_scatter = px.scatter(
                    ruptura,
                    x='dias_sem_venda',
                    y='oportunidade_perdida',
                    size='unidades_perdidas',
                    color='DEMANDA_DIA',
                    title='Relação: Dias sem Venda vs Oportunidade Perdida',
                    labels={
                        'dias_sem_venda': 'Dias sem Venda',
                        'oportunidade_perdida': 'Oportunidade Perdida (R$)',
                        'DEMANDA_DIA': 'Demanda Diária'
                    },
                    hover_data=['produto_id', 'quantidade_estoque']
                )
                fig_scatter.update_layout(height=500)
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Tabela detalhada
                st.header("📋 Detalhamento dos Produtos")
                
                # Filtros para a tabela
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    min_oportunidade = st.number_input(
                        "Oportunidade mínima (R$)",
                        min_value=0.0,
                        value=0.0,
                        step=10.0
                    )
                
                with col2:
                    max_dias_sem_venda = st.number_input(
                        "Máx. dias sem venda",
                        min_value=0,
                        value=int(ruptura['dias_sem_venda'].max()) if len(ruptura) > 0 else 365,
                        step=1
                    )
                
                with col3:
                    min_estoque = st.number_input(
                        "Estoque mínimo",
                        min_value=0,
                        value=0,
                        step=1
                    )
                
                # Aplicar filtros
                ruptura_filtrada = ruptura[
                    (ruptura['oportunidade_perdida'] >= min_oportunidade) &
                    (ruptura['dias_sem_venda'] <= max_dias_sem_venda) &
                    (ruptura['quantidade_estoque'] >= min_estoque)
                ]
                
                st.info(f"Exibindo {len(ruptura_filtrada)} de {len(ruptura)} produtos")
                
                # Formatar dados para exibição
                ruptura_display = ruptura_filtrada.copy()
                ruptura_display['DEMANDA_DIA'] = ruptura_display['DEMANDA_DIA'].round(2)
                ruptura_display['dias_esperados_para_1_venda'] = ruptura_display['dias_esperados_para_1_venda'].round(1)
                ruptura_display['valor_unitario_medio'] = ruptura_display['valor_unitario_medio'].round(2)
                ruptura_display['oportunidade_perdida'] = ruptura_display['oportunidade_perdida'].round(2)
                ruptura_display['ultima_venda'] = pd.to_datetime(ruptura_display['ultima_venda']).dt.strftime('%d/%m/%Y')
                
                # Renomear colunas para exibição
                colunas_display = {
                    'produto_id': 'ID Produto',
                    'DEMANDA_DIA': 'Demanda/Dia',
                    'dias_esperados_para_1_venda': 'Dias p/ 1 Venda',
                    'dias_sem_venda': 'Dias sem Venda',
                    'unidades_perdidas': 'Unid. Perdidas',
                    'valor_unitario_medio': 'Valor Unit. (R$)',
                    'oportunidade_perdida': 'Oportunidade Perdida (R$)',
                    'quantidade_estoque': 'Estoque',
                    'ultima_venda': 'Última Venda',
                    'acao_recomendada': 'Ação Recomendada'
                }
                
                ruptura_display = ruptura_display.rename(columns=colunas_display)
                
                # Destacar valores altos
                def highlight_high_values(val, column):
                    if column == 'Oportunidade Perdida (R$)':
                        if val > ruptura['oportunidade_perdida'].quantile(0.8):
                            return 'background-color: #ffebee'
                    elif column == 'Dias sem Venda':
                        if val > ruptura['dias_sem_venda'].quantile(0.8):
                            return 'background-color: #fff3e0'
                    return ''
                
                st.dataframe(
                    ruptura_display,
                    use_container_width=True,
                    height=400
                )
                
                # Opção para download
                csv = ruptura.to_csv(index=False)
                st.download_button(
                    label="📥 Baixar Resultados (CSV)",
                    data=csv,
                    file_name=f"ruptura_estoque_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
    except Exception as e:
        st.error(f"❌ Erro ao carregar arquivos: {str(e)}")
        st.info("Verifique se os arquivos estão no formato correto e com as colunas necessárias.")

else:
    st.markdown('<div class="warning-box">', unsafe_allow_html=True)
    st.warning("⚠️ Por favor, carregue todos os três arquivos CSV para prosseguir com a análise.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar exemplo de formato dos arquivos
    with st.expander("📄 Ver exemplo de formato dos arquivos"):
        st.subheader("estoque_leadtime.csv")
        st.code("""produto_id,quantidade_estoque
PROD001,50
PROD002,25
PROD003,100""")
        
        st.subheader("VendasGerais.csv")
        st.code("""id;data
1;2024-01-15 10:30:00,000
2;2024-01-16 14:22:00,000
3;2024-01-17 09:15:00,000""")
        
        st.subheader("ItensdeVendas.csv")
        st.code("""produto_id;vendas_id;item_quantidade;valor_unitario
PROD001;1;2;25,50
PROD002;1;1;15,00
PROD001;2;3;25,50""")

# Rodapé
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #7f8c8d; font-size: 0.9rem;'>
        💡 <strong>Dica:</strong> Esta análise identifica produtos com estoque disponível mas com tempo de venda acima do esperado, 
        calculando as perdas de oportunidade correspondentes.
    </div>
    """, 
    unsafe_allow_html=True
)