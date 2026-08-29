"""
app/utils.py
----------------
Offshore Intelligence System (OIS) — Central de Processamento
Centraliza a lógica de negócios e heurísticas para garantir paridade treino-serventia.
"""

def calcular_score_ois(
    segmento: str,
    pct_offshore: float,
    pct_cdi: float,
    caixa_usd: float,
    meses_sem_remessa: int,
    dolar_medio: float,
    dolar_atual: float,
    perfil_risco: str,
    pct_rf_global: float,
    pct_bdr: float,
    variacao_acoes_br_pct: float,
    tem_gastos_dolar: bool,
    cfg: dict,
    pesos: dict,
) -> tuple[float, dict]:
    """
    Calcula o Score GAP Total e os subscores heurísticos de um cliente.

    Fórmulas idênticas às células `score_*` de `notebooks/OIS_Project.ipynb`
    (ADR-0002) — função única para garantir paridade treino-serventia entre
    notebook e dashboard (ver ADR de testes automatizados, ticket 0006).

    Args:
        segmento: Segmento do cliente (e.g., "Qualificado").
        pct_offshore: Porcentagem do portfólio alocada em Offshore (0.0-1.0).
        pct_cdi: Porcentagem do portfólio em CDI/Renda Fixa BR (0.0-1.0).
        caixa_usd: Valor em caixa na conta internacional (USD).
        meses_sem_remessa: Quantidade de meses sem enviar remessa.
        dolar_medio: Preço médio do dólar adquirido pelo cliente.
        dolar_atual: Dólar de referência atual (benchmark).
        perfil_risco: Perfil de risco declarado (e.g., "Conservador").
        pct_rf_global: Porcentagem em Renda Fixa Global (bonds/T-Bills).
        pct_bdr: Porcentagem do portfólio em BDR/Feeder Funds.
        variacao_acoes_br_pct: Variação % da carteira de ações BR no período.
        tem_gastos_dolar: Se o cliente tem gastos recorrentes em dólar.
        cfg: Dicionário de configurações gerais.
        pesos: Dicionário com os pesos de cada critério.

    Returns:
        Uma tupla contendo (score_total, dicionario_de_subscores).
    """
    off_bm = cfg.get("offshore_benchmark", {}).get(segmento, 0.15)
    caixa_bm = cfg.get("caixa_critico_usd", {}).get(segmento, 50_000.0)
    dolar_bm = cfg.get("dolar_benchmark", dolar_atual)

    pct_br = 1.0 - pct_offshore

    ratio_off = pct_offshore / off_bm if off_bm > 0 else 1.0
    if   ratio_off >= 1.00: sc_offshore = 0.00
    elif ratio_off >= 0.70: sc_offshore = 0.25
    elif ratio_off >= 0.40: sc_offshore = 0.50
    elif ratio_off >= 0.15: sc_offshore = 0.75
    else:                   sc_offshore = 1.00

    if   pct_br < 0.70: sc_concentr_br = 0.00
    elif pct_br < 0.80: sc_concentr_br = 0.25
    elif pct_br < 0.88: sc_concentr_br = 0.50
    elif pct_br < 0.95: sc_concentr_br = 0.75
    else:                sc_concentr_br = 1.00

    denom_cdi = 1.0 - pct_offshore
    cdi_ratio = pct_cdi / denom_cdi if denom_cdi > 0 else 0.0
    if   cdi_ratio < 0.40: sc_cdi = 0.00
    elif cdi_ratio < 0.55: sc_cdi = 0.25
    elif cdi_ratio < 0.70: sc_cdi = 0.50
    elif cdi_ratio < 0.85: sc_cdi = 0.75
    else:                   sc_cdi = 1.00

    if caixa_bm > 0:
        if   caixa_usd < caixa_bm * 0.15: sc_caixa_usd = 0.00
        elif caixa_usd < caixa_bm * 0.35: sc_caixa_usd = 0.25
        elif caixa_usd < caixa_bm * 0.60: sc_caixa_usd = 0.50
        elif caixa_usd < caixa_bm:         sc_caixa_usd = 0.75
        else:                              sc_caixa_usd = 1.00
    else:
        sc_caixa_usd = 0.00

    dias_sem_remessa = meses_sem_remessa * 30
    if   dias_sem_remessa < 30:  sc_remessa = 0.00
    elif dias_sem_remessa < 60:  sc_remessa = 0.25
    elif dias_sem_remessa < 90:  sc_remessa = 0.50
    elif dias_sem_remessa < 180: sc_remessa = 0.75
    else:                        sc_remessa = 1.00

    if   dolar_medio <= dolar_bm: sc_dolar = 0.00
    elif dolar_medio <= 5.40:      sc_dolar = 0.25
    elif dolar_medio <= 5.90:      sc_dolar = 0.50
    elif dolar_medio <= 6.50:      sc_dolar = 0.75
    else:                          sc_dolar = 1.00

    if perfil_risco not in ("Conservador", "Moderado"):
        sc_perfil_rf = 0.00
    else:
        rf_ratio = pct_rf_global / pct_offshore if pct_offshore > 0 else 0.0
        if   rf_ratio >= 0.30: sc_perfil_rf = 0.00
        elif rf_ratio >= 0.15: sc_perfil_rf = 0.25
        elif rf_ratio >= 0.05: sc_perfil_rf = 0.50
        elif rf_ratio >  0.00: sc_perfil_rf = 0.75
        else:                   sc_perfil_rf = 1.00

    if   pct_bdr < 0.03: sc_bdr = 0.00
    elif pct_bdr < 0.06: sc_bdr = 0.25
    elif pct_bdr < 0.10: sc_bdr = 0.50
    elif pct_bdr < 0.15: sc_bdr = 0.75
    else:                 sc_bdr = 1.00

    if   variacao_acoes_br_pct < -0.20: sc_perda_br = 1.0
    elif variacao_acoes_br_pct < -0.10: sc_perda_br = 0.5
    else:                                sc_perda_br = 0.0

    sc_gastos_dolar = 1.0 if tem_gastos_dolar else 0.0

    subscores = {
        "sc_concentr_br": sc_concentr_br,
        "sc_offshore": sc_offshore,
        "sc_cdi": sc_cdi,
        "sc_caixa_usd": sc_caixa_usd,
        "sc_remessa": sc_remessa,
        "sc_dolar": sc_dolar,
        "sc_perfil_rf": sc_perfil_rf,
        "sc_bdr": sc_bdr,
        "sc_perda_br": sc_perda_br,
        "sc_gastos_dolar": sc_gastos_dolar,
    }

    score_total = sum(subscores[k] * pesos.get(k, 0) for k in subscores) * 100

    return score_total, subscores
