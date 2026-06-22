from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import obter_db
from app.schemas.compra import (
    AtualizarFornecedor,
    CriarFornecedor,
    CriarOrdemCompra,
    ReceberOrdemCompra,
    RespostaFornecedor,
    RespostaOrdemCompra,
    SugestaoCompra,
)
from app.services.autenticacao import obter_usuario_atual
from app.services import compra as compra_service

router = APIRouter(prefix="/compras", tags=["compras"])


@router.post("/fornecedores", response_model=RespostaFornecedor, status_code=201)
async def criar_fornecedor(
    dados: CriarFornecedor,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await compra_service.criar_fornecedor(dados, db)


@router.get("/fornecedores", response_model=list[RespostaFornecedor])
async def listar_fornecedores(
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await compra_service.listar_fornecedores(db)


@router.get("/fornecedores/{fornecedor_id}", response_model=RespostaFornecedor)
async def obter_fornecedor(
    fornecedor_id: int,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await compra_service.obter_fornecedor(fornecedor_id, db)


@router.put("/fornecedores/{fornecedor_id}", response_model=RespostaFornecedor)
async def atualizar_fornecedor(
    fornecedor_id: int,
    dados: AtualizarFornecedor,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await compra_service.atualizar_fornecedor(fornecedor_id, dados.model_dump(exclude_unset=True), db)


@router.post("/ordens", response_model=RespostaOrdemCompra, status_code=201)
async def criar_ordem_compra(
    dados: CriarOrdemCompra,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await compra_service.criar_ordem_compra(dados, db)


@router.get("/ordens", response_model=list[RespostaOrdemCompra])
async def listar_ordens(
    status: str | None = None,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await compra_service.listar_ordens(db, status)


@router.get("/ordens/{ordem_id}", response_model=RespostaOrdemCompra)
async def obter_ordem(
    ordem_id: int,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await compra_service.obter_ordem(ordem_id, db)


@router.post("/ordens/{ordem_id}/receber", response_model=RespostaOrdemCompra)
async def receber_ordem(
    ordem_id: int,
    dados: ReceberOrdemCompra,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await compra_service.receber_ordem(ordem_id, dados, db)


@router.patch("/ordens/{ordem_id}/status", response_model=RespostaOrdemCompra)
async def atualizar_status(
    ordem_id: int,
    status: str,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await compra_service.atualizar_status_ordem(ordem_id, status, db)


@router.get("/sugerir", response_model=list[SugestaoCompra])
async def sugerir_compras(
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await compra_service.sugerir_compras(db)
