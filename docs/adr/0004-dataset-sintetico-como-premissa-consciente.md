# ADR-0004: Dataset sintético log-normal como premissa consciente, não achado a esconder

**Data**: 2026-08-29
**Status**: Accepted
**Proposto por**: Luiz Maibashi (com Claude Code, refatoração de honestidade estatística)
**Contexto**: `offshore_intelligence_system` — geração da base de clientes (`notebooks/OIS_Project.ipynb` §2.1)

---

## 1. Contexto (o quê?)

O projeto nunca teve acesso a uma base real de clientes de wealth management (dado sensível,
protegido por sigilo bancário/LGPD). Toda a base de 40k clientes (e ~3.000 com exposição offshore)
é gerada sinteticamente via `numpy.random.Generator`:

- **Patrimônio Líquido**: `rng.lognormal(mu, sigma)` clipado por segmento — justificado no
  notebook como aderente à Lei de Pareto (riqueza é log-normal na cauda).
- **Percentuais de alocação** (offshore, CDI, caixa USD): `rng.normal()` truncado, com médias
  condicionadas a segmento e perfil de risco.
- **Correlações**: injetadas manualmente (ex.: mais offshore → menos CDI), não aprendidas de dado
  real.

O notebook já registra essa premissa em texto ("Como não temos acesso à uma base real de empresa,
geramos dados sintéticos calibrados com...") — mas nunca foi formalizada como decisão arquitetural
registrada, no mesmo sentido que o `shadow_fx_terminal` fez em sua seção "Transparência de dado".

**Restrições técnicas:**
- Sem outcome real, os subscores individuais (ADR-0002) e os thresholds (ADR-0003) não podem ser
  validados contra comportamento observado — todas as métricas de "qualidade" do projeto (ANOVA,
  t-test, Silhouette do ADR-0001) medem propriedades da geração sintética, não do mercado real.
- Toda correlação "realista" reportada no EDA (ex.: "mais offshore → menos CDI") é circular: foi
  injetada na geração, então a EDA "descobre" o que o próprio gerador definiu.

**Dependências afetadas:**
- Todo o projeto — base sintética é o dado de entrada único, não só desta seção.
- README, resumo do notebook, qualquer claim de "insight de mercado" derivado da EDA.

---

## 2. Decisão (por quê?)

**O que escolhemos:** manter o dataset sintético como está (é a única opção viável sem acesso a
dado real de wealth management), mas formalizar como ADR a mesma premissa que o texto já
menciona informalmente — e adicionar a ressalva explícita de que EDA sobre dado sintético
autogerado não é "insight de mercado descoberto", é verificação de que o gerador fez o que foi
programado para fazer.

**Razão principal:**

"Um leitor técnico que vir 'correlação realista: mais offshore → menos CDI' como insight de EDA
pode achar que o projeto descobriu um padrão de mercado. Na verdade essa correlação foi escrita à
mão na função geradora — a EDA só confirma que o gerador funciona. Não registrar isso como ADR
deixa a ambiguidade aberta, e é o tipo de furo que um entrevistador técnico exploraria."

"Formalizando: o projeto ganha uma seção clara — 'isto é dado sintético, aqui está o porquê, e
aqui está o que isso significa para toda métrica reportada depois' — sem precisar reescrever cada
claim individualmente."

---

## 3. Consequências

**Positivas:**
- Fecha a ambiguidade entre "insight de EDA" e "propriedade injetada na geração" de uma vez, para
  todo o projeto — não precisa repetir a ressalva em cada gráfico.
- Alinha `offshore_intelligence_system` ao mesmo padrão de honestidade que `shadow_fx_terminal`
  já usa para seu próprio dado sintético.
- Justifica, num único lugar, por que ANOVA/t-test/Silhouette (ADR-0001) medem a geração, não o
  mercado — reduz risco de alguém usar esses números como prova de mercado real no pitch.

**Negativas / débito incorrido:**
- Nenhum — este ADR só formaliza o que já era verdade e parcialmente dito no texto.

**Timeline:**
- Implementação: mesma sessão, ADR + eventual link cruzado no README.

---

## 4. Alternativas descartadas

| Opção | Vantagem | Por quê rejeitada |
|-------|----------|------------------|
| Buscar dataset público substituto (ex: dados de patrimônio de pesquisas divulgadas) | Reduziria a circularidade EDA↔geração | Fora de escopo — não existe dataset público equivalente a carteira de wealth management por cliente; a alternativa realista é sintético ou nada |
| Não formalizar (deixar só a menção informal no texto) | Zero esforço | ❌ Ambiguidade sobre "insight vs. propriedade injetada" fica sem registro explícito, mesmo padrão de risco do ADR-0001/0002/0003 |

---

## 5. Impacto e validação

**Métrica de sucesso:** README e resumo do notebook deixam explícito, perto de qualquer claim de
"correlação" ou "insight" da EDA, que a base é sintética e as correlações reportadas foram
injetadas na geração — não descobertas.

**Como verificar:** leitura do README/notebook por alguém sem contexto do projeto — a pessoa deve
concluir corretamente que nenhum número é de mercado real.

---

## 6. Referências

- `notebooks/OIS_Project.ipynb` §2.1 "Geração da Base Sintética"
- [0001](0001-k-real-vs-narrativa-de-6-clusters.md), [0002](0002-pesos-do-score-sao-heuristica-nao-calibracao.md), [0003](0003-thresholds-de-faixa-sao-cortes-arbitrarios.md) — todas as métricas afetadas por esta premissa
- Comparável a: `shadow_fx_terminal` seção "Transparência de dado" (mesmo padrão de honestidade sobre dado sintético)
- Ticket 0005 do board wayfinder (`docs/wayfinder/offshore_intelligence_system/`)
