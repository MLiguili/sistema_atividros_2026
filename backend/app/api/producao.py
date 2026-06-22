from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import obter_db
from app.schemas.pedido import RespostaPedido
from app.schemas.producao import IniciarProducao, ResumoProducao
from app.services.autenticacao import obter_usuario_atual
from app.services import producao as producao_service

router = APIRouter(prefix="/producao", tags=["producao"])


@router.get("/fila", response_model=list[RespostaPedido])
async def listar_fila(
    status: str | None = None,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await producao_service.listar_fila(db, status)


@router.get("/resumo", response_model=ResumoProducao)
async def obter_resumo(
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await producao_service.resumo(db)


@router.post("/iniciar")
async def iniciar_producao(
    dados: IniciarProducao,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    if not dados.pedido_ids:
        raise HTTPException(status_code=400, detail="Nenhum pedido informado")

    return await producao_service.iniciar_lote(dados.pedido_ids, db)


@router.post("/{pedido_id}/avancar", response_model=RespostaPedido)
async def avancar_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await producao_service.avancar_pedido(pedido_id, db)
