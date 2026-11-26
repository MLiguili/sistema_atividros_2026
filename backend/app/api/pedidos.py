from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import obter_db
from app.models.cliente import Cliente
from app.models.pedido import Pedido, PedidoEvento, StatusGeral, StatusProducao
from app.schemas.pedido import (
    AtualizarStatusPedido,
    ConfirmarBaixaEstoque,
    CriarPagamentoPedido,
    CriarPedido,
    EstornarPagamentoPedido,
    RespostaBaixaEstoque,
    RespostaEventoPedido,
    RespostaPagamentoPedido,
    RespostaPedido,
    RespostaPrevisaoBaixa,
)
from app.services.autenticacao import obter_usuario_atual
from app.services.gerador_pdf import gerar_binary_pdf
from app.services.pedido import (
    atualizar_pedido_rascunho,
    atualizar_status_pedido,
    carregar_pedido_completo,
    criar_novo_pedido,
    estornar_pagamento_pedido,
    obter_previsao_baixa_estoque,
    opcoes_carregamento_pedido,
    realizar_baixa_estoque_assistida,
    registrar_pagamento_pedido,
)

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@router.post("/", response_model=RespostaPedido, status_code=status.HTTP_201_CREATED)
async def criar_pedido(
    obj_in: CriarPedido,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Cria um novo orçamento/pedido multi-item calculando valores sugeridos e totais no backend.
    """
    return await criar_novo_pedido(obj_in, db)


@router.get("/", response_model=list[RespostaPedido])
async def listar_pedidos(
    cliente_id: int | None = Query(default=None),
    status_geral: StatusGeral | None = Query(default=None),
    status_producao: StatusProducao | None = Query(default=None),
    q: str | None = Query(default=None, description="Busca por número do pedido ou nome do cliente"),
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Lista pedidos com filtros server-side por cliente, status e busca textual.
    """
    stmt = select(Pedido).options(*opcoes_carregamento_pedido())

    if cliente_id is not None:
        stmt = stmt.where(Pedido.cliente_id == cliente_id)
    if status_geral is not None:
        stmt = stmt.where(Pedido.status_geral == status_geral)
    if status_producao is not None:
        stmt = stmt.where(Pedido.status_producao == status_producao)
    if q and q.strip():
        termo = f"%{q.strip().lower()}%"
        stmt = stmt.join(Pedido.cliente).where(
            or_(
                func.lower(Pedido.numero_pedido).like(termo),
                func.lower(Cliente.nome).like(termo),
                func.lower(Cliente.sobrenome).like(termo),
            )
        )

    stmt = stmt.order_by(Pedido.criado_em.desc())
    resultado = await db.execute(stmt)
    return resultado.scalars().unique().all()


@router.get("/{pedido_id}", response_model=RespostaPedido)
async def obter_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Retorna os detalhes completos de um pedido específico.
    """
    return await carregar_pedido_completo(pedido_id, db)


@router.put("/{pedido_id}", response_model=RespostaPedido)
async def atualizar_pedido(
    pedido_id: int,
    obj_in: CriarPedido,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Atualiza um pedido enquanto estiver no estado 'rascunho'.
    """
    return await atualizar_pedido_rascunho(pedido_id, obj_in, db)


@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Exclui pedidos em 'rascunho' ou 'cancelado' sem pagamentos ativos não estornados.
    """
    pedido = await carregar_pedido_completo(pedido_id, db)

    if pedido.status_geral not in (StatusGeral.rascunho, StatusGeral.cancelado):
        raise HTTPException(
            status_code=400,
            detail="Apenas pedidos em rascunho ou cancelado podem ser excluídos",
        )

    pagamentos_ativos = any(not p.estornado for p in pedido.pagamentos)
    if pagamentos_ativos:
        raise HTTPException(
            status_code=400,
            detail="Estorne os pagamentos ativos antes de excluir o pedido",
        )

    await db.delete(pedido)
    await db.commit()


@router.patch("/{pedido_id}/status", response_model=RespostaPedido)
async def atualizar_status(
    pedido_id: int,
    obj_in: AtualizarStatusPedido,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Executa transição de status nos eixos geral ou produção.
    """
    return await atualizar_status_pedido(
        pedido_id=pedido_id,
        eixo=obj_in.eixo,
        novo_status=obj_in.novo_status,
        observacao=obj_in.observacao or "",
        db=db,
    )


@router.get("/{pedido_id}/pagamentos", response_model=list[RespostaPagamentoPedido])
async def listar_pagamentos(
    pedido_id: int,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Lista todos os lançamentos de pagamento (inclusive estornados) de um pedido.
    """
    pedido = await carregar_pedido_completo(pedido_id, db)
    return pedido.pagamentos


@router.post("/{pedido_id}/pagamentos", response_model=RespostaPedido, status_code=status.HTTP_201_CREATED)
async def criar_pagamento(
    pedido_id: int,
    obj_in: CriarPagamentoPedido,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Registra um pagamento parcial ou integral no pedido.
    """
    return await registrar_pagamento_pedido(pedido_id, obj_in, db)


@router.post("/{pedido_id}/pagamentos/{pag_id}/estornar", response_model=RespostaPedido)
async def estornar_pagamento(
    pedido_id: int,
    pag_id: int,
    obj_in: EstornarPagamentoPedido | None = None,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Estorna um pagamento específico mantendo o registro histórico e recalculando o saldo.
    """
    motivo = obj_in.motivo if obj_in else None
    return await estornar_pagamento_pedido(pedido_id, pag_id, motivo, db)


@router.get("/{pedido_id}/eventos", response_model=list[RespostaEventoPedido])
async def listar_eventos(
    pedido_id: int,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Retorna a linha do tempo cronológica de eventos do pedido.
    """
    resultado = await db.execute(
        select(PedidoEvento)
        .where(PedidoEvento.pedido_id == pedido_id)
        .order_by(PedidoEvento.criado_em.asc(), PedidoEvento.id.asc())
    )
    return resultado.scalars().all()


@router.get("/{pedido_id}/previsao-baixa", response_model=RespostaPrevisaoBaixa)
async def prever_baixa_estoque(
    pedido_id: int,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Retorna a previsão de barras e m² reais a debitar antes de iniciar a produção.
    """
    return await obter_previsao_baixa_estoque(pedido_id, db)


@router.post("/{pedido_id}/baixa-estoque", response_model=RespostaBaixaEstoque)
async def baixar_estoque_pedido(
    pedido_id: int,
    obj_in: ConfirmarBaixaEstoque | None = None,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Confirma a Baixa Assistida de estoque (não-bloqueante) e avança o pedido para em_producao.
    """
    pedido, materiais, alertas = await realizar_baixa_estoque_assistida(pedido_id, obj_in, db)
    return RespostaBaixaEstoque(
        pedido=pedido,
        materiais_baixados=materiais,
        alertas_ruptura=alertas,
    )


@router.get("/{pedido_id}/pdf")
async def baixar_pdf_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Gera e retorna o documento PDF Único A4 (Orçamento, Ordem de Serviço ou Cancelado).
    """
    pedido = await carregar_pedido_completo(pedido_id, db)
    pdf_bytes = gerar_binary_pdf(pedido)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=pedido_{pedido.numero_pedido}.pdf"},
    )
