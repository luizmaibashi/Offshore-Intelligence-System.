# ADR-0001: K estatístico real (K=2) substitui a narrativa de 6 clusters

**Data**: 2026-08-25
**Status**: Accepted
**Proposto por**: Luiz Maibashi (com Claude Code, refatoração de honestidade estatística)
**Contexto**: `offshore_intelligence_system` — motor de score + clusterização K-Means

---

## 1. Contexto (o quê?)

O `README.md` e o `docs/crisp_dm_checklist.md` da v1 do projeto descreviam uma segmentação de
**6 clusters nomeados** (Concentração Máxima BR, Caixa USD Parado, Dólar Médio Elevado, Baixa
Adesão Offshore, Inativo, Perfil Conservador RF), cada um com script de abordagem comercial
próprio, apresentada como "confirmada pelo Elbow Method e Silhouette Score".

Ao retomar o projeto para elevá-lo ao padrão de rigor estatístico usado hoje em outros projetos
do portfólio (`payflow_inadimplencia`, `stable-treasury`), rodei `notebooks/OIS_Project.ipynb`
do zero (Restart & Run All, cópia isolada, mesma seed) para conferir os números antes de
documentá-los. O código da célula de seleção de K é:

```python
best_k = list(K_range)[silhouettes.index(max(silhouettes))]
...
K_FINAL = best_k
kmeans_final = KMeans(n_clusters=K_FINAL, random_state=SEED, n_init=10)
```

Ou seja, `K_FINAL` **não é um valor fixo em 6** — é o resultado do próprio critério
estatístico (maior Silhouette Score no intervalo K∈[2,12]). A saída real, reproduzida de forma
idêntica em duas execuções independentes:

```
K ótimo: K = 2  |  Silhouette Score máximo: 0.2040
```

**Restrições técnicas:**
- Base de clientes é sintética (log-normal, sem rótulo real de comportamento) — não há como
  validar os clusters contra um resultado de negócio observado, só contra a métrica interna
  (Silhouette).
- Silhouette 0,2040 é fraco pela referência usual (Kaufman & Rousseeuw): >0,50 estrutura forte,
  0,25–0,50 razoável, <0,25 estrutura fraca ou artificial. K=2 já está nessa faixa fraca — não
  há K melhor disponível no intervalo testado, só piores.

**Dependências afetadas:**
- `app/dashboard.py` (aba "Sobre o projeto" e qualquer visualização de cluster)
- `models/kmeans_model.pkl` (já foi treinado com `K_FINAL = best_k`, ou seja, já é K=2 — o
  artefato serializado nunca teve 6 clusters; só a documentação afirmava isso)
- `README.md`, `docs/crisp_dm_checklist.md` (narrativa a corrigir)

---

## 2. Decisão (por quê?)

**O que escolhemos:** documentar e comunicar o projeto com K=2 (o resultado real do próprio
critério estatístico do projeto), não K=6. Não forçar `n_clusters=6` fixo para recuperar a
narrativa de 6 perfis comerciais.

**Razão principal:**

"Se mantivéssemos a narrativa de 6 clusters: o projeto afirma uma segmentação que o próprio
código nunca produziu — o artefato salvo (`kmeans_model.pkl`) e o texto de venda descreveriam
coisas diferentes. Qualquer entrevistador técnico que rodasse o notebook encontraria a
divergência em segundos, e isso derruba a credibilidade do projeto inteiro, não só dessa seção."

"Seguindo com K=2 real: o projeto passa a dizer exatamente o que o código faz. É uma
segmentação mais pobre narrativamente (2 grupos, não 6 perfis com script de venda), mas é
verificável — e abre espaço para registrar honestamente que Silhouette fraco (0,20) significa
que a base sintética não tem estrutura de cluster forte o suficiente para sustentar uma
segmentação rica. Isso é comparável ao que o `payflow_inadimplencia` fez ao publicar AUC 0,56
na zona cinzenta: um resultado menos vistoso, mas real, vale mais para o portfólio do que um
resultado bonito que não sobrevive a uma verificação."

---

## 3. Consequências

**Positivas:**
- Documentação passa a bater com o artefato serializado — zero divergência entre o que é dito e
  o que o modelo faz.
- Abre um precedente saudável para o resto da refatoração: qualquer número relatado no
  README/checklist precisa ter saída de notebook por trás, reproduzida.
- Silhouette fraco vira um achado honesto do projeto (limite de expressividade de uma base
  sintética log-normal para clustering), não um problema escondido.

**Negativas / débito incorrido:**
- A narrativa comercial fica mais fraca — "2 grupos" não vende tão bem quanto "6 perfis com
  script pronto". Isso é aceito conscientemente: é o mesmo trade-off que payflow e shadow_fx já
  assumiram (honestidade > venda).
- Os 6 scripts de abordagem por perfil do README anterior precisam ser removidos ou
  reformulados em cima de 2 grupos (ou de faixas de score, que já existem e são reais —
  CRÍTICO/ALTO/MODERADO/BAIXO — e não dependem do clustering).
- Effect size (η²) das comparações ANOVA/T-test (F=450,13; t=−15,89) não foi calculado pelo
  notebook — fica registrado como débito, não fabricado agora.

**Timeline:**
- Implementação (README + checklist + remoção da narrativa de 6 clusters): mesma sessão.
- Não há re-treino necessário — o modelo salvo já é K=2.

---

## 4. Alternativas descartadas

| Opção | Vantagem | Por quê rejeitada |
|-------|----------|------------------|
| Forçar `n_clusters=6` fixo, documentado como decisão de negócio | Recupera os 6 scripts de venda, mantém K "redondo" e fácil de vender | Rejeitada nesta rodada: o usuário optou por honestidade com o K real em vez de re-treinar para forçar um número mais vistoso. Fica como opção futura, documentada aqui, se algum dia houver decisão de negócio explícita para isso. |
| Manter README como estava (K=6 narrativo) | Zero esforço, texto já pronto e vistoso | ❌ Divergência entre documentação e artefato real — o tipo de furo que a mineração de débitos deste portfólio existe para achar |
| Trocar de algoritmo (DBSCAN, Agglomerative) para tentar Silhouette melhor | Pode achar estrutura que K-Means não vê | Fora de escopo desta rodada (é sobre honestidade do que já existe, não sobre re-otimizar o modelo) — fica como próximo passo em `docs/adr/` futuro se o Luiz quiser investir mais tempo aqui |

---

## 5. Impacto e validação

**Métrica de sucesso:** README e `crisp_dm_checklist.md` descrevem exatamente K=2 e Silhouette
0,2040, sem menção a 6 clusters nomeados como resultado do modelo.

**Como verificar:** rodar `jupyter nbconvert --to notebook --execute` no notebook e conferir que
a saída de `K ótimo` bate com o que está escrito na documentação.

**Cenário de regressão:** se alguém no futuro re-treinar o modelo com dado diferente e o K ótimo
mudar, a documentação precisa ser atualizada junto — não é um número fixo, é derivado do dado.

---

## 6. Referências

- `notebooks/OIS_Project.ipynb` — célula de seleção de K (Elbow + Silhouette)
- `models/kmeans_model.pkl` — artefato já treinado com K=2
- `[[project_refatoracao_portfolio_maturidade]]` (memória) — origem da decisão de refatorar o
  portfólio para o padrão de rigor atual
- Comparável a: `payflow_inadimplencia` débito #34 (AUC 0,56 publicado como resultado honesto)
