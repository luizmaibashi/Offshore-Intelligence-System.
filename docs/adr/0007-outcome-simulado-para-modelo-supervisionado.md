# ADR-0007: Outcome simulado com ruído para treinar modelo supervisionado

**Data:** 2026-08-29
**Status:** Accepted
**Proposto por:** Luiz

---

## 1. CONTEXTO (O Quê?)

O OIS foi reposicionado (ADR-0006) como "auditoria de projeto de ML que chegou torto" — o que
resolve a narrativa, mas não resolve a limitação técnica de fundo: o score de priorização é
100% heurístico (pesos e thresholds sem calibração, ver ADR-0002/0003), e **nunca houve
tentativa de validá-lo contra outcome nenhum**, real ou simulado. O ticket 0006 do board
wayfinder provou que a fórmula "se comporta como desenhada" — correlação de p<0,001 entre score
e % offshore — mas isso é tautológico: prova que a equação calcula o que foi escrita pra
calcular, não que os pesos escolhidos são os certos.

Não existe outcome real disponível (ADR-0004: não há dataset público de conversão de wealth
management por cliente). A refatoração ofensiva decidida nesta sessão não tenta contornar essa
ausência fingindo dado real — decide **simular um outcome de conversão com ruído deliberado** e
treinar um classificador supervisionado sobre ele, comparando contra a heurística atual.

**Linguagem Ubíqua nova:**
- **Outcome simulado:** variável binária `converteu` (0/1) gerada artificialmente, não
  derivada 1:1 do score — carrega ruído intencional pra não ser um espelho da fórmula.
- **Ruído realista:** parte dos clientes de score alto não converte (falso positivo do
  heurístico), parte dos de score baixo converte (falso negativo) — simula o mundo real ser
  barulhento, não uma correlação perfeita.

## 2. DECISÃO (Por Quê?)

Gerar `converteu` como função probabilística do score real (score alto → maior *probabilidade*
de conversão, não conversão garantida) mais fatores de ruído não capturados pelo score (ex.:
tempo de relacionamento com o banco, evento de mercado aleatório). Treinar um classificador
(LogReg e/ou XGBoost) sobre as mesmas 10 features usadas no score heurístico, comparar contra a
heurística usando **AUC-ROC** como métrica única (independe de threshold, evita comparar
heurística e modelo em pontos de corte diferentes — achado de auditoria PAVC 2026-08-29). O
resultado dessa comparação é publicado como vier — ver §6, critério de sucesso revisado após
sabatina do Luiz: amarrar sucesso à vitória do modelo é o mesmo viés que motivou a auditoria
original.

**Parâmetro de ruído fixado (achado de auditoria PAVC 2026-08-29 — Falha #1):** o gerador do
outcome simulado deve ter **AUC teórico entre 0,75 e 0,80** quando avaliado contra o próprio
score que o gerou. Abaixo disso, sinal fraco demais pra ser um problema "difícil mas
aprendível"; acima disso, o outcome vira determinístico o bastante pra o classificador só
reaprender a fórmula do score de volta (leakage estrutural — `outcome = f(score)`,
`score = g(features)`, logo `outcome ≈ f(g(features))`), tornando "modelo bate heurística"
verdade por construção, não por capacidade preditiva real. Esse AUC teórico é calculado
gerando `converteu` uma vez, medindo `roc_auc_score(converteu, score_gap_total)`, e ajustando o
parâmetro de ruído até cair na faixa — documentado no código com o valor final obtido.

**Onde isso vive (achado de auditoria PAVC — Falha #3):** notebook novo,
`notebooks/OIS_Outcome_Simulado.ipynb`, separado de `OIS_Project.ipynb`. Consome
`data/processed/base_offshore_scored.csv` (saída já existente do pipeline principal) como
entrada — não edita nem depende de reexecutar o notebook original, e não toca em
`src/utils.py::calcular_score_ois` (fonte única, ADR-0002). Zero risco pra suíte de testes de
paridade do ticket 0006.

**Razão Principal:** um modelo supervisionado que bate a heurística **no próprio outcome
simulado** prova domínio de ML supervisionado de ponta a ponta (geração de label realista,
treino, validação, comparação contra baseline) sem alegar que o resultado vale pra mundo real —
a simulação é o objeto de estudo declarado, não uma alegação disfarçada de outcome real.

"Se não fizermos isso: o projeto nunca mostra a competência mais básica que se espera de um
portfólio de ML — treinar e validar um modelo supervisionado contra outcome, mesmo que
simulado."
"Se fizermos: ganhamos uma seção nova, honesta, que mostra o ciclo completo de ML supervisionado
— e ainda serve de exercício sobre os próprios pesos heurísticos (o modelo aprendido pode
revelar que algum dos 10 critérios importa menos do que o peso heurístico sugere)."

## 3. CONSEQUÊNCIAS

**Positivas:**
- Preenche a lacuna mais visível do portfólio atual — zero evidência de ML supervisionado
  completo no OIS até aqui.
- Reaproveita as mesmas 10 features já existentes — não exige nova coleta/engenharia de dado.
- Comparação heurística × modelo é, ela mesma, mais um capítulo de auditoria: se o modelo bater
  a heurística até no outcome simulado, é argumento a favor de recalibrar os pesos reais
  (ADR-0002) quando outcome real existir.

**Negativas:**
- Risco de vazamento (leakage): se o outcome simulado for função determinística do score, o
  classificador "aprende de volta" a própria fórmula — vira exercício vazio. Mitigado pelo
  ruído deliberado (ver §5, critério de sucesso).
- Risco de má interpretação: alguém lendo rápido pode achar que "modelo bate heurística" prova
  algo sobre o mundo real. Precisa de aviso explícito, do mesmo nível do ADR-0004, em toda
  visualização/resultado dessa seção.
- Escopo novo — precisa decidir onde vive (novo notebook? seção nova no existente?) sem quebrar
  a suíte de testes de paridade já existente (ticket 0006).

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Por quê foi rejeitada |
|-------|----------------------|
| Outcome = score + ruído gaussiano pequeno | Correlação quase perfeita com o score — classificador reaprende a fórmula, não prova capacidade preditiva real (decisão da sabatina). |
| Trocar de domínio para dataset público real (churn bancário Kaggle etc.) | Vira projeto novo, não OIS — perde o esqueleto/pitch de auditoria que é o diferencial (ADR-0006) e duplica o que já existe no `payflow_inadimplencia`. |
| Só fortalecer validação estatística da heurística (bootstrap/CI nos pesos) | Aprofunda o ângulo de auditoria mas não fecha a lacuna de "nunca treinei modelo supervisionado aqui" — troca-off descartado na sabatina em favor da simulação. |

## 5. IMPACTO ROI

- **Métrica de sucesso (revisado 2026-08-29, pós-sabatina):** o pipeline existe, roda de ponta
  a ponta e reporta `roc_auc_score` do classificador **e** da heurística `score_gap_total`
  contra o mesmo `converteu` simulado — **o resultado é publicado como vier, ganhe ou perca o
  classificador.** "Sucesso" não é o modelo bater a heurística; é a comparação existir e ser
  honesta. Amarrar sucesso à vitória do modelo cria incentivo de ajustar o parâmetro de ruído
  até o classificador ganhar — o mesmo tipo de resultado desenhado pra confirmar a hipótese que
  motivou a auditoria original (ADR-0001-0004). O parâmetro de ruído (AUC teórico 0,75-0,80) é
  fixado **antes** de rodar a comparação e não é reajustado depois de ver o resultado. Se o
  classificador perder, isso também é achado documentado — evidência de honestidade científica,
  não falha do experimento. Função de geração do outcome fica em código citável:
  `gerar_outcome_simulado()`, em `notebooks/OIS_Outcome_Simulado.ipynb`.
- **Timeline:** próxima sessão de execução — este ADR fecha a decisão, não a implementação.
- **Risco de regressão:** nenhum no pipeline existente se o outcome simulado viver em
  código/notebook separado do `src/utils.py::calcular_score_ois` (fonte única, ADR-0002) — não
  deve alterar a função de score heurística, só consumir sua saída como uma das entradas do
  outcome simulado.

## 6. Critérios de implementação (auditoria PAVC 2026-08-29, falsificabilidade)

- **Checagem de classe única:** se `converteu` simulado resultar em 0 casos positivos (ruído
  extremo) ou 0 negativos, abortar com erro explícito antes de treinar — nunca deixar
  scikit-learn treinar silenciosamente sobre classe degenerada.
- **Split antes de normalizar:** o holdout de treino/teste é feito ANTES de qualquer estatística
  (média/desvio do score, ou do ruído) ser calculada — normalizar com a base inteira e só depois
  splitar vaza informação do teste pro treino (leakage clássico), mesmo em outcome simulado.

## Resultado (executado 2026-08-29)

`notebooks/OIS_Outcome_Simulado.ipynb` implementado e executado de ponta a ponta.

**Achado ao calibrar:** a fórmula inicial (`score_z + ruído`) não conseguia atingir AUC teórico
acima de ~0,75 mesmo com ruído quase zero — teto estrutural, não bug de busca. Motivo: um
sorteio Bernoulli sobre probabilidade moderada (perto de 0,5) já é incerto por natureza, mesmo
quando a probabilidade é perfeitamente monótona no score. Corrigido introduzindo um parâmetro de
**temperatura** (`score_z / temperatura + ruído`) que empurra as probabilidades pra mais perto
dos extremos — achado documentado no código, não escondido.

**Calibração final:** temperatura = 0,7875 → AUC teórico do gerador = 0,7895 (dentro da faixa
0,75-0,80 do contrato). Outcome simulado: 48,7% de conversão no treino, 48,9% no teste —
balanceado, sem classe degenerada.

**Resultado da comparação (holdout, mesmo `converteu` simulado):**

| | AUC-ROC |
|---|---|
| Heurística (`score_gap_total`) | 0,7753 |
| Classificador (LogisticRegression, 7 features brutas) | 0,7608 |

**O classificador perdeu da heurística por 0,0146 AUC.** Publicado como saiu, conforme o
contrato do §5 — sem reajuste de temperatura após ver o resultado.

**Por que isso é um resultado honesto, não uma falha:** a heurística tem vantagem estrutural
nesse experimento — ela é literalmente a fonte da probabilidade de conversão simulada (o outcome
foi gerado *a partir* do score). O classificador aprende só de 7 features brutas (subconjunto
observável das 10 originais, sem os pesos exatos), sem "ver" a fórmula que gerou o rótulo. Um
classificador perder nesse desenho não implica que calibração estatística real perderia pra
heurística com outcome de conversão real — implica que, *neste teste específico, desenhado para
favorecer a heurística por construção*, ela ganhou. É essa distinção — o que o experimento prova
versus o que ele não prova — que o notebook declara explicitamente, e é o motivo do critério de
sucesso não ter sido "modelo vence" (ver §5).

## 7. LINKS RELACIONADOS

- [ADR-0002](0002-pesos-do-score-sao-heuristica-nao-calibracao.md) — os pesos que este experimento pode, no futuro, ajudar a questionar.
- [ADR-0004](0004-dataset-sintetico-como-premissa-consciente.md) — mesma disciplina de honestidade sobre dado sintético, aplicada agora ao outcome.
- [ADR-0006](0006-reposicionamento-auditoria-como-produto.md) — este ADR é a primeira peça da refatoração *ofensiva* que o reposicionamento deixou em aberto.
- Ticket 0006 (base de conhecimento) — testes de paridade que este trabalho não deve quebrar.
