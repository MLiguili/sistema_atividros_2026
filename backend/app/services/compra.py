import logging
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.compra import Fornecedor, ItemCompra, OrdemCompra, StatusCompra, TipoProduto
from app.models.estoque import Fundo, Moldura, Suplemento, Vidro
from app.schemas.compra import CriarFornecedor, CriarOrdemCompra, ReceberOrdemCompra

logger = logging.getLogger(__name__)


async def criar_fornecedor(dados: CriarFornecedor, db: AsyncSession) -> Fornecedor:
    obj = Fornecedor(**dados.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def listar_fornecedores(db: AsyncSession) -> list[Fornecedor]:
    resultado = await db.execute(select(Fornecedor).order_by(Fornecedor.nome))
    return list(resultado.scalars().all())


async def obter_fornecedor(fornecedor_id: int, db: AsyncSession) -> Fornecedor:
    resultado = await db.execute(select(Fornecedor).where(Fornecedor.id == fornecedor_id))
    obj = resultado.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Fornecedor nao encontrado")
    return obj


async def atualizar_fornecedor(fornecedor_id: int, dados: dict, db: AsyncSession) -> Fornecedor:
    obj = await obter_fornecedor(fornecedor_id, db)
    for campo, valor in dados.items():
        if valor is not None:
            setattr(obj, campo, valor)
    await db.commit()
    await db.refresh(obj)
    return obj


async def criar_ordem_compra(dados: CriarOrdemCompra, db: AsyncSession) -> OrdemCompra:
    await obter_fornecedor(dados.fornecedor_id, db)

    ordem = OrdemCompra(
        fornecedor_id=dados.fornecedor_id,
        data_prevista=dados.data_prevista,
        observacao=dados.observacao,
    )
    db.add(ordem)
    await db.flush()

    for item_in in dados.itens:
        item = ItemCompra(
            ordem_compra_id=ordem.id,
            **item_in.model_dump(),
        )
        db.add(item)

    await db.commit()

    resultado = await db.execute(
        select(OrdemCompra)
        .where(OrdemCompra.id == ordem.id)
        .options(selectinload(OrdemCompra.itens), selectinload(OrdemCompra.fornecedor))
    )
    return resultado.scalar_one()


async def listar_ordens(db: AsyncSession, status_filtro: str | None = None) -> list[OrdemCompra]:
    query = (
        select(OrdemCompra)
        .options(selectinload(OrdemCompra.itens), selectinload(OrdemCompra.fornecedor))
        .order_by(OrdemCompra.criado_em.desc())
    )
    if status_filtro:
        query = query.where(OrdemCompra.status == status_filtro)
    resultado = await db.execute(query)
    return list(resultado.scalars().all())


async def obter_ordem(ordem_id: int, db: AsyncSession) -> OrdemCompra:
    resultado = await db.execute(
        select(OrdemCompra)
        .where(OrdemCompra.id == ordem_id)
        .options(selectinload(OrdemCompra.itens), selectinload(OrdemCompra.fornecedor))
    )
    obj = resultado.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Ordem de compra nao encontrada")
    return obj


async def receber_ordem(ordem_id: int, dados: ReceberOrdemCompra, db: AsyncSession) -> OrdemCompra:
    ordem = await obter_ordem(ordem_id, db)

    if ordem.status in [StatusCompra.recebida, StatusCompra.cancelada]:
        raise HTTPException(status_code=400, detail=f"Ordem ja esta {ordem.status.value}")

    for item_input in dados.itens:
        item_db = next((i for i in ordem.itens if i.id == item_input.item_id), None)
        if not item_db:
            raise HTTPException(status_code=404, detail=f"Item {item_input.item_id} nao encontrado na ordem")

        nova_qtd = item_db.quantidade_recebida + item_input.quantidade_recebida
        if nova_qtd > item_db.quantidade_solicitada:
            raise HTTPException(
                status_code=400,
                detail=f"Item {item_input.item_id}: recebimento ({nova_qtd}) excede solicitado ({item_db.quantidade_solicitada})",
            )

        item_db.quantidade_recebida = nova_qtd
        await _atualizar_estoque(item_db.produto_tipo, item_db.produto_id, item_input.quantidade_recebida, db)
        logger.debug("Item %s recebido: +%s no produto %s %s", item_db.id, item_input.quantidade_recebida, item_db.produto_tipo.value, item_db.produto_id)

    todos_recebidos = all(i.quantidade_recebida >= i.quantidade_solicitada for i in ordem.itens)
    algum_recebido = any(i.quantidade_recebida > 0 for i in ordem.itens)

    if todos_recebidos:
        ordem.status = StatusCompra.recebida
    elif algum_recebido:
        ordem.status = StatusCompra.parcial

    await db.commit()

    resultado = await db.execute(
        select(OrdemCompra)
        .where(OrdemCompra.id == ordem_id)
        .options(selectinload(OrdemCompra.itens), selectinload(OrdemCompra.fornecedor))
    )
    return resultado.scalar_one()


async def atualizar_status_ordem(ordem_id: int, novo_status: str, db: AsyncSession) -> OrdemCompra:
    ordem = await obter_ordem(ordem_id, db)

    try:
        ordem.status = StatusCompra(novo_status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Status invalido: {novo_status}")

    await db.commit()
    await db.refresh(ordem)
    return ordem


async def sugerir_compras(db: AsyncSession) -> list[dict]:
    LIMIAR_MOLDURA = 3
    LIMIAR_VIDRO = 2
    LIMIAR_FUNDO = 2
    LIMIAR_SUPLEMENTO = 5

    sugestoes = []

    resultado_m = await db.execute(select(Moldura).where(Moldura.quantidade < LIMIAR_MOLDURA))
    for m in resultado_m.scalars().all():
        sugestoes.append({
            "produto_tipo": TipoProduto.moldura.value,
            "produto_id": m.id,
            "nome": f"Moldura {m.codigo} ({m.cor})",
            "quantidade_atual": m.quantidade,
            "quantidade_sugerida": LIMIAR_MOLDURA - m.quantidade + 5,
            "motivo": f"Estoque abaixo de {LIMIAR_MOLDURA} unidades",
        })

    resultado_v = await db.execute(select(Vidro).where(Vidro.quantidade < LIMIAR_VIDRO))
    for v in resultado_v.scalars().all():
        sugestoes.append({
            "produto_tipo": TipoProduto.vidro.value,
            "produto_id": v.id,
            "nome": f"Vidro {v.tipo} {v.espessura}mm",
            "quantidade_atual": v.quantidade,
            "quantidade_sugerida": LIMIAR_VIDRO - v.quantidade + 3,
            "motivo": f"Estoque abaixo de {LIMIAR_VIDRO} unidades",
        })

    resultado_f = await db.execute(select(Fundo).where(Fundo.quantidade < LIMIAR_FUNDO))
    for f in resultado_f.scalars().all():
        sugestoes.append({
            "produto_tipo": TipoProduto.fundo.value,
            "produto_id": f.id,
            "nome": f"Fundo {f.tipo} {f.espessura}mm",
            "quantidade_atual": f.quantidade,
            "quantidade_sugerida": LIMIAR_FUNDO - f.quantidade + 3,
            "motivo": f"Estoque abaixo de {LIMIAR_FUNDO} unidades",
        })

    resultado_s = await db.execute(select(Suplemento).where(Suplemento.quantidade < LIMIAR_SUPLEMENTO))
    for s in resultado_s.scalars().all():
        sugestoes.append({
            "produto_tipo": TipoProduto.suplemento.value,
            "produto_id": s.id,
            "nome": s.nome,
            "quantidade_atual": s.quantidade,
            "quantidade_sugerida": LIMIAR_SUPLEMENTO - s.quantidade + 10,
            "motivo": f"Estoque abaixo de {LIMIAR_SUPLEMENTO} unidades",
        })

    return sugestoes


async def _atualizar_estoque(produto_tipo: TipoProduto, produto_id: int, quantidade: int, db: AsyncSession) -> None:
    model_map = {
        TipoProduto.moldura: Moldura,
        TipoProduto.vidro: Vidro,
        TipoProduto.fundo: Fundo,
        TipoProduto.suplemento: Suplemento,
    }

    model = model_map.get(produto_tipo)
    if not model:
        raise HTTPException(status_code=400, detail=f"Tipo de produto invalido: {produto_tipo}")

    resultado = await db.execute(select(model).where(model.id == produto_id))
    obj = resultado.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail=f"Produto {produto_tipo.value} id {produto_id} nao encontrado")

    obj.quantidade += quantidade
