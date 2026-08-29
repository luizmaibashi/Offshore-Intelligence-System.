# ADR-0003: Thresholds de faixa (62/45/28/12) são cortes arbitrários, não percentis calculados

**Data**: 2026-08-29
**Status**: Accepted
**Proposto por**: Luiz Maibashi (com Claude Code, refatoração de honestidade estatística)
**Contexto**: `offshore_intelligence_system` — classificação de prioridade (`classificar_prioridade()`)

---

## 1. Contexto (o quê?)

`classificar_prioridade()` corta o `score_gap_total` (0–100) em 5 faixas com valores hardcoded:

```python
def classificar_prioridade(score):
    if   score >= 62:  return 'CRÍTICO'
    elif score >= 45:  return 'ALTO'
    elif score >= 28:  return 'MODERADO'
    elif score >= 12:  return 'BAIXO'
    else:              return 'SEM GAP'
```

Ao investigar o código para escrever este ADR, procurei por `.quantile()` ou `.describe()` sobre
`score_gap_total` que justificasse esses 4 cortes como percentis da distribuição sintética — não
encontrei nenhuma célula fazendo esse cálculo. Os números (62, 45, 28, 12) aparecem direto como
constantes, sem célula intermediária de análise de distribuição.

Luiz confirmou (2026-08-29): não houve cálculo de percentil por trás desses cortes — são valores
escolhidos por sensação de faixa razoável, mesma natureza dos pesos do [ADR-0002](0002-pesos-do-score-sao-heuristica-nao-calibracao.md).

**Restrições técnicas:**
- Sem outcome real (conversão/receita por cliente), não há como validar se "CRÍTICO ≥ 62" de fato
  corresponde a um grupo com comportamento distinto — é só um corte no score, que por sua vez já é
  heurístico (ADR-0002).
- Os cortes não são derivados da distribuição observada de `score_gap_total` na base de 40k
  clientes sintéticos — poderiam concentrar 90% dos clientes numa faixa ou 5%, dependendo de como
  a distribuição do score realmente se forma. Isso não foi checado.

**Dependências afetadas:**
- `config_sistema_ois.json::thresholds_prioridade`
- `app/dashboard.py` (cores/badges de prioridade)
- Qualquer relatório ou ranking que ordene clientes por faixa

---

## 2. Decisão (por quê?)

**O que escolhemos:** manter os 4 cortes como estão (não há evidência de que estejam "errados"),
mas documentar como corte arbitrário — não como percentil calculado — e registrar como débito a
verificação de quantos clientes caem em cada faixa na base atual.

**Razão principal:**

"Se a documentação insinuar (ou o texto de venda assumir) que os cortes vêm de análise de
distribuição, é o mesmo furo do ADR-0001 e ADR-0002: alegação de rigor que o código não sustenta.
Sem saber a distribuição real do score, os cortes podem estar desbalanceados (ex.: 80% dos
clientes caindo em 'MODERADO', tornando a faixa inútil para priorização) e ninguém percebeu porque
nunca foi olhado."

"Registrando como arbitrário: fica claro que este é um ponto de melhoria concreto e barato —
rodar `df['score_gap_total'].describe()` e `.value_counts()` sobre `prioridade` já responde se os
cortes fazem sentido prático, sem precisar de dado real."

---

## 3. Consequências

**Positivas:**
- Documentação para de alegar precisão que não existe.
- Identifica um débito barato e concreto (checar `value_counts()` de prioridade) que pode virar
  o próximo ticket, em vez de ficar escondido atrás da falsa aparência de rigor.

**Negativas / débito incorrido:**
- Sem saber a distribuição real, não dá para afirmar se os cortes atuais são úteis ou
  desbalanceados — fica registrado como incerteza, não resolvido aqui.
- README/dashboard não descrevem essa incerteza hoje.

**Timeline:**
- Implementação (este ADR + correção de texto): mesma sessão.
- Verificação de `value_counts()` por faixa: próximo passo, não incluído neste ADR.

---

## 4. Alternativas descartadas

| Opção | Vantagem | Por quê rejeitada |
|-------|----------|------------------|
| Recalcular cortes agora com percentis reais (`quantile(0.75/0.5/0.25)`) | Corrigiria de vez | Fora de escopo deste ticket (é sobre documentar a decisão existente, não sobre re-otimizar); fica como próximo passo natural, já que é barato |
| Deixar sem ADR, já que "não é bug" | Zero esforço | ❌ Decisão sem registro é decisão invisível — próxima pessoa (ou o Luiz em 6 meses) não sabe se os cortes têm base estatística ou não |

---

## 5. Impacto e validação

**Métrica de sucesso:** README/dashboard não afirmam que os 4 cortes vêm de análise de percentil.

**Como verificar:** grep por "percentil" ou "quartil" perto da explicação de `thresholds_prioridade`
no README — não deve haver essa alegação sem ressalva.

**Próximo passo sugerido (fora deste ADR):** rodar `df.groupby('prioridade').size()` na base
sintética atual e decidir se os cortes precisam de ajuste para distribuição mais útil (ex.:
CRÍTICO não deveria ser >30% da base, senão perde função de priorização).

---

## 6. Referências

- `notebooks/OIS_Project.ipynb` — `classificar_prioridade()`
- `config_sistema_ois.json::thresholds_prioridade`
- [0002](0002-pesos-do-score-sao-heuristica-nao-calibracao.md) — mesma natureza de decisão (heurística de negócio, não estatística)
- Ticket 0005 do board wayfinder (`docs/wayfinder/offshore_intelligence_system/`)
