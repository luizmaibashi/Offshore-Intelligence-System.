# ADR-0002: Pesos do score são heurística consciente, não calibração estatística

**Data**: 2026-08-29
**Status**: Accepted
**Proposto por**: Luiz Maibashi (com Claude Code, refatoração de honestidade estatística)
**Contexto**: `offshore_intelligence_system` — motor de score (`src/utils.py`, `config_sistema_ois.json`)

---

## 1. Contexto (o quê?)

Os 10 pesos do score heurístico (`sc_concentr_br=20%`, `sc_offshore=18%`, `sc_cdi=15%`,
`sc_caixa_usd=13%`, `sc_remessa=10%`, `sc_dolar=9%`, `sc_perfil_rf=7%`, `sc_bdr=4%`,
`sc_perda_br=2%`, `sc_gastos_dolar=2%`) nunca tiveram uma decisão arquitetural registrada.

O notebook (`OIS_Project.ipynb`, célula "FASE 1: CRITÉRIOS DE GAP E PESOS") rotula a seção como
**"Economist-Driven"** e o resumo final do notebook descreve o score como "Índice ponderado 0–100
calibrado por economista sênior". Ao investigar o código para escrever este ADR, não encontrei
nenhuma célula de grid search, otimização, validação cruzada ou comparação com dado real por trás
desses números — só um dict Python com peso e "racional" textual por critério (ex: `sc_concentr_br`:
"Risco fiscal/político elevado. Carteiras >85% BR têm risco sistêmico não compensado."). O próprio
notebook lista **"Otimização Bayesiana de pesos e thresholds com dados reais"** como trabalho de
longo prazo (9–18 meses), confirmando que a calibração formal nunca foi feita.

Luiz confirmou (2026-08-29): os pesos são julgamento de negócio dele mesmo, sem processo de
calibração estatística. Não existe "economista sênior" — é framing narrativo do papel que o
projeto assume.

**Restrições técnicas:**
- Base de clientes é sintética (log-normal, sem outcome real de negócio) — não há como calibrar
  pesos contra conversão/receita observada, só contra intuição.
- `assert abs(sum(PESOS.values()) - 1.0) < 0.001` garante soma = 100%, mas isso é validação de
  forma, não de conteúdo.

**Dependências afetadas:**
- `config_sistema_ois.json` (`pesos_criterios`)
- `src/utils.py::calcular_score_ois` (consome `pesos` como parâmetro)
- `README.md`, resumo do notebook (narrativa "calibrado por economista sênior" a corrigir)

---

## 2. Decisão (por quê?)

**O que escolhemos:** manter os pesos como estão (não há erro técnico neles — são uma hipótese de
negócio razoável, com racional explícito por critério), mas documentar e comunicar como **heurística
consciente**, não como resultado de calibração. Remover a alegação "calibrado por economista
sênior" de onde aparecer.

**Razão principal:**

"Se mantivéssemos a narrativa de calibração: o projeto afirma um rigor estatístico que o código
nunca produziu — mesmo padrão de furo do ADR-0001 (K=6 fictício). Um peso de 20% para
`sc_concentr_br` contra 2% para `sc_gastos_dolar` parece resultado de otimização, mas é escolha de
quem escreveu o notebook. Isso é aceitável como hipótese de produto, mas não pode ser vendido como
validado."

"Registrando como heurística: o projeto ganha honestidade sem perder a estrutura — os pesos
continuam usáveis, o racional de negócio por trás de cada um continua documentado (é bom material
de storytelling pro entrevistador), só a alegação de calibração estatística sai do texto."

---

## 3. Consequências

**Positivas:**
- Remove uma alegação de rigor que não sobrevive a uma pergunta técnica direta ("como vocês
  validaram esses pesos?").
- O racional de negócio por critério (já escrito no notebook) continua sendo o argumento de venda
  — só reposicionado como hipótese fundamentada, não como calibração.
- Abre caminho explícito para o próximo passo real: otimização com dado de conversão observado
  (já listado como longo prazo no roadmap do notebook).

**Negativas / débito incorrido:**
- Sem calibração real, não há garantia de que a ordem de prioridade dos critérios reflete o que
  de fato move conversão do assessor. Isso é um limite conhecido do projeto, não deste ADR.
- README e resumo do notebook precisam de edição pontual para remover "economista sênior" e
  "calibrado".

**Timeline:**
- Implementação (correção de texto): mesma sessão.
- Sem impacto em código executável — os pesos numéricos não mudam, só a alegação sobre sua origem.

---

## 4. Alternativas descartadas

| Opção | Vantagem | Por quê rejeitada |
|-------|----------|------------------|
| Rodar otimização Bayesiana agora para "validar de verdade" | Resolveria o problema pela raiz | Fora de escopo desta rodada — exige dado de conversão real (outcome observado), que o projeto não tem (base é sintética). Fica registrado como próximo passo de longo prazo. |
| Manter a narrativa "calibrado por economista sênior" | Zero esforço, texto mais vistoso | ❌ Mesma classe de furo do K=6: alegação que não resiste a verificação |
| Remover os racionais de negócio junto (deixar só números) | Simplifica o texto | Rejeitada — o racional por critério é o valor real do trabalho (hipótese de negócio fundamentada); só a palavra "calibrado" é o problema |

---

## 5. Impacto e validação

**Métrica de sucesso:** nenhum texto do projeto (README, notebook, dashboard) descreve os pesos
como "calibrados" ou atribui a um "economista sênior" sem essa alegação estar marcada como
narrativa de papel, não como processo real.

**Como verificar:** grep por `economista sênior|calibrado` em `README.md` e nas células markdown
do notebook — resultado deve ou não existir, ou vir acompanhado de ressalva ("hipótese, não
validação estatística").

**Cenário de regressão:** se no futuro uma otimização real for feita (dado de conversão
disponível), este ADR fica superseded por um novo registrando o método e o resultado.

---

## 6. Referências

- `notebooks/OIS_Project.ipynb` — célula "FASE 1: CRITÉRIOS DE GAP E PESOS (Economist-Driven)"
- `config_sistema_ois.json::pesos_criterios`
- [0001](0001-k-real-vs-narrativa-de-6-clusters.md) — mesmo padrão de correção narrativa
- Ticket 0005 do board wayfinder (`docs/wayfinder/offshore_intelligence_system/`)
