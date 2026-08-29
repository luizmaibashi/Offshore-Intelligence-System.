# SPEC_FINAL: Hardening de deploy do OIS

**Origem:** consolidação do board wayfinder (`docs/wayfinder/offshore_intelligence_system/`,
11 tickets, todos fechados). **Escopo desta spec:** só os 4 gaps de deploy do ticket 0011 —
os outros 10 tickets já foram executados e commitados (README, testes, ADRs 0001-0004,
pin de sklearn/joblib). Ver [ADR-0005](adr/0005-hardening-de-deploy-pos-auditoria.md) para
contexto/decisão completos.

**Critério de pronto:** `docker build` + `docker run` funcionam de ponta a ponta com os 4 itens
corrigidos, sem regressão de escrita em `data/processed/`/`models/`.

---

## 1. Dockerfile — usuário não-root

**Achado:** container roda como root (sem `USER`).

**Mudança:**
```dockerfile
# depois do RUN pip install -e .
RUN useradd --create-home --shell /bin/bash oisuser \
    && chown -R oisuser:oisuser /app
USER oisuser
```

**Cuidado (confirmado em auditoria PAVC 2026-08-29):** `app/dashboard.py` **escreve** em
runtime — não só lê `data/processed/*.csv` existente, gera simulação de score novo e regrava.
`chown -R` no build cobre o caso sem volume montado, mas **se o container rodar com volume do
host montado em `data/processed/`** (ex.: `docker-compose.yml` comentário de exemplo, linhas
13-16), o dono do arquivo no host pode não bater com `oisuser` do container — escrita falha em
runtime, não em build, e pode falhar silenciosamente dependendo de como o Streamlit trata a
exceção. Teste obrigatório antes de fechar este item: `docker run` **com** volume montado
(não só sem volume), confirmando que o dashboard consegue escrever
`lista_prioritaria_assessor.csv` sem erro de permissão.

## 2. Dockerfile — pin de imagem base por digest

**Achado:** `FROM python:3.11-slim` é tag solta, pode apontar pra imagem diferente entre builds.

**Mudança:**
```bash
# Obter o digest atual (uma vez, documentar a data)
docker pull python:3.11-slim
docker inspect --format='{{index .RepoDigests 0}}' python:3.11-slim
```
```dockerfile
FROM python:3.11-slim@sha256:<digest-obtido>
```

**Trade-off aceito (mesmo do ADR-0007/sklearn):** digest não atualiza sozinho — processo manual
de revisão periódica, não automação. Documentar a data do pin num comentário acima do `FROM`.

**Gatilho de reavaliação (achado em auditoria PAVC 2026-08-29 — sem isso o pin vira "regra
herdada sem revalidar motivo", mesmo padrão do débito #3 do shadow_fx):** revisar o digest a
cada 6 meses (mesmo ciclo do `models/*.pkl`, ver README § Monitoramento de drift) OU
imediatamente se houver CVE alta/crítica divulgada pra imagem `python:3.11-slim` — checar
[Docker Hub security scan](https://hub.docker.com/_/python) ou Dependabot se ativado no repo.

## 3. `.dockerignore` — FALSO POSITIVO, já existia

**Correção 2026-08-29 (achado ao executar a spec):** o achado original do ticket 0011 estava
errado. `.dockerignore` já existe no repo desde o commit `00b8da2` (dockerização original) e já
cobre `.git/`, `notebooks/`, `images/`, `reports/`, `.venv/`, `__pycache__/`. O comando de
auditoria original (`cat .dockerignore 2>/dev/null; echo ---; cat .gitignore`) teve o output do
`.dockerignore` confundido com o do `.gitignore` — erro de leitura na investigação, não gap no
código.

**Ação:** nenhuma. Item fechado sem mudança — registrado aqui pra não reabrir por engano numa
próxima auditoria.

## 4. `app/dashboard.py` — declarar acesso livre como decisão consciente

**Achado:** Streamlit sem autenticação, nunca declarado como intencional.

**Decidido 2026-08-29:** manter acesso livre — é portfólio/demo, não produção com dado real de
cliente. Declarar explicitamente em vez de deixar implícito.

**Mudança:**
1. Comentário no topo de `app/dashboard.py`:
   ```python
   # Dashboard sem autenticação por decisão consciente — projeto de portfólio/demo,
   # base 100% sintética (ADR-0004), não produção com dado real de cliente.
   ```
2. Adicionar linha em README § "O que este projeto assume abertamente":
   ```
   - **O dashboard não tem autenticação.** Decisão consciente — projeto de portfólio/demo
     sobre base sintética, não produção com dado real de cliente.
   ```

**Não fazer:** construir API REST com JWT ou autenticação — escopo maior que o problema (ver
ADR-0005 §4, alternativa descartada).

---

## Ordem de execução recomendada

1. Item 3 (`.dockerignore`) primeiro — mudança isolada, sem risco de quebrar build.
2. Item 2 (pin por digest) — mudança isolada, só troca uma linha.
3. Item 1 (`USER` não-root) — testar build+run completo depois, é o item com maior chance de
   regressão de permissão.
4. Item 4 (autenticação) — decisão do Luiz primeiro (a ou b), depois execução.

Cada item testado com `docker build . && docker run -p 8501:8501 <imagem>` antes de passar pro
próximo, pra isolar qual mudança quebrou algo se algo quebrar.

---

## Execução (2026-08-29)

**Status: todos os 4 itens fechados, build+run testados.**

- **Item 3 (`.dockerignore`):** falso positivo — já existia desde o commit original de
  dockerização. Achado do ticket 0011 veio de erro de leitura na auditoria (output do
  `.dockerignore` confundido com `.gitignore`). Nenhuma mudança feita.
- **Item 2 (pin por digest):** aplicado —
  `python:3.11-slim@sha256:1042b61448fef4ba92d16a8c7eb4996d027568ce64792a7877fd88511e0af7c6`
  (Debian 13/trixie). **Achado ao testar:** o digest atual já não tem
  `software-properties-common` no repo default do trixie, e o pacote não era usado por nenhum
  script do repo (nenhum `add-apt-repository`) — removido do Dockerfile. Prova viva do risco
  documentado no ADR-0005: imagem base muda sob o mesmo nome de tag.
- **Item 1 (`USER` não-root):** aplicado — `useradd oisuser` + `chown -R` + `USER oisuser`.
  Testado `docker run` **sem** volume (health check OK) e **com** volume montado no host
  (`data/` bind mount) simulando a escrita real do dashboard: `WRITE_OK`. Docker Desktop no
  Windows/WSL2 monta bind mounts com `rwxrwxrwx`, então a escrita passou sem `chown` extra no
  volume — em Linux nativo (deploy fora de Windows/WSL2) esse comportamento pode diferir;
  registrado como risco residual, não testado nesse ambiente.
- **Item 4 (declarar acesso livre):** aplicado — comentário em `app/dashboard.py` (docstring) +
  linha nova em README § "O que este projeto assume abertamente", ambos linkando ADR-0005.
  **Achado extra ao executar:** "NEXUM" ainda aparecia na UI visível do dashboard (`st.caption`
  na sidebar, título de um gráfico Plotly) — resíduo que o grep da decisão 0010 não pegou
  porque rodou só no README. Removido nos dois pontos. Ainda sobra "NEXUM" em
  `REPRODUCIBILITY.md`, `docs/crisp_dm_checklist.md` e `notebooks/OIS_Project.ipynb` — fora do
  escopo desta spec (deploy, não narrativa), registrado como pendência separada.
