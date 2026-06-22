from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import obter_db
from app.schemas.financeiro import (
    CriarContaPagar,
    CriarContaReceber,
    FluxoCaixaItem,
    PagarConta,
    ReceberConta,
    ResumoFinanceiro,
    RespostaContaPagar,
    RespostaContaReceber,
)
from app.services.autenticacao import obter_usuario_atual
from app.services import financeiro as financeiro_service

router = APIRouter(prefix="/financeiro", tags=["financeiro"])


@router.post("/contas-receber", response_model=RespostaContaReceber, status_code=201)
async def criar_conta_receber(
    dados: CriarContaReceber,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await financeiro_service.criar_conta_receber(dados, db)


@router.get("/contas-receber", response_model=list[RespostaContaReceber])
async def listar_contas_receber(
    status: str | None = None,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await financeiro_service.listar_contas_receber(db, status)


@router.post("/contas-receber/{conta_id}/receber", response_model=RespostaContaReceber)
async def receber_conta(
    conta_id: int,
    dados: ReceberConta,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await financeiro_service.receber_conta(conta_id, dados, db)


@router.post("/contas-pagar", response_model=RespostaContaPagar, status_code=201)
async def criar_conta_pagar(
    dados: CriarContaPagar,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await financeiro_service.criar_conta_pagar(dados, db)


@router.get("/contas-pagar", response_model=list[RespostaContaPagar])
async def listar_contas_pagar(
    status: str | None = None,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await financeiro_service.listar_contas_pagar(db, status)


@router.post("/contas-pagar/{conta_id}/pagar", response_model=RespostaContaPagar)
async def pagar_conta(
    conta_id: int,
    dados: PagarConta,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await financeiro_service.pagar_conta(conta_id, dados, db)


@router.get("/fluxo-caixa", response_model=list[FluxoCaixaItem])
async def obter_fluxo_caixa(
    inicio: date | None = Query(default=None),
    fim: date | None = Query(default=None),
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await financeiro_service.fluxo_caixa(db, inicio, fim)


@router.get("/resumo", response_model=ResumoFinanceiro)
async def obter_resumo(
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    return await financeiro_service.resumo(db)
