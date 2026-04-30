# 🛠️ Plano de Refatoração: OIS (Offshore Intelligence System)

**Objetivo:** Garantir a paridade treino-serventia (Training-Serving Parity) e centralizar a inteligência analítica seguindo o manual Maibashi.

## 🔴 Débitos Técnicos Identificados

1. **Training-Serving Skew (Grave):** A lógica de cálculo do "Score GAP Total" está duplicada no `app/dashboard.py` (Página "Score em Tempo Real"). Se os pesos ou a lógica de normalização mudarem no notebook, o dashboard fornecerá resultados errados.
2. **Hardcoded Heuristics:** Valores padrão para `sc_bdr`, `sc_perda_br` e `sc_gastos_dolar` estão fixos no frontend, em vez de virem de uma configuração ou serem processados por uma função central.
3. **Ausência de Central de Features:** O projeto possui `src/export_utils.py` para exportação de dados, mas carece de um `src/utils.py` que contenha a lógica de cálculo de scores e normalização usada tanto no treinamento quanto na inferência.
4. **Acoplamento de Lógica no Streamlit:** O arquivo `dashboard.py` contém lógica de negócio (cálculos matemáticos) misturada com lógica de interface.

## 📋 Lista de Tarefas (Checklist de Refatoração)

- [ ] **Criação do `src/utils.py`:**
    - Mover a função de cálculo de score (heurística e pesos) para este arquivo.
    - Implementar a função `calculate_score(client_data, config)` que aceite um dicionário/dataframe e retorne o score final.
- [ ] **Refatoração do `notebooks/OIS_Project.ipynb`:**
    - Importar e usar `src/utils.py` para gerar os scores da base histórica.
    - Garantir que a "fonte da verdade" para os cálculos seja o arquivo central.
- [ ] **Refatoração do `app/dashboard.py`:**
    - Remover os blocos de cálculo manual de scores (linhas 271-299).
    - Importar `src/utils.py` e chamar a função centralizada para a predição em tempo real.
- [ ] **Sincronização de Configurações:**
    - Garantir que `data/processed/config_sistema_ois.json` seja a única origem para pesos e benchmarks.

## 🚀 Próximos Passos

1. Validar se a função centralizada gera exatamente os mesmos resultados do notebook original.
2. Substituir a lógica no Streamlit e testar a calculadora em tempo real.
