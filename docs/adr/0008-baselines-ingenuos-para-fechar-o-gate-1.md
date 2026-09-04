# ADR-0008: Baselines ingênuos para fechar o Gate 1 que o projeto nunca fechou

**Data:** 2026-09-04
**Status:** Accepted (decisão travada — implementação pendente)
**Proposto por:** Luiz
**Contexto:** `notebooks/OIS_Outcome_Simulado.ipynb`, infra do ADR-0007

---

## 1. CONTEXTO (O Quê?)

O OIS se vende como priorização inteligente de clientes com gap de alocação offshore. A pergunta
que sustenta essa proposta de valor — *é melhor do que o que o assessor já faz hoje?* — nunca foi
respondida. O ADR-0007 comparou o score heurístico (AUC 0,7753) contra uma LogisticRegression
(0,7608) sobre outcome simulado. Verificação em sessão (2026-09-04, `/tese`): **essa é a única
comparação que existe no projeto inteiro.** Não há, em lugar nenhum do repo, comparação contra
regra de bolso — nem patrimônio, nem tempo sem contato, nem ordem aleatória.

Pelo framework dos Três Gates de Viabilidade da base de conhecimento, isso é um furo de **Gate 1**:
comparar o modelo sofisticado contra outro modelo sofisticado, e nunca contra a heurística trivial
que o negócio já usa, é comparação cega. O projeto pulou o gate mais barato e foi direto pro mais
caro.

A tese `docs/tese/refatoracao-ois-dor-resolvida/TESE.md` (base de conhecimento, veredito
2026-09-04) chegou aqui por outro caminho e no mesmo lugar. Ela tentou responder "o que o assessor
faz hoje sem a ferramenta" e falhou — duas rodadas de pesquisa não acharam confirmação pública
nenhuma da dor, e a fonte original (conversa com um amigo do mercado) está inacessível. O achado
que destravou: as respostas plausíveis são poucas e enumeráveis. Liga pros maiores por patrimônio.
Liga pra quem está há mais tempo sem contato. Liga na ordem que o CRM cuspir. Não é preciso
descobrir qual delas é a verdadeira — dá pra testar **todas**.

**Linguagem Ubíqua nova:**
- **Baseline ingênuo:** ordenação de clientes por uma única coluna bruta, sem modelo e sem pesos —
  a regra de bolso que um assessor conseguiria executar com um sort no Excel.
- **Gate 1 (viabilidade):** o teste de que a solução proposta bate a regra trivial já existente. Se
  não bate, não há problema de ML a resolver, há um sort de planilha.

## 2. DECISÃO (Por Quê?)

Medir três baselines ingênuos por **AUC-ROC** contra o **mesmo `converteu` simulado** e o **mesmo
holdout** do ADR-0007 (`train_test_split(test_size=0.3, random_state=42)`, n de teste = 900 de
3.000), publicando o resultado ao lado da heurística e do classificador na mesma tabela.

**Os três baselines, com direção travada antes de rodar:**

| Baseline | Coluna | Direção (declarada agora) | Racional de negócio |
|---|---|---|---|
| Maior patrimônio primeiro | `pl_brl` | decrescente | "Liga pros maiores clientes" — a regra mais citada do mercado |
| Mais tempo sem contato primeiro | `dias_sem_remessa` | decrescente | "Liga pra quem sumiu" — higiene de carteira |
| Ordem aleatória | — | `rng(seed=42)` | Piso de sanidade; equivale a "a ordem que o CRM cuspir" |

**A direção de cada baseline é parte do contrato e não é invertida depois de ver o AUC.** Se
`pl_brl` decrescente der AUC abaixo de 0,5, o número publicado é abaixo de 0,5. Inverter o sinal a
posteriori pra "melhorar" o baseline é o mesmo vício de desenhar o experimento pró-hipótese que a
auditoria original do OIS (ADR-0001 a 0004) existe pra corrigir. O que a inversão significaria — que
o score prioriza justamente quem a regra trivial deixaria por último — vira leitura no texto, não
ajuste no código.

**Divulgação de olhada prévia no dado:** ao redigir este ADR foi calculada a correlação de Spearman
entre as colunas dos baselines e `score_gap_total` na base completa: `pl_brl` −0,268 e
`dias_sem_remessa` +0,123. Isso é propriedade da base de entrada, não resultado do experimento
(nenhum AUC contra `converteu` foi calculado), mas fica registrado porque a direção travada acima
foi escrita depois dessa olhada. A direção veio do racional de negócio e não do sinal da correlação:
a de `pl_brl` é negativa e mesmo assim o baseline segue decrescente, que é como o assessor de fato
ligaria.

**Métrica e intervalo:** AUC-ROC pontual em n = 900, mais **intervalo de confiança de 95% por
bootstrap percentil** (1.000 reamostragens do holdout, seed fixa) para cada competidor **e para as
diferenças** score − baseline. Diferença de AUC sem intervalo em n = 900 é falsa precisão: o próprio
ADR-0007 reportou uma diferença de 0,0146 que provavelmente não sobrevive a um IC. Diferença cujo IC
cruza zero é reportada como **empate estatístico**, nunca como vitória.

**Razão Principal:** hoje a frase "priorização inteligente" no README é alegação sem verificação —
exatamente o tipo de alegação (rigor afirmado, não demonstrado) que motivou a auditoria original do
projeto. Fechar o Gate 1 troca a alegação por um número medido.

"Se não fizermos: o OIS continua sendo o projeto que auditou o erro dos outros e manteve o próprio.
A proposta de valor central segue sem evidência nenhuma, e a primeira pergunta de qualquer
entrevistador técnico ('comparou contra o quê?') não tem resposta."
"Se fizermos: o projeto ganha o único resultado que a tese deixou alcançável — um teste positivo,
medido e publicado, sobre a competência que ele alega ter."

## 3. CONSEQUÊNCIAS

**Positivas:**
- Fecha o gate mais barato e mais óbvio do framework com meia dúzia de linhas em cima de infra que
  já existe (ADR-0007). Custo estimado: uma sessão.
- Responde o item 3 do critério B da tese (o que o assessor faz hoje) **sem** depender de acesso à
  fonte da dor — testa todas as respostas plausíveis em vez de descobrir a verdadeira.
- O baseline aleatório é sanity check da infra inteira: se ele não der AUC ≈ 0,5, há bug no pipeline
  de avaliação, e aí o resultado do ADR-0007 também fica sob suspeita.
- A comparação vira material de portfólio mais forte que a do ADR-0007: mostra domínio do gate que a
  maioria dos projetos de ML pula.

**Negativas:**
- **A assimetria de evidência é grande e precisa estar escrita junto do resultado.** O `converteu`
  simulado foi gerado *a partir* do `score_gap_total` (ADR-0007 §2). Qualquer competidor que não
  seja o score parte em desvantagem estrutural, inclusive estes baselines, pelo mesmo motivo que a
  LogisticRegression perdeu. Logo: **o score vencer prova pouco** (é quase verdade por construção),
  enquanto **o score perder ou empatar seria devastador** e altamente informativo. O experimento é
  forte num sentido só, e o notebook precisa dizer isso com a clareza do aviso do ADR-0007.
- `pl_brl` não é independente do score, é insumo dele. Não existe baseline verdadeiramente externo
  nesta base sintética; o mais externo disponível é o aleatório.
- Risco de má leitura por terceiros ("o OIS bate a regra de mercado") sem o qualificador acima.
  Exige aviso explícito, no nível do ADR-0004, no notebook e no README.
- Não fecha a lacuna de fundo: nenhum destes números diz o que aconteceria com outcome real. O Gate
  1 fechado aqui é o Gate 1 *no mundo simulado declarado*, e é assim que precisa ser enunciado.

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Vantagem | Por quê rejeitada |
|---|---|---|
| Gerar um `converteu` novo, independente do score, pra dar chance justa aos baselines | Elimina a assimetria estrutural | Muda o objeto de estudo no meio do caminho e quebra a comparabilidade com o ADR-0007 (outcome novo, holdout novo, resultado anterior não reaproveitável). Fica registrado como possível ADR-0009, não como parte deste |
| Comparar por precision@k (top 50 da lista) em vez de AUC-ROC | Mais perto do uso real: o assessor liga pros primeiros da lista, não pra base toda | AUC-ROC é a métrica travada no ADR-0007; trocar de métrica no mesmo experimento impede a comparação direta. Candidata a métrica secundária numa iteração posterior, nunca substituta |
| Perguntar de novo pro amigo do mercado qual regra ele usa | Resolveria a dúvida na fonte | Sem acesso à pessoa (tese, Fase 1). Testar todas as regras plausíveis é o contorno, e é mais forte: não depende de uma amostra de n=1 |
| Não fazer nada e manter o reposicionamento de auditoria (ADR-0006) | Custo zero | Deixa a proposta de valor central sem evidência, que é a reincidência exata do erro auditado pelo próprio projeto (critério A da tese) |

## 5. IMPACTO ROI

- **Métrica de sucesso:** a comparação existe, roda de ponta a ponta e reporta AUC-ROC com IC 95%
  bootstrap para os cinco competidores (score heurístico, LogisticRegression, `pl_brl`,
  `dias_sem_remessa`, aleatório) contra o mesmo `converteu` e o mesmo holdout. **Sucesso não é o
  score ganhar.** Sucesso é o número existir e ser publicado como vier.
- **Trava de publicação (escrita antes de rodar, 2026-09-04, confirmada pelo Luiz):** se o score
  perder de qualquer baseline ingênuo, **o resultado é publicado assim mesmo** e a proposta de valor
  do projeto cai junto — o README passa a dizer que a regra trivial ganha. Nenhum parâmetro
  (temperatura do gerador, seed, holdout, direção dos baselines, features) é reajustado depois de
  ver o resultado. Mesma disciplina do ADR-0007, da Fase 4 (K real substituindo os 6 clusters
  narrados) e da Fase 7 (classificador que perdeu e foi publicado perdendo).
- **Timeline:** implementação na sessão seguinte a este ADR. Este documento fecha a decisão, não a
  execução.
- **Risco de regressão:** nenhum no pipeline existente. O trabalho é aditivo dentro de
  `notebooks/OIS_Outcome_Simulado.ipynb`, consome `data/processed/base_offshore_scored.csv` e não
  toca `src/utils.py::calcular_score_ois` (fonte única, ADR-0002) nem a suíte de paridade.

## 6. Critérios de implementação (falsificabilidade)

- **Reuso literal do holdout:** o `df_test` e o vetor `converteu` avaliados são os mesmos objetos
  produzidos pelas células do ADR-0007, no mesmo notebook e na mesma execução. Recalcular o split ou
  regerar o outcome invalida a comparação.
- **Sanity check obrigatório do aleatório:** o baseline aleatório precisa cair em IC 95% que contenha
  0,5. Se não cair, abortar a leitura dos demais números e investigar o pipeline de avaliação antes
  de publicar qualquer coisa.
- **Direção declarada em código:** cada baseline entra em `roc_auc_score` com a direção da tabela do
  §2 escrita e comentada explicitamente, nunca descoberta em runtime por qual sinal dá AUC maior.
- **IC obrigatório em toda diferença reportada:** nenhuma frase do tipo "A supera B por X" sai do
  notebook ou do README sem o IC da diferença ao lado. Se o IC cruza zero, a frase é "empate
  estatístico em n=900".
- **Aviso de assimetria colado no resultado:** a tabela final carrega, na mesma célula, a nota de
  que o outcome foi gerado a partir do score e que isso favorece o score por construção — de modo
  que ninguém leia a tabela sem ler a ressalva.

## 7. LINKS RELACIONADOS

- [ADR-0007](0007-outcome-simulado-para-modelo-supervisionado.md) — infra de outcome simulado, holdout e trava de publicação que este ADR reusa integralmente.
- [ADR-0002](0002-pesos-do-score-sao-heuristica-nao-calibracao.md) — os pesos heurísticos que este experimento coloca à prova contra regra de bolso.
- [ADR-0004](0004-dataset-sintetico-como-premissa-consciente.md) — mesma disciplina de aviso sobre o que dado sintético não prova.
- [ADR-0006](0006-reposicionamento-auditoria-como-produto.md) — reposicionamento que este ADR tenta superar, saindo da auditoria defensiva para um resultado medido.
- `docs/tese/refatoracao-ois-dor-resolvida/TESE.md` (base de conhecimento) — veredito de 2026-09-04 que redefiniu o escopo e originou esta decisão.
- Framework dos Três Gates de Viabilidade (base de conhecimento) — origem do conceito de Gate 1 usado aqui.
