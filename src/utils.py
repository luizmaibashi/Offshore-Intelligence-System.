"""
app/utils.py
----------------
Offshore Intelligence System (OIS) — Central de Processamento
Centraliza a lógica de negócios e heurísticas para garantir paridade treino-serventia.
"""

def calcular_score_ois(
    segmento: str,
    pct_br: float,
    pct_offshore: float,
    pct_cdi: float,
    caixa_usd: float,
    meses_sem_remessa: int,
    dolar_medio: float,
    dolar_atual: float,
    cfg: dict,
    pesos: dict
) -> tuple[float, dict]:
    """
    Calcula o Score GAP Total e os subscores heurísticos de um cliente.
    
    Args:
        segmento: Segmento do cliente (e.g., "Qualificado").
        pct_br: Porcentagem do portfólio concentrada no Brasil.
        pct_offshore: Porcentagem do portfólio alocada em Offshore.
        pct_cdi: Porcentagem do portfólio em CDI/Renda Fixa BR.
        caixa_usd: Valor em caixa na conta internacional (USD).
        meses_sem_remessa: Quantidade de meses sem enviar remessa.
        dolar_medio: Preço médio do dólar adquirido pelo cliente.
        dolar_atual: Dólar de referência atual (benchmark).
        cfg: Dicionário de configurações gerais.
        pesos: Dicionário com os pesos de cada critério.
        
    Returns:
        Uma tupla contendo (score_total, dicionario_de_subscores).
    """
    # Configurações dinâmicas baseadas no segmento
    off_bm = cfg.get("offshore_benchmark", {}).get(segmento, 0.15)
    caixa_bm = cfg.get("caixa_critico_usd", {}).get(segmento, 50_000.0)

    # Cálculo dos subscores (0.0 a 1.0)
    sc_concentr_br = min(pct_br / 0.9, 1.0)
    sc_offshore = max(0.0, min((off_bm - pct_offshore) / off_bm, 1.0)) if off_bm > 0 else 0.0
    sc_cdi = min(pct_cdi / 0.8, 1.0)
    sc_caixa_usd = max(0.0, min((caixa_bm - caixa_usd) / caixa_bm, 1.0)) if caixa_usd < caixa_bm and caixa_bm > 0 else 0.0
    sc_remessa = min(meses_sem_remessa / 24, 1.0)
    sc_dolar = max(0.0, min((dolar_medio - dolar_atual) / dolar_atual, 1.0)) if dolar_atual > 0 else 0.0
    sc_perfil_rf = min(pct_cdi / 0.75, 1.0)
    
    # Valores default/heurísticos (devem ser aprimorados pelo modelo na V2)
    sc_bdr = 0.3
    sc_perda_br = 0.2
    sc_gastos_dolar = 0.2

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

    # Calcula score total (0 a 100)
    score_total = sum(subscores[k] * pesos.get(k, 0) for k in subscores) * 100
    
    return score_total, subscores
