import logging
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.financeiro import ContaPagar, ContaReceber, StatusFinanceiro
from app.schemas.financeiro import CriarContaPagar, CriarContaReceber, PagarConta, ReceberConta

logger = logging.getLogger(__name__)


async def criar_conta_receber(dados: CriarContaReceber, db: AsyncSession) -> ContaReceber:
    obj = ContaReceber(**dados.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def listar_contas_receber(
    db: AsyncSession,
    status_filtro: str | None = None,
) -> list[ContaReceber]:
    query = (
        select(ContaReceber)
        .options(selectinload(ContaReceber.pedido))
        .order_by(ContaReceber.data_vencimento.asc())
    )
    if status_filtro:
        query = query.where(ContaReceber.status == status_filtro)
    resultado = await db.execute(query)
    return list(resultado.scalars().all())


async def receber_conta(conta_id: int, dados: ReceberConta, db: AsyncSession) -> ContaReceber:
    resultado = await db.execute(
        select(ContaReceber)
        .where(ContaReceber.id == conta_id)
        .options(selectinload(ContaReceber.pedido))
    )
    conta = resultado.scalar_one_or_none()
    if not conta:
        raise HTTPException(status_code=404, detail="Conta a receber nao encontrada")

    if conta.status == StatusFinanceiro.recebido:
        raise HTTPException(status_code=400, detail="Conta ja foi recebida")

    novo_recebido = conta.valor_recebido + dados.valor_recebido
    if novo_recebido > conta.valor:
        raise HTTPException(
            status_code=400,
            detail=f"Valor recebido ({novo_recebido}) excede valor da conta ({conta.valor})",
        )

    conta.valor_recebido = novo_recebido
    conta.data_recebimento = dados.data_recebimento or date.today()

    if novo_recebido >= conta.valor:
        conta.status = StatusFinanceiro.recebido
    elif novo_recebido > 0:
        conta.status = StatusFinanceiro.parcial

    if conta.pedido_id and conta.status == StatusFinanceiro.recebido:
        from app.models.pedido import Pedido, PedidoEvento, StatusFinanceiro as PedidoStatusFinanceiro

        resultado_pedido = await db.execute(select(Pedido).where(Pedido.id == conta.pedido_id))
        pedido = resultado_pedido.scalar_one_or_none()
        if pedido and pedido.status_financeiro != PedidoStatusFinanceiro.pago_total.value:
            pedido.status_financeiro = PedidoStatusFinanceiro.pago_total
            pedido.saldo_devedor = 0.0
            evento = PedidoEvento(
                pedido_id=pedido.id,
                eixo="financeiro",
                status_anterior=pedido.status_financeiro.value,
                status_novo=PedidoStatusFinanceiro.pago_total.value,
                observacao="Pago automaticamente via recebimento de conta",
            )
            db.add(evento)

    await db.commit()
    await db.refresh(conta)

    resultado_final = await db.execute(
        select(ContaReceber)
        .where(ContaReceber.id == conta_id)
        .options(selectinload(ContaReceber.pedido))
    )
    return resultado_final.scalar_one()


async def criar_conta_pagar(dados: CriarContaPagar, db: AsyncSession) -> ContaPagar:
    obj = ContaPagar(**dados.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def listar_contas_pagar(
    db: AsyncSession,
    status_filtro: str | None = None,
) -> list[ContaPagar]:
    query = (
        select(ContaPagar)
        .options(selectinload(ContaPagar.fornecedor))
        .order_by(ContaPagar.data_vencimento.asc())
    )
    if status_filtro:
        query = query.where(ContaPagar.status == status_filtro)
    resultado = await db.execute(query)
    return list(resultado.scalars().all())


async def pagar_conta(conta_id: int, dados: PagarConta, db: AsyncSession) -> ContaPagar:
    resultado = await db.execute(
        select(ContaPagar)
        .where(ContaPagar.id == conta_id)
        .options(selectinload(ContaPagar.fornecedor))
    )
    conta = resultado.scalar_one_or_none()
    if not conta:
        raise HTTPException(status_code=404, detail="Conta a pagar nao encontrada")

    if conta.status == StatusFinanceiro.pago:
        raise HTTPException(status_code=400, detail="Conta ja foi paga")

    novo_pago = conta.valor_pago + dados.valor_pago
    if novo_pago > conta.valor:
        raise HTTPException(
            status_code=400,
            detail=f"Valor pago ({novo_pago}) excede valor da conta ({conta.valor})",
        )

    conta.valor_pago = novo_pago
    conta.data_pagamento = dados.data_pagamento or date.today()

    if novo_pago >= conta.valor:
        conta.status = StatusFinanceiro.pago
    elif novo_pago > 0:
        conta.status = StatusFinanceiro.parcial

    await db.commit()
    await db.refresh(conta)

    resultado_final = await db.execute(
        select(ContaPagar)
        .where(ContaPagar.id == conta_id)
        .options(selectinload(ContaPagar.fornecedor))
    )
    return resultado_final.scalar_one()


async def fluxo_caixa(
    db: AsyncSession,
    inicio: date | None = None,
    fim: date | None = None,
) -> list[dict]:
    if not inicio:
        inicio = date.today() - timedelta(days=30)
    if not fim:
        fim = date.today() + timedelta(days=30)

    lancamentos = []

    resultado_r = await db.execute(
        select(ContaReceber)
        .where(ContaReceber.data_vencimento.between(inicio, fim))
        .order_by(ContaReceber.data_vencimento)
    )
    for c in resultado_r.scalars().all():
        valor_real = c.valor_recebido if c.valor_recebido > 0 else c.valor
        lancamentos.append({
            "data": c.data_vencimento,
            "tipo": "receita",
            "descricao": c.descricao,
            "valor": valor_real,
            "conta_id": c.id,
            "modelo": "contas_receber",
        })

    resultado_p = await db.execute(
        select(ContaPagar)
        .where(ContaPagar.data_vencimento.between(inicio, fim))
        .order_by(ContaPagar.data_vencimento)
    )
    for c in resultado_p.scalars().all():
        valor_real = c.valor_pago if c.valor_pago > 0 else c.valor
        lancamentos.append({
            "data": c.data_vencimento,
            "tipo": "despesa",
            "descricao": c.descricao,
            "valor": valor_real,
            "conta_id": c.id,
            "modelo": "contas_pagar",
        })

    lancamentos.sort(key=lambda x: x["data"])
    return lancamentos


async def resumo(db: AsyncSession) -> dict:
    hoje = date.today()

    resultado_r = await db.execute(
        select(
            func.coalesce(func.sum(ContaReceber.valor), 0),
            func.coalesce(func.sum(ContaReceber.valor_recebido), 0),
        ).where(ContaReceber.status.in_([StatusFinanceiro.pendente, StatusFinanceiro.parcial]))
    )
    total_a_receber, total_recebido = resultado_r.one()

    resultado_p = await db.execute(
        select(
            func.coalesce(func.sum(ContaPagar.valor), 0),
            func.coalesce(func.sum(ContaPagar.valor_pago), 0),
        ).where(ContaPagar.status.in_([StatusFinanceiro.pendente, StatusFinanceiro.parcial]))
    )
    total_a_pagar, total_pago = resultado_p.one()

    resultado_r_vencidas = await db.execute(
        select(func.count(ContaReceber.id)).where(
            ContaReceber.status.in_([StatusFinanceiro.pendente, StatusFinanceiro.parcial]),
            ContaReceber.data_vencimento < hoje,
        )
    )
    contas_receber_vencidas = resultado_r_vencidas.scalar() or 0

    resultado_p_vencidas = await db.execute(
        select(func.count(ContaPagar.id)).where(
            ContaPagar.status.in_([StatusFinanceiro.pendente, StatusFinanceiro.parcial]),
            ContaPagar.data_vencimento < hoje,
        )
    )
    contas_pagar_vencidas = resultado_p_vencidas.scalar() or 0

    return {
        "total_a_receber": total_a_receber,
        "total_recebido": total_recebido,
        "total_a_pagar": total_a_pagar,
        "total_pago": total_pago,
        "saldo_previsto": total_a_receber - total_a_pagar,
        "contas_receber_vencidas": contas_receber_vencidas,
        "contas_pagar_vencidas": contas_pagar_vencidas,
    }
