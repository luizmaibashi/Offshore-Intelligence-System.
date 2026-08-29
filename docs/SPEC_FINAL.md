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

## 3. `.dockerignore` — criar do zero

**Achado:** não existe. `COPY . .` copia `.git/`, `notebooks/`, `data/raw/`, `reports/` pra
dentro da imagem.

**Mudança:** criar `.dockerignore` na raiz do repo:
```
.git
.gitignore
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
.streamlit/
notebooks/
reports/
images/
docs/
brain/
*.md
!README.md
```

**Cuidado:** `notebooks/OIS_Project.ipynb` gera os `.pkl` em `models/` — confirmar que os
modelos serializados já commitados são suficientes pro container rodar sem precisar do notebook
dentro da imagem (o Dockerfile roda só o dashboard, não o notebook — checar `ENTRYPOINT`).

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
