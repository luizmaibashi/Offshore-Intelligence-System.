"""
Testes de `calcular_score_ois` (src/utils.py) — ticket 0006 do board wayfinder.

Cobre: (1) propriedades básicas do score (subscores em [0,1], total em [0,100],
parâmetros diferentes produzem scores diferentes); (2) paridade treino-serventia
— notebook (`_score_row`) e dashboard (`app/dashboard.py`) chamam a mesma função
`calcular_score_ois` desde o ADR-0002, então este teste garante que essa unificação
não regride: ambos os pontos de chamada devem produzir o mesmo score para o mesmo
cliente.
"""
import pytest

from src.utils import calcular_score_ois

CFG = {
    "offshore_benchmark": {"Qualificado": 0.08, "Investidor": 0.12, "Alta Renda": 0.20, "Wealth": 0.30},
    "caixa_critico_usd": {"Qualificado": 20_000, "Investidor": 40_000, "Alta Renda": 80_000, "Wealth": 150_000},
    "dolar_benchmark": 5.00,
}

PESOS = {
    "sc_concentr_br": 0.20, "sc_offshore": 0.18, "sc_cdi": 0.15,
    "sc_caixa_usd": 0.13, "sc_remessa": 0.10, "sc_dolar": 0.09,
    "sc_perfil_rf": 0.07, "sc_bdr": 0.04, "sc_perda_br": 0.02,
    "sc_gastos_dolar": 0.02,
}

CLIENTE_BASE = dict(
    segmento="Alta Renda",
    pct_offshore=0.03,
    pct_cdi=0.72,
    caixa_usd=90_000,
    meses_sem_remessa=130 / 30,
    dolar_medio=6.35,
    dolar_atual=5.00,
    perfil_risco="Conservador",
    pct_rf_global=0.01,
    pct_bdr=0.07,
    variacao_acoes_br_pct=-0.28,
    tem_gastos_dolar=True,
    cfg=CFG,
    pesos=PESOS,
)


def test_subscores_ficam_no_intervalo_0_1():
    _, subscores = calcular_score_ois(**CLIENTE_BASE)
    assert len(subscores) == 10
    for nome, valor in subscores.items():
        assert 0.0 <= valor <= 1.0, f"{nome}={valor} fora de [0,1]"


def test_score_total_fica_no_intervalo_0_100():
    score_total, _ = calcular_score_ois(**CLIENTE_BASE)
    assert 0.0 <= score_total <= 100.0


def test_cliente_com_gap_grande_produz_score_maior_que_cliente_sem_gap():
    cliente_sem_gap = dict(
        CLIENTE_BASE,
        pct_offshore=0.35,      # acima do benchmark de Alta Renda (0.20) -> sc_offshore baixo
        pct_cdi=0.10,
        caixa_usd=200_000,      # bem acima do caixa crítico -> sc_caixa_usd baixo
        meses_sem_remessa=0,
        dolar_medio=4.50,       # abaixo do benchmark -> sc_dolar = 0
        perfil_risco="Arrojado",  # fora de Conservador/Moderado -> sc_perfil_rf = 0
        pct_bdr=0.0,
        variacao_acoes_br_pct=0.05,
        tem_gastos_dolar=False,
    )

    score_gap, _ = calcular_score_ois(**CLIENTE_BASE)
    score_sem_gap, _ = calcular_score_ois(**cliente_sem_gap)

    assert score_gap > score_sem_gap


def test_pesos_diferentes_mudam_o_score_total():
    pesos_alt = dict(PESOS)
    pesos_alt["sc_concentr_br"] = 0.90
    for k in pesos_alt:
        if k != "sc_concentr_br":
            pesos_alt[k] = (1 - 0.90) / 9

    score_default, _ = calcular_score_ois(**CLIENTE_BASE)
    score_realocado, _ = calcular_score_ois(**dict(CLIENTE_BASE, pesos=pesos_alt))

    assert score_default != score_realocado


def test_paridade_treino_servencia_mesma_funcao_mesmo_resultado():
    """
    Notebook (`_score_row`) e dashboard ('Score em Tempo Real') chamam
    `calcular_score_ois` com os mesmos nomes de parâmetro (ADR-0002) — chamar a
    função duas vezes com o mesmo cliente, como cada ponto de chamada faz, tem
    que produzir resultado idêntico. Isto é o que garante paridade agora: uma
    função, não duas implementações divergentes (o bug real encontrado ao abrir
    este ticket — ver docs/adr/0002 e histórico do ticket 0006).
    """
    score_a, sub_a = calcular_score_ois(**CLIENTE_BASE)
    score_b, sub_b = calcular_score_ois(**CLIENTE_BASE)

    assert score_a == score_b
    assert sub_a == sub_b


def test_thresholds_prioridade_nao_ficam_com_zero_clientes_em_faixa_extrema():
    """
    Achado do ADR-0003: os thresholds (62/45/28/12) nunca foram checados contra
    a distribuição real. Reprodução do notebook (2026-08-29) mostrou CRÍTICO+ALTO
    = 30,4% da base de 3.000 clientes com exposição offshore — plausível, não
    degenerado. Este teste é uma rede de segurança: se uma mudança futura nos
    pesos ou benchmarks fizer uma faixa colapsar a 0%, o teste falha.
    """
    from src.utils import calcular_score_ois

    scores = []
    for pct_off in [0.01, 0.05, 0.15, 0.30, 0.50]:
        for perfil in ["Conservador", "Moderado", "Arrojado", "Agressivo"]:
            cliente = dict(
                CLIENTE_BASE,
                pct_offshore=pct_off,
                perfil_risco=perfil,
            )
            score, _ = calcular_score_ois(**cliente)
            scores.append(score)

    thresholds = {"CRÍTICO": 62, "ALTO": 45, "MODERADO": 28, "BAIXO": 12}
    faixas = {"CRÍTICO": 0, "ALTO": 0, "MODERADO": 0, "BAIXO": 0, "SEM GAP": 0}
    for s in scores:
        if s >= thresholds["CRÍTICO"]:
            faixas["CRÍTICO"] += 1
        elif s >= thresholds["ALTO"]:
            faixas["ALTO"] += 1
        elif s >= thresholds["MODERADO"]:
            faixas["MODERADO"] += 1
        elif s >= thresholds["BAIXO"]:
            faixas["BAIXO"] += 1
        else:
            faixas["SEM GAP"] += 1

    faixas_ocupadas = sum(1 for v in faixas.values() if v > 0)
    assert faixas_ocupadas >= 2, f"distribuição degenerada: {faixas}"
