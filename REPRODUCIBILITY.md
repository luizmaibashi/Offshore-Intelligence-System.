# 🚀 Guia de Reprodutibilidade — Offshore Intelligence System (OIS)

> **CRISP-DM Fase 6 — Deployment:** Este guia garante que qualquer pessoa possa reproduzir o projeto do zero.

---

## Pré-requisitos

- Python **3.10+**
- Git
- 4 GB de RAM mínimo

---

## 1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/Offshore-Intelligence-System.git
cd Offshore-Intelligence-System
```

---

## 2. Criar e Ativar Ambiente Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python -m venv venv
source venv/bin/activate
```

---

## 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

---

## 4. Executar o Notebook Principal

O notebook gera os dados processados e os modelos serializados:

```bash
jupyter notebook notebooks/OIS_Project.ipynb
```

**O que o notebook produz:**
| Arquivo | Localização | Descrição |
|---|---|---|
| `base_offshore_scored.csv` | `data/processed/` | Base completa com Score GAP e clusters |
| `lista_prioritaria_assessor.csv` | `data/processed/` | Lista filtrada para abordagem |
| `config_sistema_ois.json` | `data/processed/` | Parâmetros configuráveis do sistema |
| `kmeans_model.pkl` | `models/` | Modelo K-Means serializado |
| `scaler_pipeline.pkl` | `models/` | Pipeline de normalização serializado |

---

## 5. Rodar o Dashboard Streamlit

```bash
streamlit run app/dashboard.py
```

O app abrirá automaticamente em `http://localhost:8501`

### Funcionalidades do Dashboard:

| Aba | Descrição |
|---|---|
| 📊 Visão Geral | Distribuição de scores e clusters da base completa |
| 🎯 Lista Prioritária | Filtro interativo da lista de assessores |
| 🤖 Score em Tempo Real | Calcule o score de qualquer novo cliente (inferência sem re-treino) |
| 💰 Simulador de ROI | Análise de sensibilidade das premissas de negócio |
| 📋 Checklist CRISP-DM | Auditoria do projeto contra o Framework de Qualidade |

---

## 6. Atualizar os Parâmetros do Sistema

Os thresholds e benchmarks são configuráveis sem re-treinar o modelo:

```json
// data/processed/config_sistema_ois.json
{
  "dolar_benchmark": 5.0,         // Câmbio de referência atual (ajuste diariamente)
  "offshore_benchmark": {
    "Wealth": 0.3                  // Meta de 30% offshore para clientes Wealth
  },
  "thresholds_prioridade": {
    "CRÍTICO": 62                  // Score >= 62 = abordagem prioritária
  }
}
```

---

## 7. Extrair Imagens do Notebook (opcional)

```bash
python src/export_utils.py --notebook notebooks/OIS_Project.ipynb --output images/
```

---

## 🔄 Plano de Monitoramento de Drift

O modelo K-Means foi treinado em dados simulados com distribuições de Wealth Management reais. Em produção:

| Trigger | Ação |
|---|---|
| **Câmbio diverge > 15% do benchmark** | Atualizar `dolar_benchmark` no JSON |
| **Score médio da base cai > 10 pontos** | Suspeita de drift — re-analisar distribuição |
| **Taxa de conversão real < 10%** | Re-calibrar pesos dos critérios no notebook |
| **Novos produtos internacionais** | Adicionar critério ao sistema de scoring |
| **A cada 6 meses** | Re-treinar K-Means com dados reais coletados |

> **Critério de re-treino:** Quando a taxa de conversão real cair abaixo de **15%** por 2 meses consecutivos, iniciar ciclo de re-calibração.

---

## 📦 Estrutura Final do Repositório

```
Offshore-Intelligence-System/
│
├── README.md                        ← Contexto de negócio e impactos
├── REPRODUCIBILITY.md               ← Este guia (como rodar o projeto)
├── requirements.txt                 ← Dependências com versões pinadas
├── .gitignore
├── roadmap_data_science_crispdm.md  ← Template CRISP-DM reutilizável
│
├── data/
│   ├── raw/                         ← Dados originais (nunca modificar)
│   └── processed/                   ← Dados prontos para modelagem
│       ├── base_offshore_scored.csv
│       ├── lista_prioritaria_assessor.csv
│       └── config_sistema_ois.json
│
├── notebooks/
│   └── OIS_Project.ipynb            ← Motor analítico principal (CRISP-DM completo)
│
├── models/
│   ├── kmeans_model.pkl             ← Modelo K-Means serializado
│   └── scaler_pipeline.pkl          ← Pipeline Sklearn serializado
│
├── app/
│   └── dashboard.py                 ← Streamlit App (Deployment)
│
├── src/
│   └── export_utils.py              ← Utilitários de exportação
│
├── reports/                         ← Visualizações exportadas
├── images/                          ← Imagens para README
└── docs/
    └── crisp_dm_checklist.md        ← Checklist CRISP-DM preenchido
```

---

*Versão 1.0 | Abril 2026 | NEXUM Financial Ecosystem*
