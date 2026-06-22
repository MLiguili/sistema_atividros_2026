import logging

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pedido import Eixo, ItemPedido, Pedido, PedidoEvento, StatusProducao

logger = logging.getLogger(__name__)

STATUS_ORDEM = [
    StatusProducao.pendente,
    StatusProducao.aguardando_material,
    StatusProducao.em_producao,
    StatusProducao.para_embalar,
    StatusProducao.pronto_entrega,
    StatusProducao.entregue,
]

TRANSICOES_PRODUCAO = {
    StatusProducao.pendente: [StatusProducao.aguardando_material, StatusProducao.em_producao],
    StatusProducao.aguardando_material: [StatusProducao.pendente, StatusProducao.em_producao],
    StatusProducao.em_producao: [StatusProducao.pendente, StatusProducao.aguardando_material, StatusProducao.para_embalar],
    StatusProducao.para_embalar: [StatusProducao.em_producao, StatusProducao.pronto_entrega],
    StatusProducao.pronto_entrega: [StatusProducao.para_embalar, StatusProducao.entregue],
    StatusProducao.entregue: [StatusProducao.pronto_entrega],
}

PROXIMO_PASSO = {
    StatusProducao.pendente: StatusProducao.em_producao,
    StatusProducao.aguardando_material: StatusProducao.em_producao,
    StatusProducao.em_producao: StatusProducao.para_embalar,
    StatusProducao.para_embalar: StatusProducao.pronto_entrega,
    StatusProducao.pronto_entrega: StatusProducao.entregue,
    StatusProducao.entregue: StatusProducao.entregue,
}


async def listar_fila(db: AsyncSession, status_filtro: str | None = None) -> list[Pedido]:
    query = (
        select(Pedido)
        .options(
            selectinload(Pedido.itens),
            selectinload(Pedido.eventos),
            selectinload(Pedido.cliente),
        )
        .order_by(Pedido.criado_em.asc())
    )

    if status_filtro:
        query = query.where(Pedido.status_producao == status_filtro)
    else:
        query = query.where(
            Pedido.status_producao.in_([s.value for s in STATUS_ORDEM if s != StatusProducao.entregue])
        )

    resultado = await db.execute(query)
    return list(resultado.scalars().all())


async def avancar_pedido(pedido_id: int, db: AsyncSession) -> Pedido:
    resultado = await db.execute(
        select(Pedido)
        .where(Pedido.id == pedido_id)
        .options(selectinload(Pedido.itens), selectinload(Pedido.eventos))
    )
    pedido = resultado.scalar_one_or_none()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    status_atual = pedido.status_producao
    proximo = PROXIMO_PASSO.get(status_atual)

    if not proximo or proximo == status_atual:
        raise HTTPException(status_code=400, detail=f"Pedido ja esta no status final '{status_atual.value}'")

    if proximo not in TRANSICOES_PRODUCAO.get(status_atual, []):
        raise HTTPException(
            status_code=400,
            detail=f"Transicao de '{status_atual.value}' para '{proximo.value}' nao permitida",
        )

    if proximo == StatusProducao.em_producao:
        estoque_ok = await _verificar_estoque_para_avancar(pedido, db)
        if not estoque_ok["disponivel"]:
            raise HTTPException(
                status_code=400,
                detail=f"Estoque insuficiente: {'; '.join(estoque_ok['faltando'])}",
            )
        await _realizar_baixa_para_avancar(pedido, db)

    status_anterior = status_atual.value
    pedido.status_producao = proximo

    evento = PedidoEvento(
        pedido_id=pedido.id,
        eixo=Eixo.producao,
        status_anterior=status_anterior,
        status_novo=proximo.value,
        observacao=f"Avancado automaticamente de '{status_anterior}' para '{proximo.value}'",
    )
    db.add(evento)

    if proximo == StatusProducao.entregue:
        pedido.status_geral = "entregue"

    await db.commit()
    await db.refresh(pedido)

    resultado_final = await db.execute(
        select(Pedido)
        .where(Pedido.id == pedido.id)
        .options(selectinload(Pedido.itens), selectinload(Pedido.eventos), selectinload(Pedido.cliente))
    )
    return resultado_final.scalar_one()


async def iniciar_lote(pedido_ids: list[int], db: AsyncSession) -> dict:
    resultados = []
    sucessos = []

    for pid in pedido_ids:
        try:
            resultado = await db.execute(
                select(Pedido)
                .where(Pedido.id == pid)
                .options(selectinload(Pedido.itens).selectinload(ItemPedido.moldura), selectinload(Pedido.itens).selectinload(ItemPedido.vidro), selectinload(Pedido.itens).selectinload(ItemPedido.fundo))
            )
            pedido = resultado.scalar_one_or_none()

            if not pedido:
                resultados.append({"pedido_id": pid, "sucesso": False, "mensagem": "Pedido nao encontrado"})
                continue

            if pedido.status_producao not in [StatusProducao.pendente, StatusProducao.aguardando_material]:
                resultados.append(
                    {"pedido_id": pid, "sucesso": False, "mensagem": f"Status invalido: {pedido.status_producao.value}"}
                )
                continue

            estoque = await _verificar_estoque_para_avancar(pedido, db)
            if not estoque["disponivel"]:
                resultados.append(
                    {"pedido_id": pid, "sucesso": False, "mensagem": f"Estoque insuficiente: {'; '.join(estoque['faltando'])}"}
                )
                continue

            await _realizar_baixa_para_avancar(pedido, db)
            pedido.status_producao = StatusProducao.em_producao

            evento = PedidoEvento(
                pedido_id=pedido.id,
                eixo=Eixo.producao,
                status_anterior=StatusProducao.pendente.value,
                status_novo=StatusProducao.em_producao.value,
                observacao="Iniciado em lote",
            )
            db.add(evento)
            sucessos.append(pid)
            resultados.append({"pedido_id": pid, "sucesso": True, "mensagem": "OK"})

        except Exception as e:
            logger.error("Erro ao processar pedido %s: %s", pid, e)
            resultados.append({"pedido_id": pid, "sucesso": False, "mensagem": str(e)})

    if sucessos:
        await db.commit()

    return {"resultados": resultados, "total_processados": len(sucessos), "total_erros": len(resultados) - len(sucessos)}


async def resumo(db: AsyncSession) -> dict:
    query = select(Pedido.status_producao, func.count(Pedido.id)).group_by(Pedido.status_producao)
    resultado = await db.execute(query)
    contagem = dict(resultado.all())

    return {
        "pendente": contagem.get("pendente", 0),
        "aguardando_material": contagem.get("aguardando_material", 0),
        "em_producao": contagem.get("em_producao", 0),
        "para_embalar": contagem.get("para_embalar", 0),
        "pronto_entrega": contagem.get("pronto_entrega", 0),
        "entregue": contagem.get("entregue", 0),
        "total": sum(contagem.values()),
    }


async def _verificar_estoque_para_avancar(pedido: Pedido, db: AsyncSession) -> dict:
    resultado = await db.execute(
        select(ItemPedido)
        .where(ItemPedido.pedido_id == pedido.id)
        .options(selectinload(ItemPedido.moldura), selectinload(ItemPedido.vidro), selectinload(ItemPedido.fundo))
    )
    itens = resultado.scalars().all()

    faltando = []
    for item in itens:
        if item.moldura_id and item.moldura:
            if item.moldura.quantidade < item.quantidade:
                faltando.append(f"Moldura {item.moldura.codigo}: disponivel {item.moldura.quantidade}, necessario {item.quantidade}")
        if item.vidro_id and item.vidro:
            if item.vidro.quantidade < item.quantidade:
                faltando.append(f"Vidro {item.vidro.tipo}: disponivel {item.vidro.quantidade}, necessario {item.quantidade}")
        if item.fundo_id and item.fundo:
            if item.fundo.quantidade < item.quantidade:
                faltando.append(f"Fundo {item.fundo.tipo}: disponivel {item.fundo.quantidade}, necessario {item.quantidade}")

    return {"disponivel": len(faltando) == 0, "faltando": faltando}


async def _realizar_baixa_para_avancar(pedido: Pedido, db: AsyncSession) -> None:
    resultado = await db.execute(
        select(ItemPedido)
        .where(ItemPedido.pedido_id == pedido.id)
        .options(selectinload(ItemPedido.moldura), selectinload(ItemPedido.vidro), selectinload(ItemPedido.fundo))
    )
    itens = resultado.scalars().all()

    for item in itens:
        if item.moldura_id and item.moldura:
            item.moldura.quantidade -= item.quantidade
        if item.vidro_id and item.vidro:
            item.vidro.quantidade -= item.quantidade
        if item.fundo_id and item.fundo:
            item.fundo.quantidade -= item.quantidade
