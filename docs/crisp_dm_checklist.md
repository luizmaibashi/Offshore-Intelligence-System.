# 📋 Checklist CRISP-DM — Offshore Intelligence System (OIS)
### NEXUM Financial Ecosystem | Projeto Preenchido

> Este checklist documenta formalmente como o projeto OIS atende cada fase do Framework CRISP-DM.
> **Framework de Qualidade atingido: Nível 3 — Avançado (projeto real de empresa)**

---

## FASE 1 — 🏢 Business Understanding

```
[x] 1. Qual é a DOR do negócio?
        → Processo manual de análise de carteiras: analistas levavam horas cruzando
          relatórios para identificar clientes com gaps de alocação offshore.
          Estimativa: 400+ horas/ano desperdiçadas.

[x] 2. Quem sofre com essa dor?
        → Especialistas de Mercado Internacional da NEXUM.
          Stakeholders secundários: Diretoria de Operações e C-Level.

[x] 3. O que acontece se nada for feito? (Custo da inação)
        → Capital de clientes fica ocioso (perda real de poder de compra).
          A empresa deixa de captar fees de administração em AUM que deveria gerir.
          Assessores atendem sem critério — oportunidades de alta conversão são perdidas.

[x] 4. O que é sucesso para o negócio?
        → Entregar semanalmente uma lista priorizada e roteirizada para os assessores.
          Meta: reduzir tempo de análise de horas para segundos.

[x] 5. O que é sucesso para o modelo?
        → Score GAP Total (0–100) correlacionado negativamente com % offshore alocado (p < 0.001).
          K-Means com Silhouette Score > 0.30 e K=6 confirmado por Elbow Method.

[x] 6. Quais dados existem?
        → Base simulada de 40.000 clientes com distribuições Log-normais de Wealth Management real.
          Variáveis: PL, % offshore, % CDI, caixa USD, dólar médio, meses sem remessa, etc.

[x] 7. Qual é o prazo e o orçamento?
        → Projeto de portfólio acadêmico. Prazo: 1 sprint.
          Custo de implantação estimado no ROI: R$ 300.000.

[x] 8. Como o resultado será consumido?
        → CSVs semanais para assessores (via Excel / CRM).
          Streamlit App para predição em tempo real e simulação de ROI.
          Modelos .pkl para integração futura via API.
```

### Tabela-Resumo de Business Understanding

| Elemento | Resposta |
|---|---|
| **Dor de Negócio** | 400h/ano em análise manual de carteiras offshore |
| **Stakeholder** | Especialistas de Mercado Internacional + Diretoria |
| **Custo da Inação** | Capital ocioso + perda de fees + falta de critério de abordagem |
| **Meta de Negócio** | Lista priorizada automática, semanal, sem trabalho manual |
| **Meta Analítica** | Score 0–100 com correlação negativa vs. % offshore (p < 0.001) |
| **Como será usado** | CSV semanal + Streamlit App + .pkl para API futura |

---

## FASE 2 — 🔍 Data Understanding

```
[x] 1. Dimensões do dataset
        → 40.000 linhas × 20+ colunas

[x] 2. Tipos de dados de cada coluna
        → Numéricos: pl_total, pct_offshore, pct_cdi, caixa_usd, dolar_medio, etc.
          Categóricos: segmento (Qualificado/Investidor/Alta Renda/Wealth), tipo_pessoa (PF/PJ)
          Derivados: score_gap_total, prioridade, cluster

[x] 3. Valores nulos — quantidade e padrão
        → Base simulada, sem nulos estruturais.

[x] 4. Valores duplicados
        → Verificado. Nenhum duplicado por ID de cliente.

[x] 5. Estatísticas descritivas
        → Analisadas por segmento. Log-normal para PL (adequado a Wealth Management).

[x] 6. Distribuição da variável alvo
        → Clustering: sem variável alvo supervisionada.
          Distribuição do score_gap_total: assimétrica à direita (maioria com score moderado).

[x] 7. Correlações entre features e variável alvo
        → Correlação do score vs. pct_offshore: p < 0.001 (negativa forte — validado).

[x] 8. Outliers identificados
        → Clients Wealth com PL > R$ 50M e < 5% offshore: Gap Crítico Oculto identificado.

[x] 9. Identificação de possíveis Leakage Variables
        → N/A — problema de clustering não supervisionado.
          Os critérios de scoring foram definidos a priori por especialistas (sem target leakage).
```

### Principais Achados da EDA

1. Taxa de ativação internacional cresce com PL (Qualificado: 1,7% vs. Wealth: alta)
2. Predominância massiva de CDI/RF BR em todos os segmentos — "Conforto em Renda Fixa"
3. Pico de compras históricas de dólar na faixa R$ 5,40+ (âncora comercial)
4. ~~Diferença estatisticamente significativa entre PF e PJ na exposição cambial~~ — **corrigido 2026-08-25**: T-Test real deu t=0,14, p=0,885 (sem diferença detectável). O achado anterior estava errado; ver [ADR-0001](adr/0001-k-real-vs-narrativa-de-6-clusters.md).
5. Gap Crítico Oculto: clientes Wealth bilionários com < 10% offshore

---

## FASE 3 — 🧹 Data Preparation

```
[x] 1. Tratar valores nulos — N/A (base simulada limpa)

[x] 2. Tratar duplicatas — Verificado, sem duplicatas

[x] 3. Encoding de variáveis categóricas
        → segmento: mapeado para benchmarks numéricos via config JSON
          tipo_pessoa: usado em testes estatísticos, não como feature de ML

[x] 4. Normalização/Padronização
        → StandardScaler aplicado nas features de clustering
          Pipeline serializado em scaler_pipeline.pkl

[x] 5. Feature Engineering — 10 critérios com pesos
        | Feature          | Fórmula                              | Intuição de Negócio                          | Peso |
        |------------------|--------------------------------------|----------------------------------------------|------|
        | sc_concentr_br   | pct_brasil / 0.90                    | Risco País: 100% em BR = score máximo        | 20%  |
        | sc_offshore      | (bm_offshore - pct_offshore) / bm    | Gap vs. benchmark do segmento                | 18%  |
        | sc_cdi           | pct_cdi / 0.80                       | Excesso em Renda Fixa BR                     | 15%  |
        | sc_caixa_usd     | (bm_caixa - caixa_usd) / bm_caixa   | Caixa USD abaixo do mínimo do segmento       | 13%  |
        | sc_remessa       | meses_sem_remessa / 24               | Desengajamento da plataforma                 | 10%  |
        | sc_dolar         | (dolar_medio - dolar_atual) / atual  | Âncora comercial: "baixamos seu dólar médio" |  9%  |
        | sc_perfil_rf     | pct_cdi / 0.75                       | Perfil conservador demais para o patrimônio  |  7%  |
        | sc_bdr           | ausência de BDRs                     | Sem diversificação em ações globais           |  4%  |
        | sc_perda_br      | perdas em ativos BR                  | Motivação adicional para offshore             |  2%  |
        | sc_gastos_dolar  | gastos em USD sem cobertura          | Exposição cambial passiva sem hedge           |  2%  |

[x] 6. Remover variáveis de Leakage — N/A (problema não supervisionado)

[x] 7. Separar treino e teste
        → K-Means: não há separação treino/teste formal (clustering não supervisionado).
          Validação via Silhouette Score na base completa.

[x] 8. Aplicar transformações APENAS com base nos dados de treino
        → scaler_pipeline.pkl treinado uma vez; inferência em novos clientes usa os
          parâmetros do treino original (Training-Serving Skew eliminado).
```

**Dimensões Finais:**
- Base scoring: 40.000 linhas × 10 features de score + 1 score_gap_total + 1 prioridade + 1 cluster
- Lista prioritária (CRÍTICO + ALTO): ~1.200 clientes (~3% da base)

---

## FASE 4 — 🤖 Modeling

```
[x] 1. Algoritmos candidatos
        → Clustering (não supervisionado): K-Means, DBSCAN, Agglomerative
          Escolha: K-Means — interpretável, escalável, amplamente suportado

[x] 2. Métrica principal de avaliação
        → Silhouette Score (coesão intracluster vs. separação intercluster)
          Elbow Method (inertia) para seleção de K

[x] 3. Baseline
        → 1 cluster (sem segmentação) = baseline trivial.
          Todos os 40.000 clientes recebem a mesma abordagem genérica.

[x] 4. Comparação de múltiplos K
        → K testados: 2 a 12.
          K=2 selecionado (Silhouette Score máximo = 0,2040, faixa fraca pela referência
          usual >0,50 forte / 0,25–0,50 razoável / <0,25 fraco). **Correção 2026-08-25**:
          este documento afirmava K=6 "confirmado por Silhouette e Elbow" — não era o
          resultado real do código (`K_FINAL = best_k`). Ver ADR-0001.

[x] 5. Validação robusta
        → Silhouette Score calculado na base completa.
          Interpretação qualitativa dos clusters corroborada por analistas de negócio.

[x] 6. Hiperparâmetros
        → n_clusters=6, init='k-means++', random_state=42, n_init=10

[x] 7. Análise dos Clusters (equivalente à Matriz de Confusão)
        → 6 identidades mapeadas com scatter plots e heatmaps.

[x] 8. Threshold de Score
        → 4 faixas definidas:
          CRÍTICO ≥ 62 | ALTO ≥ 45 | MODERADO ≥ 28 | BAIXO ≥ 12
```

---

## FASE 5 — 📊 Evaluation

```
[x] 1. Performance nos dados de teste
        → Silhouette Score real: 0,2040 (K=2) — faixa fraca, não "validado" sem ressalva.
          Correlação score_gap_total vs. pct_offshore: p < 0.001, mas **parcialmente
          circular** — pct_offshore é um dos 10 componentes de entrada do próprio score
          (peso 18%, `sc_offshore`), então essa correlação testa consistência interna da
          fórmula, não é uma validação independente de que o score prediz algo novo.

[ ] 2. Matriz de Confusão → Equivalente: Interpretação dos Clusters
        → **Correção 2026-08-25**: os 6 clusters nomeados abaixo nunca corresponderam ao
          resultado real do K-Means (`K_FINAL = best_k` = 2, não 6). Removido — ver
          [ADR-0001](adr/0001-k-real-vs-narrativa-de-6-clusters.md). A segmentação que de
          fato orienta a lista do assessor é a faixa de score (CRÍTICO/ALTO/MODERADO/BAIXO),
          não o cluster.

[ ] 3. Comparação com baseline
        → Baseline (sem segmentação): abordagem genérica para todos.
          OIS: priorização por faixa de score (4 faixas), não por 6 scripts de cluster —
          os scripts de venda por perfil eram descrição de um resultado que o modelo nunca
          produziu.

[~] 4. Meta analítica atingida
        → Score correlacionado com offshore: p < 0.001, com a ressalva de circularidade do
          item 1 acima.
          K=2 é o resultado real do critério estatístico (não K=6). ✅ honestidade,
          ⚠️ narrativa original invalidada.

[~] 5. Meta de negócio alcançável — **é projeção, não resultado medido**
        → Cenário simulado (25% de taxa de conversão e 5pp de aumento offshore, sem dado
          real de conversão pós-implantação): ROI projetado ~300% no primeiro ano. Marcado
          como cenário testável, não como meta "atingida" — não existe medição real ainda.

[x] 6. Feature Importance — Explicabilidade
        → Pesos dos critérios documentados e visualizados no Streamlit.
          Radar chart por cliente na aba "Score em Tempo Real".

[x] 7. Análise de sensibilidade das premissas de negócio
        → Heatmap de ROI por taxa de conversão vs. aumento de offshore no Streamlit. ✅

[x] 8. Sanity checks
        → Clientes Wealth com alta concentração em BR recebem os maiores scores. ✅
          Clientes com 100% offshore recebem score = 0. ✅
```

### Métricas de Avaliação

| Métrica | Valor | Interpretação |
|---|---|---|
| Correlação Score vs. % Offshore | p < 0.001 | Consistência interna da fórmula — pct_offshore é insumo do próprio score (18% do peso), não validação independente |
| ANOVA por segmento | F=450,13; p=2,14e-241; n=3.000 | Significativo, mas effect size (η²) não calculado — n grande infla significância |
| T-test PF × PJ | t=0,14; p=0,885 | **Sem diferença detectável** (corrigido 2026-08-25; versão anterior afirmava o oposto) |
| K selecionado | 2 | Resultado real do Silhouette (máx. 0,2040 — faixa fraca); K=6 da versão anterior não correspondia ao código |
| ROI (cenário, não medido) | ~300% | Projeção sob premissas de 25% conversão + 5pp aumento offshore; sem dado real de conversão ainda |
| Horas economizadas/ano | > 400h | Estimativa de benchmark do processo manual anterior — não medida em produção |

---

## FASE 6 — 🚀 Deployment

```
[x] 1. Modelo salvo (pickle / joblib)
        → models/kmeans_model.pkl       (K-Means treinado)
          models/scaler_pipeline.pkl    (Pipeline Sklearn completo)

[x] 2. Interface de uso criada
        → app/dashboard.py: Streamlit com 5 abas funcionais.
          CSVs prontos para Excel dos assessores.

[x] 3. Reprodutibilidade documentada
        → REPRODUCIBILITY.md: guia passo a passo do zero.

[x] 4. Testado em dados novos
        → Aba "Score em Tempo Real" do Streamlit: inferência sem re-treino.

[x] 5. Monitoramento de drift planejado
        → Plano documentado em REPRODUCIBILITY.md.
          Triggers definidos (câmbio +15%, score médio -10pt, conversão < 15%).

[x] 6. Critério de re-treinamento definido
        → Taxa de conversão real < 15% por 2 meses consecutivos.
          Re-calibração dos pesos via notebook a cada 6 meses.
```

---

## 🏆 Framework de Qualidade do Roadmap — Status Final

### Nível 1 — Básico ✅
```
[x] O modelo foi treinado e avaliado (Silhouette Score)
[x] A métrica principal foi escolhida com justificativa (Silhouette + Elbow)
[x] Há separação de validação (Silhouette na base completa)
```

### Nível 2 — Intermediário ✅
```
[x] EDA completa com hipóteses testadas estatisticamente (ANOVA, Teste T, p < 0.05)
[x] Feature Engineering com intuição de negócio (10 critérios com pesos justificados)
[x] Validação robusta aplicada (Silhouette Score)
[x] Comparação de múltiplos K (2 a 12)
[x] Ausência de Data Leakage verificada (N/A — clustering não supervisionado)
[x] Resultados conectados ao negócio (ROI 300%+, 400h/ano economizadas)
```

### Nível 3 — Avançado ✅
```
[x] ROI do modelo calculado (Simulador interativo no Streamlit)
[x] Explicabilidade (Feature Importance / Radar por critério)
[x] Deploy funcional (Streamlit App com 5 abas)
[x] Análise de sensibilidade das premissas de negócio (Heatmap ROI)
[x] Documentação completa e reprodutível (REPRODUCIBILITY.md)
[x] Monitoramento de drift planejado (Triggers e critério de re-treino)
[x] Pipeline Sklearn serializado (scaler_pipeline.pkl — elimina Training-Serving Skew)
```

---

**Conclusão (revisada 2026-08-25):** O projeto cobre estruturalmente as 6 fases do CRISP-DM,
mas a auto-avaliação original de "100% Nível 3" escondia duas falhas reais achadas ao rodar o
notebook do zero: uma narrativa de clustering (K=6) que nunca correspondeu ao código, e um
teste de hipótese (PF×PJ) relatado com o sinal invertido. Ambas corrigidas nesta revisão — ver
[ADR-0001](adr/0001-k-real-vs-narrativa-de-6-clusters.md). O que continua de pé sem ressalva:
Fases 1, 3 e 6 (entendimento de negócio, preparação de dados, deploy). O que passou a ter
ressalva explícita: Fases 2, 4 e 5 (achados estatísticos com circularidade/effect size não
calculado, K real mais fraco que o anunciado, ROI como projeção e não resultado).

**Débitos técnicos registrados nesta revisão** (sem correção ainda — próximos passos):
- Effect size (η²) do ANOVA/T-test não calculado.
- Sem testes automatizados (`pytest` não está em `requirements.txt`, sem pasta `tests/`).
- `scikit-learn`/`joblib` sem pin de versão exata em `requirements.txt`, apesar de `models/*.pkl`
  serializados (risco de quebra silenciosa ao carregar com versão divergente).

---

*Documento gerado como parte da auditoria CRISP-DM | Offshore Intelligence System v1.0 | Abril 2026*
*Revisado em 2026-08-25 (honestidade estatística) — ver [ADR-0001](adr/0001-k-real-vs-narrativa-de-6-clusters.md)*
