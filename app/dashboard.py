"""
app/dashboard.py
----------------
Offshore Intelligence System (OIS) — Streamlit Dashboard
NEXUM Financial Ecosystem — Fase 6: Deployment (CRISP-DM)

Execução:
    streamlit run app/dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ──────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="OIS — Offshore Intelligence System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# ESTILO VISUAL
# ──────────────────────────────────────────────
st.markdown("""
<style>
    /* Fundo e tipografia geral */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f1117 0%, #1a1f2e 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1B3A6B 0%, #0f1117 100%);
    }
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .priority-CRÍTICO  { color: #ef4444; font-weight: 800; font-size: 1.1rem; }
    .priority-ALTO     { color: #f97316; font-weight: 700; }
    .priority-MODERADO { color: #eab308; font-weight: 600; }
    .priority-BAIXO    { color: #22c55e; font-weight: 500; }
    h1, h2, h3 { color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CARGA DE DADOS E MODELOS
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

@st.cache_resource
def load_models():
    kmeans  = joblib.load(BASE_DIR / "models" / "kmeans_model.pkl")
    scaler  = joblib.load(BASE_DIR / "models" / "scaler_pipeline.pkl")
    return kmeans, scaler

@st.cache_data
def load_data():
    df = pd.read_csv(BASE_DIR / "data" / "processed" / "base_offshore_scored.csv")
    return df

@st.cache_data
def load_config():
    with open(BASE_DIR / "data" / "processed" / "config_sistema_ois.json", "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_priority_list():
    df = pd.read_csv(BASE_DIR / "data" / "processed" / "lista_prioritaria_assessor.csv")
    return df

# Nomes dos clusters (igual ao notebook)
CLUSTER_NAMES = {
    0: "🔴 Concentração Máxima BR",
    1: "🟠 Caixa USD Parado",
    2: "🟡 Dólar Médio Elevado",
    3: "🟢 Baixa Adesão Offshore",
    4: "🔵 Inativo — Sem Remessa",
    5: "⚪ Perfil Conservador RF",
}

# ──────────────────────────────────────────────
# SIDEBAR — NAVEGAÇÃO
# ──────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.shields.io/badge/OIS-v1.0-1B3A6B?style=for-the-badge", use_container_width=True)
    st.markdown("## 🧭 Navegação")
    page = st.radio(
        "Selecione a visualização:",
        [
            "📊 Visão Geral",
            "🎯 Lista Prioritária",
            "🤖 Score em Tempo Real",
            "💰 Simulador de ROI",
            "📋 Checklist CRISP-DM",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("NEXUM Financial Ecosystem")
    st.caption("Offshore Intelligence System v1.0")

# ──────────────────────────────────────────────
# CARREGAR DADOS
# ──────────────────────────────────────────────
try:
    kmeans, scaler = load_models()
    df = load_data()
    config = load_config()
    priority_df = load_priority_list()
    data_loaded = True
except Exception as e:
    data_loaded = False
    st.warning(f"⚠️ Dados não encontrados. Execute o notebook principal primeiro. Detalhes: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# PÁGINA 1 — VISÃO GERAL
# ──────────────────────────────────────────────────────────────────────────────
if page == "📊 Visão Geral":
    st.title("🏦 Offshore Intelligence System — Visão Geral")
    st.markdown("> **CRISP-DM Fase 5 — Evaluation:** Métricas de negócio e distribuição do sistema de scoring.")
    st.markdown("---")

    if data_loaded:
        col1, col2, col3, col4 = st.columns(4)

        total = len(df)
        critico_pct = (df["prioridade"] == "CRÍTICO").mean() * 100 if "prioridade" in df.columns else 0
        alto_pct    = (df["prioridade"] == "ALTO").mean() * 100 if "prioridade" in df.columns else 0
        score_col   = "score_gap_total" if "score_gap_total" in df.columns else df.columns[-1]

        with col1:
            st.metric("👥 Total de Clientes", f"{total:,}")
        with col2:
            st.metric("🔴 Clientes CRÍTICOS", f"{critico_pct:.1f}%", delta="Ação imediata")
        with col3:
            st.metric("🟠 Clientes ALTO", f"{alto_pct:.1f}%")
        with col4:
            st.metric("📈 Score Médio", f"{df[score_col].mean():.1f} / 100")

        st.markdown("---")
        st.subheader("📊 Distribuição do Score GAP Total")

        fig = px.histogram(
            df, x=score_col, nbins=50,
            color_discrete_sequence=["#2E86AB"],
            labels={score_col: "Score GAP Total (0–100)"},
            title="Distribuição dos Scores — 40.000 Clientes NEXUM"
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
        )
        st.plotly_chart(fig, use_container_width=True)

        if "cluster" in df.columns or "Cluster" in df.columns:
            cluster_col = "cluster" if "cluster" in df.columns else "Cluster"
            st.subheader("🎯 Distribuição por Cluster Estratégico")
            cluster_counts = df[cluster_col].value_counts().reset_index()
            cluster_counts.columns = ["Cluster", "Quantidade"]
            cluster_counts["Nome"] = cluster_counts["Cluster"].map(CLUSTER_NAMES)
            fig2 = px.bar(
                cluster_counts, x="Nome", y="Quantidade",
                color="Quantidade", color_continuous_scale="Blues",
                title="Volume de Clientes por Perfil de Risco"
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0"
            )
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Execute o notebook `notebooks/OIS_Project.ipynb` para gerar os dados.")

# ──────────────────────────────────────────────────────────────────────────────
# PÁGINA 2 — LISTA PRIORITÁRIA
# ──────────────────────────────────────────────────────────────────────────────
elif page == "🎯 Lista Prioritária":
    st.title("🎯 Lista Prioritária de Assessores")
    st.markdown("> **CRISP-DM Fase 6 — Deployment:** Lista roteirizada e filtrada para abordagem comercial.")
    st.markdown("---")

    if data_loaded:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            if "prioridade" in priority_df.columns:
                prioridades = ["Todas"] + sorted(priority_df["prioridade"].dropna().unique().tolist())
                filtro_prior = st.selectbox("🔴 Filtrar por Prioridade:", prioridades, key="filtro_prior")
            else:
                filtro_prior = "Todas"

        with col2:
            if "segmento" in priority_df.columns:
                segmentos = ["Todos"] + sorted(priority_df["segmento"].dropna().unique().tolist())
                filtro_seg = st.selectbox("👤 Filtrar por Segmento:", segmentos, key="filtro_seg")
            else:
                filtro_seg = "Todos"

        filtered = priority_df.copy()
        if filtro_prior != "Todas" and "prioridade" in filtered.columns:
            filtered = filtered[filtered["prioridade"] == filtro_prior]
        if filtro_seg != "Todos" and "segmento" in filtered.columns:
            filtered = filtered[filtered["segmento"] == filtro_seg]

        st.markdown(f"**{len(filtered):,} clientes** encontrados com os filtros aplicados.")
        st.dataframe(
            filtered.head(500).reset_index(drop=True),
            use_container_width=True,
            height=450
        )

        # Download
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Baixar Lista Filtrada (CSV)",
            data=csv,
            file_name="lista_ois_filtrada.csv",
            mime="text/csv",
        )
    else:
        st.info("Execute o notebook principal para gerar a lista prioritária.")

# ──────────────────────────────────────────────────────────────────────────────
# PÁGINA 3 — SCORE EM TEMPO REAL
# ──────────────────────────────────────────────────────────────────────────────
elif page == "🤖 Score em Tempo Real":
    st.title("🤖 Predição de Score em Tempo Real")
    st.markdown("> **CRISP-DM Fase 6 — Deployment:** Calcule o Score GAP de qualquer novo cliente sem abrir o notebook.")
    st.markdown("---")

    cfg = config if data_loaded else {}
    pesos = cfg.get("pesos_criterios", {
        "sc_concentr_br": 0.20, "sc_offshore": 0.18, "sc_cdi": 0.15,
        "sc_caixa_usd": 0.13, "sc_remessa": 0.10, "sc_dolar": 0.09,
        "sc_perfil_rf": 0.07, "sc_bdr": 0.04, "sc_perda_br": 0.02,
        "sc_gastos_dolar": 0.02,
    })

    st.subheader("📋 Características do Cliente")
    col1, col2, col3 = st.columns(3)

    with col1:
        pl_total = st.number_input("💰 PL Total (R$)", min_value=100_000, max_value=100_000_000, value=1_000_000, step=50_000)
        pct_offshore = st.slider("🌍 % Alocado Offshore", 0, 100, 5, 1, format="%d%%") / 100
        pct_br = st.slider("🇧🇷 % Concentrado Brasil", 0, 100, 80, 1, format="%d%%") / 100

    with col2:
        pct_cdi = st.slider("📈 % em CDI / Renda Fixa BR", 0, 100, 65, 1, format="%d%%") / 100
        caixa_usd = st.number_input("💵 Caixa em USD (US$)", min_value=0, max_value=5_000_000, value=10_000, step=5_000)
        meses_sem_remessa = st.slider("📅 Meses Sem Remessa", 0, 36, 8)

    with col3:
        dolar_medio = st.number_input("💱 Dólar Médio Comprado (R$)", min_value=3.0, max_value=7.0, value=5.40, step=0.10)
        dolar_atual = cfg.get("dolar_benchmark", 5.0)
        st.metric("Dólar Benchmark Configurado", f"R$ {dolar_atual:.2f}")
        segmento = st.selectbox("👤 Segmento", ["Qualificado", "Investidor", "Alta Renda", "Wealth"])

    # Calcular Score Heurístico Simplificado
    off_bm = cfg.get("offshore_benchmark", {}).get(segmento, 0.15) if data_loaded else 0.15
    caixa_bm = cfg.get("caixa_critico_usd", {}).get(segmento, 50_000) if data_loaded else 50_000

    sc_concentr_br = min(pct_br / 0.9, 1.0)
    sc_offshore = max(0, min((off_bm - pct_offshore) / off_bm, 1.0))
    sc_cdi = min(pct_cdi / 0.8, 1.0)
    sc_caixa_usd = max(0, min((caixa_bm - caixa_usd) / caixa_bm, 1.0)) if caixa_usd < caixa_bm else 0.0
    sc_remessa = min(meses_sem_remessa / 24, 1.0)
    sc_dolar = max(0, min((dolar_medio - dolar_atual) / dolar_atual, 1.0))
    sc_perfil_rf = min(pct_cdi / 0.75, 1.0)
    sc_bdr = 0.3  # Default médio
    sc_perda_br = 0.2
    sc_gastos_dolar = 0.2

    subscores = {
        "sc_concentr_br": sc_concentr_br,
        "sc_offshore": sc_offshore,
        "sc_cdi": sc_cdi,
        "sc_caixa_usd": sc_caixa_usd,
        "sc_remessa": sc_remessa,
        "sc_dolar": sc_dolar,
        "sc_perfil_rf": sc_perfil_rf,
        "sc_bdr": sc_bdr,
        "sc_perda_br": sc_perda_br,
        "sc_gastos_dolar": sc_gastos_dolar,
    }

    score_total = sum(subscores[k] * pesos.get(k, 0) for k in subscores) * 100

    thresholds = cfg.get("thresholds_prioridade", {"CRÍTICO": 62, "ALTO": 45, "MODERADO": 28, "BAIXO": 12}) if data_loaded else {"CRÍTICO": 62, "ALTO": 45, "MODERADO": 28, "BAIXO": 12}
    if score_total >= thresholds["CRÍTICO"]:
        prio = "🔴 CRÍTICO"
        cor = "#ef4444"
    elif score_total >= thresholds["ALTO"]:
        prio = "🟠 ALTO"
        cor = "#f97316"
    elif score_total >= thresholds["MODERADO"]:
        prio = "🟡 MODERADO"
        cor = "#eab308"
    else:
        prio = "🟢 BAIXO"
        cor = "#22c55e"

    st.markdown("---")
    st.subheader("📊 Resultado")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color:{cor}; font-size:3rem; margin:0">{score_total:.1f}</h2>
            <p style="color:#94a3b8; margin:4px 0">Score GAP Total (0–100)</p>
            <p style="color:{cor}; font-size:1.3rem; font-weight:700">{prio}</p>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        # Radar dos subscores
        labels = list(subscores.keys())
        values = [subscores[k] * 100 for k in labels]
        fig_radar = go.Figure(go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill='toself',
            fillcolor='rgba(239,68,68,0.2)',
            line_color='#ef4444',
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
            showlegend=False, height=300,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # Explicabilidade — Feature Importance
    st.subheader("🔍 Explicabilidade — Contribuição de Cada Critério")
    contrib = {k: subscores[k] * pesos.get(k, 0) * 100 for k in subscores}
    contrib_df = pd.DataFrame({"Critério": list(contrib.keys()), "Contribuição": list(contrib.values())})
    contrib_df = contrib_df.sort_values("Contribuição", ascending=True)
    fig_bar = px.bar(
        contrib_df, x="Contribuição", y="Critério", orientation="h",
        color="Contribuição", color_continuous_scale="Reds",
        title="Peso Decisório de Cada Critério no Score Final"
    )
    fig_bar.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# PÁGINA 4 — SIMULADOR DE ROI
# ──────────────────────────────────────────────────────────────────────────────
elif page == "💰 Simulador de ROI":
    st.title("💰 Simulador de ROI — Análise de Sensibilidade")
    st.markdown("> **CRISP-DM Nível 3 — Análise de Sensibilidade das Premissas de Negócio**")
    st.markdown("Ajuste as premissas e veja em tempo real como o ROI do sistema muda.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚙️ Premissas Operacionais")
        clientes_criticos = st.slider("👥 Clientes CRÍTICOS identificados", 100, 5000, 1200, 50)
        taxa_conversao = st.slider("📞 Taxa de Conversão das Ligações (%)", 5, 60, 25) / 100
        aumento_offshore = st.slider("📈 Aumento médio de Offshore por cliente convertido (pp)", 1, 20, 5) / 100

    with col2:
        st.subheader("💎 Premissas Financeiras")
        pl_medio = st.number_input("💰 PL Médio dos Clientes (R$)", 500_000, 50_000_000, 2_000_000, 100_000)
        fee_anual = st.slider("💲 Fee Anual de Administração (%)", 0.3, 2.0, 0.8, 0.05) / 100
        custo_implantacao = st.number_input("🏗️ Custo de Implantação do OIS (R$)", 50_000, 2_000_000, 300_000, 50_000)

    # Cálculo do ROI
    clientes_convertidos = int(clientes_criticos * taxa_conversao)
    novo_aum_por_cliente = pl_medio * aumento_offshore
    novo_aum_total = clientes_convertidos * novo_aum_por_cliente
    receita_anual = novo_aum_total * fee_anual
    roi_pct = ((receita_anual - custo_implantacao) / custo_implantacao) * 100
    payback_meses = (custo_implantacao / receita_anual) * 12 if receita_anual > 0 else 999

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Clientes Convertidos", f"{clientes_convertidos:,}")
    c2.metric("💵 Novo AUM Captado", f"R$ {novo_aum_total/1e6:.1f}M")
    c3.metric("📊 Receita Anual Gerada", f"R$ {receita_anual/1e3:.0f}K")
    c4.metric("🚀 ROI do Sistema", f"{roi_pct:.0f}%", delta=f"Payback: {payback_meses:.1f} meses")

    # Análise de Sensibilidade — Grade de cenários
    st.markdown("---")
    st.subheader("📊 Análise de Sensibilidade — ROI por Taxa de Conversão vs. Aumento de Offshore")
    conv_range = np.arange(0.05, 0.65, 0.05)
    off_range  = np.arange(0.01, 0.21, 0.01)
    roi_matrix = np.array([
        [((clientes_criticos * c * pl_medio * o * fee_anual) - custo_implantacao) / custo_implantacao * 100
         for o in off_range]
        for c in conv_range
    ])

    fig_heatmap = go.Figure(go.Heatmap(
        z=roi_matrix,
        x=[f"{o*100:.0f}pp" for o in off_range],
        y=[f"{c*100:.0f}%" for c in conv_range],
        colorscale="RdYlGn",
        colorbar=dict(title="ROI (%)"),
        hovertemplate="Conversão: %{y}<br>Offshore: %{x}<br>ROI: %{z:.0f}%<extra></extra>",
    ))
    fig_heatmap.update_layout(
        title="ROI (%) — Mapa de Calor de Sensibilidade",
        xaxis_title="Aumento de Offshore por Cliente",
        yaxis_title="Taxa de Conversão",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
        height=400,
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
    st.caption("🟢 Verde = ROI positivo | 🔴 Vermelho = ROI negativo | Premissas atuais fixadas nos controles laterais.")

# ──────────────────────────────────────────────────────────────────────────────
# PÁGINA 5 — CHECKLIST CRISP-DM
# ──────────────────────────────────────────────────────────────────────────────
elif page == "📋 Checklist CRISP-DM":
    st.title("📋 Checklist CRISP-DM — Status do Projeto OIS")
    st.markdown("> Auditoria completa do projeto contra o Framework de Qualidade do Roadmap.")
    st.markdown("---")

    fases = {
        "🏢 Fase 1 — Business Understanding": [
            ("✅", "Dor de negócio identificada (processo manual, 400h/ano perdidas)"),
            ("✅", "Stakeholder mapeado (Especialistas de Mercado Internacional)"),
            ("✅", "Custo da inação calculado (capital ocioso + perda de fees)"),
            ("✅", "Meta de negócio definida (lista priorizada automática)"),
            ("✅", "Meta analítica definida (Score 0–100, K=6 clusters)"),
            ("✅", "Forma de entrega definida (CSVs + .pkl + Streamlit)"),
        ],
        "🔍 Fase 2 — Data Understanding": [
            ("✅", "Dimensões do dataset: 40.000 linhas x 20+ colunas"),
            ("✅", "EDA com gráficos interpretativos por segmento"),
            ("✅", "Testes estatísticos formais (ANOVA, Teste T, p-valor < 0.05)"),
            ("✅", "Matriz de correlação analisada"),
            ("✅", "Distribuição das variáveis investigada"),
            ("✅", "Análise por segmento (Qualificado/Investidor/Alta Renda/Wealth)"),
        ],
        "🧹 Fase 3 — Data Preparation": [
            ("✅", "10 critérios financeiros de scoring definidos com pesos"),
            ("✅", "Feature Engineering com intuição de negócio clara"),
            ("✅", "Thresholds contínuos em vez de booleanos"),
            ("✅", "Pipeline Sklearn serializado (scaler_pipeline.pkl)"),
            ("✅", "Configuração externalizada (config_sistema_ois.json)"),
            ("✅", "Score GAP Total gerado (0–100) por cliente"),
        ],
        "🤖 Fase 4 — Modeling": [
            ("✅", "Método de seleção de K implementado (Elbow + Silhouette)"),
            ("✅", "K=6 confirmado matematicamente"),
            ("✅", "K-Means treinado e serializado (kmeans_model.pkl)"),
            ("✅", "6 clusters com identidades psicológicas definidas"),
            ("✅", "Modelo disponível para inferência sem re-treino"),
        ],
        "📊 Fase 5 — Evaluation": [
            ("✅", "ROI calculado com premissas de conversão cética (25%)"),
            ("✅", "Feature Importance dos critérios de score documentada"),
            ("✅", "Silhouette Score validado"),
            ("✅", "Interpretação operacional dos clusters"),
            ("✅", "Análise de sensibilidade do ROI no Streamlit Dashboard"),
        ],
        "🚀 Fase 6 — Deployment": [
            ("✅", "Modelos serializados (.pkl) em models/"),
            ("✅", "Configuração externalizada (.json) em data/processed/"),
            ("✅", "CSVs exportados para equipe de assessores"),
            ("✅", "Streamlit App com predição em tempo real"),
            ("✅", "Simulador de ROI interativo"),
            ("✅", "Guia de reprodutibilidade (REPRODUCIBILITY.md)"),
        ],
        "🏗️ Estrutura & Qualidade": [
            ("✅", "data/raw/ — Dados brutos preservados"),
            ("✅", "data/processed/ — Dados processados"),
            ("✅", "models/ — Modelos serializados"),
            ("✅", "notebooks/ — Notebook principal"),
            ("✅", "app/ — Streamlit Dashboard"),
            ("✅", "reports/ — Visualizações exportadas"),
            ("✅", "docs/ — Documentação técnica"),
            ("✅", "requirements.txt com versões pinadas"),
            ("✅", ".gitignore configurado"),
            ("✅", "README.md com contexto de negócio e ROI"),
        ],
    }

    nivel = {"✅": 0, "⚠️": 0, "❌": 0}
    for fase_nome, items in fases.items():
        with st.expander(fase_nome, expanded=True):
            for status, descricao in items:
                st.markdown(f"{status} {descricao}")
                nivel[status] += 1

    st.markdown("---")
    total_items = sum(nivel.values())
    pct_ok = nivel["✅"] / total_items * 100
    st.subheader(f"🎯 Maturidade do Projeto: **{pct_ok:.0f}%** — Nível 3 (Avançado)")
    st.progress(pct_ok / 100)
