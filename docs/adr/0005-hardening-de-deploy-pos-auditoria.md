# ADR-0005: Hardening de deploy pós-auditoria (ticket 0011)

**Data:** 2026-08-29
**Status:** Accepted
**Proposto por:** Luiz

---

## 1. CONTEXTO (O Quê?)

Auditoria de Docker/compose/setup.py ([ticket 0011](../../../../docs/wayfinder/offshore_intelligence_system/0011-auditoria-de-deploy.md) na base de conhecimento) encontrou 4 gaps reais no
deploy do OIS, mesma classe de problema que o `shadow_fx_terminal` já corrigiu no seu próprio
deploy (CORS aberto, auth fail-open):

1. `Dockerfile` roda como root — sem instrução `USER`.
2. Base image pinada só por tag solta (`python:3.11-slim`), não por digest.
3. Sem `.dockerignore` — `COPY . .` copia `.git/`, `notebooks/`, `data/raw/` pra dentro da imagem.
4. `app/dashboard.py` sem autenticação — acesso livre por padrão, nunca declarado como
   intencional.

O OIS não tem API própria (só Streamlit containerizado) — superfície de risco menor que o
shadow_fx, mas real: ambiente que roda como root em produção, imagem que carrega arquivo
desnecessário (incluindo `.git/` com histórico completo), e dashboard sem controle de acesso.

## 2. DECISÃO (Por Quê?)

Corrigir os 4 gaps antes de qualquer deploy público do OIS.

**Razão Principal:** container root + imagem sem `.dockerignore` é o mesmo padrão de risco que
motivou a correção do shadow_fx — a diferença de superfície (sem API REST) não elimina o risco,
só reduz o vetor de ataque direto.

"Se não fizermos isso: container roda com privilégio desnecessário, imagem carrega `.git/`
completo (útil pra reconhecimento de atacante), dashboard fica exposto sem controle de quem
acessa."
"Se fizermos: container roda com usuário não-privilegiado, imagem só tem o necessário, digest
pinado elimina supply-chain drift silencioso, dashboard tem autenticação básica ou está
declarado explicitamente como uso interno sem necessidade dela."

## 3. CONSEQUÊNCIAS

**Positivas:**
- Container sem privilégio root reduz blast radius de um escape de container.
- `.dockerignore` reduz superfície de imagem e tempo de build.
- Pin por digest elimina risco de a tag `python:3.11-slim` apontar pra imagem diferente no
  próximo build (mesma classe de proteção que ticket 0007 deu ao sklearn).
- Autenticação (ou declaração explícita de dashboard interno) fecha o gap mais visível.

**Negativas:**
- `USER` não-root exige checar permissão de escrita em `data/processed/` dentro do container
  (Streamlit **escreve** lista priorizada em runtime, não só lê) — pode exigir ajuste de
  `chown` no Dockerfile, e falha se houver volume do host montado com dono diferente do
  usuário do container (achado em auditoria PAVC — testar `docker run` com volume montado,
  não só sem volume).
- Pin por digest exige processo manual de atualização (digest não sobe sozinho com `docker
  pull`) — mesmo trade-off do ticket 0007 com sklearn.
- Autenticação no Streamlit exige decidir mecanismo (variável de ambiente com senha simples?
  `streamlit-authenticator`? OAuth?) — decisão de escopo separada, não travar o resto do
  hardening por causa dela.

## 4. ALTERNATIVAS DESCARTADAS

| Opção | Por quê foi rejeitada |
|-------|----------------------|
| Deixar como está (aceitar risco) | Mesma classe de gap que já causou correção real no shadow_fx — ignorar um achado repetido de auditoria não é postura defensável em portfólio que se vende pela honestidade de engenharia. |
| Adicionar API REST com auth completa (JWT etc.) | Escopo maior que o problema — OIS não tem API própria hoje; resolver autenticação do dashboard não exige criar uma API nova. |

## 5. IMPACTO ROI

- **Métrica de sucesso:** `Dockerfile` tem `USER` não-root, imagem base pinada por
  `@sha256:...`, `.dockerignore` existe e exclui `.git/`/`notebooks/`/`data/raw/`,
  `app/dashboard.py` tem autenticação básica ou comentário explícito declarando acesso livre
  como decisão intencional.
- **Timeline:** antes de qualquer deploy público/demo do OIS (Streamlit Cloud ou equivalente).
- **Risco de regressão:** `USER` não-root pode quebrar escrita em `data/processed/`/`models/`
  se permissão não for ajustada — testar `docker build` + `docker run` completo antes de
  considerar fechado.

## 6. LINKS RELACIONADOS

- [Ticket 0011 — auditoria de deploy](../../../../docs/wayfinder/offshore_intelligence_system/0011-auditoria-de-deploy.md) (base de conhecimento)
- [ADR-0007 — pin de dependências sklearn](../../../../docs/wayfinder/offshore_intelligence_system/0007-pin-dependencias.md) — mesmo padrão de risco (drift silencioso), aplicado a imagem
  base em vez de dependência Python.
- Comparável: `shadow_fx_terminal` — correção de CORS aberto e auth fail-open em `src/api.py`.
