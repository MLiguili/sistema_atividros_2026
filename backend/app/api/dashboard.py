from datetime import UTC, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import obter_db
from app.models.estoque import Fundo, Moldura, Vidro
from app.models.pedido import Pedido, StatusGeral
from app.schemas.dashboard import (
    AlertasEstoqueDashboard,
    FundoCriticoResumo,
    MolduraCriticaResumo,
    RespostaDashboardResumo,
    VidroCriticoResumo,
)
from app.services.autenticacao import obter_usuario_atual
from app.services.calculadora import arredondar_2, arredondar_4

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _obter_fuso_loja():
    """
    Retorna o fuso horário da loja (America/Sao_Paulo) com fallback para -03:00.
    """
    try:
        return ZoneInfo("America/Sao_Paulo")
    except ZoneInfoNotFoundError:
        from datetime import timezone

        return timezone(timedelta(hours=-3))


@router.get("/resumo", response_model=RespostaDashboardResumo)
async def obter_resumo_dashboard(
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Retorna os indicadores financeiros, contadores de prazo e alertas críticos de estoque.
    """
    fuso = _obter_fuso_loja()
    hoje_local = datetime.now(fuso).date()

    pedidos_res = await db.execute(select(Pedido))
    pedidos = pedidos_res.scalars().all()

    receita_confirmada = Decimal("0.00")
    total_a_receber = Decimal("0.00")
    pedidos_ativos = 0
    pedidos_hoje = 0
    pedidos_prazo_vencido = 0
    pedidos_vencendo_hoje = 0
    orcamentos_abertos = 0

    for pedido in pedidos:
        if pedido.status_geral in (StatusGeral.confirmado, StatusGeral.entregue, StatusGeral.arquivado):
            receita_confirmada += Decimal(str(pedido.valor_total))

        if pedido.status_geral in (StatusGeral.confirmado, StatusGeral.entregue):
            total_a_receber += Decimal(str(pedido.saldo_devedor))

        if pedido.status_geral == StatusGeral.confirmado:
            pedidos_ativos += 1
            if pedido.prazo_entrega is not None:
                if pedido.prazo_entrega < hoje_local:
                    pedidos_prazo_vencido += 1
                elif pedido.prazo_entrega == hoje_local:
                    pedidos_vencendo_hoje += 1

        if pedido.status_geral == StatusGeral.rascunho:
            orcamentos_abertos += 1

        if pedido.criado_em is not None:
            dt = pedido.criado_em if pedido.criado_em.tzinfo is not None else pedido.criado_em.replace(tzinfo=UTC)
            if dt.astimezone(fuso).date() == hoje_local:
                pedidos_hoje += 1

    molduras_res = await db.execute(
        select(Moldura).where(Moldura.quantidade <= Moldura.estoque_minimo).order_by(Moldura.quantidade.asc())
    )
    molduras_criticas = [
        MolduraCriticaResumo(
            id=m.id,
            codigo=m.codigo,
            cor=m.cor,
            quantidade=m.quantidade,
            estoque_minimo=m.estoque_minimo,
        )
        for m in molduras_res.scalars().all()
    ]

    vidros_res = await db.execute(
        select(Vidro).where(Vidro.area_disponivel_m2 <= Vidro.estoque_minimo_m2).order_by(Vidro.area_disponivel_m2.asc())
    )
    vidros_criticos = [
        VidroCriticoResumo(
            id=v.id,
            tipo=v.tipo.value,
            espessura=arredondar_2(Decimal(str(v.espessura))),
            area_disponivel_m2=arredondar_4(Decimal(str(v.area_disponivel_m2))),
            estoque_minimo_m2=arredondar_4(Decimal(str(v.estoque_minimo_m2))),
        )
        for v in vidros_res.scalars().all()
    ]

    fundos_res = await db.execute(
        select(Fundo).where(Fundo.area_disponivel_m2 <= Fundo.estoque_minimo_m2).order_by(Fundo.area_disponivel_m2.asc())
    )
    fundos_criticos = [
        FundoCriticoResumo(
            id=f.id,
            tipo=f.tipo,
            espessura=arredondar_2(Decimal(str(f.espessura))),
            area_disponivel_m2=arredondar_4(Decimal(str(f.area_disponivel_m2))),
            estoque_minimo_m2=arredondar_4(Decimal(str(f.estoque_minimo_m2))),
        )
        for f in fundos_res.scalars().all()
    ]

    return RespostaDashboardResumo(
        receita_confirmada=arredondar_2(receita_confirmada),
        total_a_receber=arredondar_2(total_a_receber),
        pedidos_ativos=pedidos_ativos,
        pedidos_hoje=pedidos_hoje,
        pedidos_prazo_vencido=pedidos_prazo_vencido,
        pedidos_vencendo_hoje=pedidos_vencendo_hoje,
        orcamentos_abertos=orcamentos_abertos,
        alertas_estoque=AlertasEstoqueDashboard(
            molduras_criticas=molduras_criticas,
            vidros_criticos=vidros_criticos,
            fundos_criticos=fundos_criticos,
        ),
    )
