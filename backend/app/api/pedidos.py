
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import obter_db
from app.models.pedido import ItemPedido, Pedido, PedidoEvento
from app.schemas.pedido import AtualizarStatusPedido, CriarPedido, RespostaEventoPedido, RespostaPedido
from app.services.autenticacao import obter_usuario_atual
from app.services.gerador_pdf import gerar_binary_pdf
from app.services.pedido import (
    atualizar_status_pedido,
    criar_novo_pedido,
    realizar_baixa_estoque,
    verificar_estoque_disponivel,
)

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@router.post("/", response_model=RespostaPedido, status_code=status.HTTP_201_CREATED)
async def criar_pedido(obj_in: CriarPedido, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    return await criar_novo_pedido(obj_in, db)


@router.get("/", response_model=list[RespostaPedido])
async def listar_pedidos(db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(
        select(Pedido).options(
            selectinload(Pedido.itens),
            selectinload(Pedido.eventos)
        ).order_by(Pedido.criado_em.desc())
    )
    return resultado.scalars().all()


@router.get("/{pedido_id}", response_model=RespostaPedido)
async def obter_pedido(pedido_id: int, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(
        select(Pedido).where(Pedido.id == pedido_id).options(
            selectinload(Pedido.itens),
            selectinload(Pedido.eventos)
        )
    )
    obj = resultado.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")
    return obj


@router.put("/{pedido_id}", response_model=RespostaPedido)
async def atualizar_pedido(
    pedido_id: int,
    obj_in: CriarPedido,
    db: AsyncSession = Depends(obter_db),
    _ = Depends(obter_usuario_atual)
):
    resultado = await db.execute(
        select(Pedido).where(Pedido.id == pedido_id).options(
            selectinload(Pedido.itens),
            selectinload(Pedido.eventos)
        )
    )
    pedido = resultado.scalar_one_or_none()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    if pedido.status_geral.value not in ["rascunho", "cancelado"]:
        raise HTTPException(status_code=400, detail="Apenas pedidos em rascunho ou cancelado podem ser editados")

    pedido.cliente_id = obj_in.cliente_id
    pedido.endereco_entrega = obj_in.endereco_entrega
    pedido.frete = obj_in.frete
    pedido.valor_sinal = obj_in.valor_sinal

    for item_db in pedido.itens:
        await db.delete(item_db)
    pedido.itens.clear()

    total_pedido = 0.0
    for item_in in obj_in.itens:
        subtotal = item_in.preco_unitario * item_in.quantidade
        item_db = ItemPedido(
            pedido_id=pedido.id,
            descricao=item_in.descricao or "Quadro",
            quantidade=item_in.quantidade,
            preco_unitario=item_in.preco_unitario,
            subtotal=subtotal,
            moldura_id=item_in.moldura_id,
            vidro_id=item_in.vidro_id,
            fundo_id=item_in.fundo_id,
            largura=item_in.largura,
            altura=item_in.altura
        )
        db.add(item_db)
        total_pedido += float(subtotal)

    pedido.valor_total = total_pedido
    pedido.saldo_devedor = total_pedido - float(pedido.valor_sinal or 0)

    await db.commit()
    await db.refresh(pedido)

    resultado_final = await db.execute(
        select(Pedido).where(Pedido.id == pedido_id).options(
            selectinload(Pedido.itens),
            selectinload(Pedido.eventos)
        )
    )
    return resultado_final.scalar_one()


@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(obter_db),
    _ = Depends(obter_usuario_atual)
):
    resultado = await db.execute(
        select(Pedido).where(Pedido.id == pedido_id).options(
            selectinload(Pedido.itens),
            selectinload(Pedido.eventos)
        )
    )
    pedido = resultado.scalar_one_or_none()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    if pedido.status_geral.value not in ["rascunho", "cancelado"]:
        raise HTTPException(status_code=400, detail="Apenas pedidos em rascunho ou cancelado podem ser deletados")

    await db.delete(pedido)
    await db.commit()


@router.patch("/{pedido_id}/status", response_model=RespostaPedido)
async def atualizar_status(
    pedido_id: int,
    obj_in: AtualizarStatusPedido,
    db: AsyncSession = Depends(obter_db),
    _ = Depends(obter_usuario_atual)
):
    resultado = await db.execute(
        select(Pedido).where(Pedido.id == pedido_id).options(
            selectinload(Pedido.itens),
            selectinload(Pedido.eventos)
        )
    )
    pedido = resultado.scalar_one_or_none()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    return await atualizar_status_pedido(pedido, obj_in.eixo, obj_in.novo_status, obj_in.observacao or "", db, obj_in.valor_sinal)


@router.get("/{pedido_id}/eventos", response_model=list[RespostaEventoPedido])
async def listar_eventos(pedido_id: int, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(
        select(PedidoEvento).where(PedidoEvento.pedido_id == pedido_id).order_by(PedidoEvento.criado_em.asc())
    )
    return resultado.scalars().all()


@router.post("/{pedido_id}/baixa-estoque")
async def baixar_estoque_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(obter_db),
    _ = Depends(obter_usuario_atual)
):
    resultado = await db.execute(
        select(Pedido).where(Pedido.id == pedido_id).options(
            selectinload(Pedido.itens),
            selectinload(Pedido.eventos)
        )
    )
    pedido = resultado.scalar_one_or_none()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    if pedido.status_producao.value not in ["pendente", "aguardando_material"]:
        raise HTTPException(status_code=400, detail="Baixa de estoque so e permitida quando status de producao e 'pendente' ou 'aguardo_material'")

    estoque = await verificar_estoque_disponivel(pedido, db)
    if not estoque["disponivel"]:
        raise HTTPException(status_code=400, detail=f"Estoque insuficiente: {'; '.join(estoque['faltando'])}")

    await realizar_baixa_estoque(pedido, db)

    resultado_final = await db.execute(
        select(Pedido).where(Pedido.id == pedido_id).options(
            selectinload(Pedido.itens),
            selectinload(Pedido.eventos)
        )
    )
    return resultado_final.scalar_one()


@router.get("/{pedido_id}/pdf")
async def baixar_pdf_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(obter_db),
    _ = Depends(obter_usuario_atual)
):
    resultado = await db.execute(
        select(Pedido).where(Pedido.id == pedido_id).options(
            selectinload(Pedido.itens).selectinload(ItemPedido.moldura),
            selectinload(Pedido.itens).selectinload(ItemPedido.vidro),
            selectinload(Pedido.itens).selectinload(ItemPedido.fundo),
            selectinload(Pedido.cliente)
        )
    )
    pedido = resultado.scalar_one_or_none()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    pdf_bytes = gerar_binary_pdf(pedido)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=pedido_{pedido_id}.pdf"}
    )
