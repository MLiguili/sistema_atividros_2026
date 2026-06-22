
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import obter_db
from app.models.tabela_preco import TabelaPrecoPaspatour, TabelaPrecoVidro
from app.schemas.calculadora import EntradaCalculo, EntradaCalculoQuadro, ResultadoCalculo, ResultadoCalculoQuadro
from app.schemas.tabela_preco import (
    AtualizarTabelaPrecoPaspatour,
    AtualizarTabelaPrecoVidro,
    CriarTabelaPrecoPaspatour,
    CriarTabelaPrecoVidro,
    RespostaTabelaPrecoPaspatour,
    RespostaTabelaPrecoVidro,
)
from app.services.autenticacao import obter_usuario_atual
from app.services.calculadora import calcular_quadro
from app.services.pedido import obter_detalhes_calculo

router = APIRouter(prefix="/calculadora", tags=["calculadora"])

@router.post("/quadro", response_model=ResultadoCalculoQuadro)
async def calcular_quadro_avancado(
    dados: EntradaCalculoQuadro,
    db: AsyncSession = Depends(obter_db),
    _ = Depends(obter_usuario_atual)
):
    return await calcular_quadro(dados, db)


@router.post("/", response_model=ResultadoCalculo)
async def calcular_orcamento(
    dados: EntradaCalculo,
    db: AsyncSession = Depends(obter_db),
    _ = Depends(obter_usuario_atual)
):
    dados_dict = dados.model_dump()
    itens_detalhes, total = await obter_detalhes_calculo(dados_dict, db)
    return {"itens": itens_detalhes, "total_estimado": total}


@router.post("/simular", response_model=ResultadoCalculo)
async def simular_calculo(
    dados: EntradaCalculo,
    db: AsyncSession = Depends(obter_db),
    _ = Depends(obter_usuario_atual)
):
    dados_dict = dados.model_dump()
    itens_detalhes, total = await obter_detalhes_calculo(dados_dict, db)
    return {"itens": itens_detalhes, "total_estimado": total}


# Tabela de Preços de Vidro
@router.get("/tabela-vidro", response_model=list[RespostaTabelaPrecoVidro])
async def listar_tabela_vidro(db: AsyncSession = Depends(obter_db)):
    resultado = await db.execute(select(TabelaPrecoVidro))
    return resultado.scalars().all()

@router.post("/tabela-vidro", response_model=RespostaTabelaPrecoVidro, status_code=status.HTTP_201_CREATED)
async def criar_preco_vidro(obj_in: CriarTabelaPrecoVidro, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    existente = await db.execute(select(TabelaPrecoVidro).where(TabelaPrecoVidro.tipo == obj_in.tipo))
    if existente.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ja existe preco para este tipo de vidro")
    db_obj = TabelaPrecoVidro(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.put("/tabela-vidro/{preco_id}", response_model=RespostaTabelaPrecoVidro)
async def atualizar_preco_vidro(preco_id: int, obj_in: AtualizarTabelaPrecoVidro, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(select(TabelaPrecoVidro).where(TabelaPrecoVidro.id == preco_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Preco nao encontrado")
    db_obj.preco_por_m2 = obj_in.preco_por_m2
    db_obj.descricao = obj_in.descricao
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

# Tabela de Preços de Paspatour
@router.get("/tabela-paspatour", response_model=list[RespostaTabelaPrecoPaspatour])
async def listar_tabela_paspatour(db: AsyncSession = Depends(obter_db)):
    resultado = await db.execute(select(TabelaPrecoPaspatour))
    return resultado.scalars().all()

@router.post("/tabela-paspatour", response_model=RespostaTabelaPrecoPaspatour, status_code=status.HTTP_201_CREATED)
async def criar_preco_paspatour(obj_in: CriarTabelaPrecoPaspatour, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    db_obj = TabelaPrecoPaspatour(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.put("/tabela-paspatour/{preco_id}", response_model=RespostaTabelaPrecoPaspatour)
async def atualizar_preco_paspatour(preco_id: int, obj_in: AtualizarTabelaPrecoPaspatour, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(select(TabelaPrecoPaspatour).where(TabelaPrecoPaspatour.id == preco_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Preco nao encontrado")
    db_obj.preco_por_m2 = obj_in.preco_por_m2
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
