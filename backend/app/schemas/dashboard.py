from decimal import Decimal

from pydantic import BaseModel


class MolduraCriticaResumo(BaseModel):
    """
    Resumo de moldura com saldo igual ou abaixo do mínimo configurado.
    """

    id: int
    codigo: str
    cor: str
    quantidade: int
    estoque_minimo: int


class VidroCriticoResumo(BaseModel):
    """
    Resumo de vidro com saldo em m² igual ou abaixo do mínimo configurado.
    """

    id: int
    tipo: str
    espessura: Decimal
    area_disponivel_m2: Decimal
    estoque_minimo_m2: Decimal


class FundoCriticoResumo(BaseModel):
    """
    Resumo de fundo com saldo em m² igual ou abaixo do mínimo configurado.
    """

    id: int
    tipo: str
    espessura: Decimal
    area_disponivel_m2: Decimal
    estoque_minimo_m2: Decimal


class AlertasEstoqueDashboard(BaseModel):
    """
    Agrupamento de materiais críticos e em ruptura exibidos no Dashboard.
    """

    molduras_criticas: list[MolduraCriticaResumo]
    vidros_criticos: list[VidroCriticoResumo]
    fundos_criticos: list[FundoCriticoResumo]


class RespostaDashboardResumo(BaseModel):
    """
    Payload consolidado de indicadores financeiros, operacionais e alertas do Dashboard.
    """

    receita_confirmada: Decimal
    total_a_receber: Decimal
    pedidos_ativos: int
    pedidos_hoje: int
    pedidos_prazo_vencido: int
    pedidos_vencendo_hoje: int
    orcamentos_abertos: int
    alertas_estoque: AlertasEstoqueDashboard
