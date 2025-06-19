<h1 align="center">📉 Análise de Ruptura de Estoque</h1>
<p align="center">Identifique produtos com estoque que pararam de vender e estime o impacto financeiro</p>

<p align="center">
  <a href="https://rupturas-wlmrhploartgj9bp529dyo.streamlit.app/" target="_blank">
    <img src="https://img.shields.io/badge/Ver App Online-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  </a>
  <a href="https://www.linkedin.com/in/gustavo-barbosa-868976236/" target="_blank">
    <img src="https://img.shields.io/badge/Autor-Gustavo Barbosa-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white"/>
  </a>
</p>

---

Veja o APP ONLINE link: https://rupturas-wlmrhploartgj9bp529dyo.streamlit.app/

## 🧠 Visão Geral

Esta aplicação permite detectar produtos com **estoque disponível que não venderam no período esperado**, calculando a **perda de receita estimada** por oportunidades de venda não realizadas.

A análise considera:

- Demanda diária esperada
- Tempo desde a última venda
- Estoque atual
- Valor unitário médio

> Ao final, você obtém **indicadores financeiros e recomendações de ação**.

---

## 📁 Arquivos Necessários

Para rodar a análise, é necessário carregar **três arquivos `.csv`**:

| Arquivo | Colunas obrigatórias | Separador |
|--------|----------------------|-----------|
| `estoque_leadtime.csv` | `produto_id`, `quantidade_estoque` | vírgula `,` |
| `VendasGerais.csv` | `id`, `data` | ponto e vírgula `;` |
| `ItensdeVendas.csv` | `produto_id`, `vendas_id`, `item_quantidade`, `valor_unitario` | ponto e vírgula `;` |

Você pode visualizar um exemplo de cada um diretamente na interface da aplicação.

---

## 📊 Métricas Calculadas

- Produtos afetados por ruptura
- Unidades perdidas estimadas
- Receita não realizada (`oportunidade_perdida`)
- Valor médio perdido por produto

---

## 📈 Visualizações Interativas

- Top 10 produtos com maior perda financeira
- Histograma: dias sem vendas
- Dispersão: dias sem venda vs oportunidade perdida
- Tabela com filtros e botão para download

---

## 💡 Lógica da Análise

```text
1. Estimar demanda média diária dos produtos
2. Calcular tempo desde a última venda
3. Estimar dias esperados para nova venda
4. Comparar com dias sem venda para detectar ruptura
5. Calcular unidades perdidas e valor da oportunidade perdida
6. Gerar insights acionáveis com foco em vendas e exposição
```

🧾 Como rodar localmente

# Clone o repositório
git clone https://github.com/seu-usuario/nome-do-repositorio.git
cd nome-do-repositorio

# Crie e ative um ambiente virtual (opcional, mas recomendado)
python -m venv venv
source venv/bin/activate  # no Windows use `venv\Scripts\activate`

# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação
streamlit run app.py


📌 To-Do Futuro

 Integração com banco de dados

 Relatórios automáticos por e-mail

 Integração com sistemas ERP

 Trazer mais informações como: Data do último inventário realizado no produto, Data da última entrada do produto e Quantidade de estoque no impróprio

🧑‍💻 Autor

Desenvolvido por Gustavo Barbosa

### 📫 Contato

[![LinkedIn](https://img.shields.io/badge/-LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/gustavo-barbosa-868976236/) [![Email](https://img.shields.io/badge/Email-gustavobarbosa7744@gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:gustavobarbosa7744@gmail.com)
