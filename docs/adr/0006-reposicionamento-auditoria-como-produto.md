# ADR-0006: Reposicionamento — auditoria como produto, não scoring como produto

**Data:** 2026-08-29
**Status:** Accepted
**Proposto por:** Luiz

---

## 1. CONTEXTO (O Quê?)

O README apresentava o OIS primeiro como "sistema de priorização de clientes offshore" —
produto de scoring/ML — com a auditoria (ADRs 0001-0005) como rodapé de transparência. Depois
de fechar os 11 tickets do board wayfinder, ficou claro que o resultado visível pro usuário
final (a lista priorizada) **não mudou** com a refatoração — o que mudou foi a capacidade de
provar que essa lista está correta e de que premissas ela depende.

O projeto tem 3 limitações estruturais que um pitch de "sistema de scoring" não sobrevive bem:
1. Base 100% sintética — nunca validado contra outcome real.
2. Clustering (K=2, Silhouette 0,20) morreu — não existe segmentação comportamental entregue.
3. Pesos/thresholds são heurística declarada, não calibração — não há "o modelo aprendeu algo".

Comparado a outros projetos do portfólio (`payflow_inadimplencia`, AUC 0,56 mas com outcome
real via Home Credit Default Risk; `stable-treasury`, hedge cambial sobre caso real da Azul),
o OIS é o único cujo "produto de ML" em si é fraco — mas cujo **processo de auditoria** é o mais
extenso do portfólio: 11 tickets, 5 ADRs, um bug real de produção encontrado e corrigido, uma
correção de deploy auditada por uma segunda camada (PAVC) que achou 3 furos na própria correção
antes do commit.

## 2. DECISÃO (Por Quê?)

Reposicionar o README e a narrativa pública do projeto: liderar com "auditoria de um projeto de
ML que chegou torto — do jeito que se faz em produção real", não com "sistema de scoring
offshore". A engenharia de scoring/clustering vira o *caso de uso que serve de pretexto* pra
mostrar o processo de auditoria, não o entregável principal.

**Razão Principal:** um portfólio de "eu sei treinar modelo/calcular score" compete com todo
candidato pleno-sênior de ML — é o portfólio padrão. Um portfólio de "eu sei auditar um projeto
real, achar bug de produção silencioso, provar que uma alegação de rigor estatístico era falsa,
e fazer isso de forma documentada e datada" é raro — a maioria não expõe publicamente o processo
de encontrar e corrigir os próprios erros.

"Se não fizermos isso: o projeto compete pela métrica errada (qualidade do modelo, que é
mediana) em vez da métrica onde ele é forte (disciplina de engenharia, que é rara e
verificável)."
"Se fizermos: o pitch vira sobre o processo — 11 tickets, 5 ADRs, 1 bug de produção real
achado, 1 alegação estatística falsa corrigida — que é evidência de trabalho sênior
independente da qualidade do modelo em si."

## 3. CONSEQUÊNCIAS

**Positivas:**
- Diferencia o projeto dos outros 3 do portfólio, que competem em "modelo com outcome real".
- Sobrevive melhor a perguntas técnicas de entrevista — o pitch já assume as limitações do
  modelo como parte da história, não como algo a esconder.
- Reaproveita trabalho já feito (os 11 tickets, os 5 ADRs, o artifact de auditoria) sem exigir
  mais código — é reescrita de narrativa, não de sistema.

**Negativas:**
- Exige reescrever a ordem e o tom do README — a estrutura CRISP-DM atual apresenta a auditoria
  como nota de rodapé de cada fase; o reposicionamento pede que ela vire a linha narrativa
  principal.
- Risco de o pitch soar "desculpa disfarçada" se mal executado — precisa deixar claro que
  auditar bem é competência per se, não justificativa para modelo fraco. A diferença está em
  como o texto é escrito, não em nova validação técnica.

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Por quê foi rejeitada |
|-------|----------------------|
| Manter "sistema de scoring" como pitch principal | Compete na métrica onde o projeto é mediano (modelo sem outcome real); desperdiça o trabalho de auditoria, que é o diferencial real. |
| Buscar dataset proxy real para validar o score antes de reposicionar | Escopo maior, sem dado disponível hoje (ver ADR-0004) — vira trabalho futuro, não bloqueia o reposicionamento de narrativa, que é execução imediata. |

## 5. IMPACTO ROI

- **Métrica de sucesso:** README abre com a história de auditoria (bug real, alegação falsa
  corrigida, deploy hardenizado), não com "sistema de priorização de clientes" como primeira
  frase — verificável lendo as 3 primeiras linhas do arquivo.
- **Timeline:** execução imediata (reescrita de texto, sem código novo).
- **Risco de regressão:** nenhum — CRISP-DM completo, ADRs e código seguem intactos; só a
  ordem e o enquadramento da narrativa mudam.

## 6. LINKS RELACIONADOS

- [ADR-0001](0001-k-real-vs-narrativa-de-6-clusters.md) a [ADR-0005](0005-hardening-de-deploy-pos-auditoria.md) — os achados que este reposicionamento coloca em primeiro plano.
- Board wayfinder completo: `docs/wayfinder/offshore_intelligence_system/` na base de conhecimento (11 tickets).
- Artifact de auditoria publicado nesta sessão (2026-08-29), mesmo enquadramento aplicado agora ao README.
