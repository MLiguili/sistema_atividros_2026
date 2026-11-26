from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import obter_db
from app.models.tabela_preco import TabelaPrecoFundo, TabelaPrecoPaspatour, TabelaPrecoVidro
from app.schemas.calculadora import EntradaCalculoQuadro, EntradaCalculoVidroAvulso, ResultadoCalculoQuadro
from app.schemas.tabela_preco import (
    AtualizarTabelaPrecoFundo,
    AtualizarTabelaPrecoPaspatour,
    AtualizarTabelaPrecoVidro,
    CriarTabelaPrecoFundo,
    CriarTabelaPrecoPaspatour,
    CriarTabelaPrecoVidro,
    RespostaTabelaPrecoFundo,
    RespostaTabelaPrecoPaspatour,
    RespostaTabelaPrecoVidro,
)
from app.services.autenticacao import obter_usuario_atual
from app.services.calculadora import calcular_quadro, calcular_vidro_avulso

router = APIRouter(prefix="/calculadora", tags=["calculadora"])


@router.post("/quadro", response_model=ResultadoCalculoQuadro)
async def calcular_quadro_avancado(
    dados: EntradaCalculoQuadro,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Calcula dimensões propagadas, consumos e preço sugerido para um quadro sob medida.
    """
    return await calcular_quadro(dados, db)


@router.post("/vidro-avulso", response_model=ResultadoCalculoQuadro)
async def calcular_vidro_avulso_endpoint(
    dados: EntradaCalculoVidroAvulso,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Calcula área real, área mínima comercial e preço sugerido para corte avulso de vidro ou espelho.
    """
    return await calcular_vidro_avulso(dados, db)


# --- Tabela de Preços de Vidro ---
@router.get("/tabela-vidro", response_model=list[RespostaTabelaPrecoVidro])
async def listar_tabela_vidro(db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Lista todas as faixas de preço por m² e área mínima de vidros/espelhos.
    """
    resultado = await db.execute(select(TabelaPrecoVidro).order_by(TabelaPrecoVidro.tipo))
    return resultado.scalars().all()


@router.post("/tabela-vidro", response_model=RespostaTabelaPrecoVidro, status_code=status.HTTP_201_CREATED)
async def criar_preco_vidro(
    obj_in: CriarTabelaPrecoVidro,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Cria um registro na tabela de preços de vidro por m².
    """
    tipo_norm = obj_in.tipo.strip().lower()
    existente = await db.execute(select(TabelaPrecoVidro).where(func.lower(TabelaPrecoVidro.tipo) == tipo_norm))
    if existente.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Já existe preço cadastrado para este tipo de vidro")

    dados = obj_in.model_dump()
    dados["tipo"] = tipo_norm
    db_obj = TabelaPrecoVidro(**dados)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.put("/tabela-vidro/{preco_id}", response_model=RespostaTabelaPrecoVidro)
async def atualizar_preco_vidro(
    preco_id: int,
    obj_in: AtualizarTabelaPrecoVidro,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Atualiza preço por m², área mínima ou descrição de um tipo de vidro.
    """
    resultado = await db.execute(select(TabelaPrecoVidro).where(TabelaPrecoVidro.id == preco_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Preço de vidro não encontrado")

    db_obj.preco_por_m2 = obj_in.preco_por_m2
    if obj_in.area_minima_m2 is not None:
        db_obj.area_minima_m2 = obj_in.area_minima_m2
    if obj_in.descricao is not None:
        db_obj.descricao = obj_in.descricao
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.delete("/tabela-vidro/{preco_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_preco_vidro(
    preco_id: int,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Remove uma entrada da tabela de preços de vidro.
    """
    resultado = await db.execute(select(TabelaPrecoVidro).where(TabelaPrecoVidro.id == preco_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Preço de vidro não encontrado")

    await db.delete(db_obj)
    await db.commit()


# --- Tabela de Preços de Fundo ---
@router.get("/tabela-fundo", response_model=list[RespostaTabelaPrecoFundo])
async def listar_tabela_fundo(db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Lista todas as faixas de preço por m² cadastradas para fundos.
    """
    resultado = await db.execute(select(TabelaPrecoFundo).order_by(TabelaPrecoFundo.tipo))
    return resultado.scalars().all()


@router.post("/tabela-fundo", response_model=RespostaTabelaPrecoFundo, status_code=status.HTTP_201_CREATED)
async def criar_preco_fundo(
    obj_in: CriarTabelaPrecoFundo,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Cria um registro na tabela de preços de fundo por m².
    """
    tipo_limpo = obj_in.tipo.strip()
    existente = await db.execute(
        select(TabelaPrecoFundo).where(func.lower(TabelaPrecoFundo.tipo) == tipo_limpo.lower())
    )
    if existente.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Já existe preço cadastrado para este tipo de fundo")

    dados = obj_in.model_dump()
    dados["tipo"] = tipo_limpo
    db_obj = TabelaPrecoFundo(**dados)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.put("/tabela-fundo/{preco_id}", response_model=RespostaTabelaPrecoFundo)
async def atualizar_preco_fundo(
    preco_id: int,
    obj_in: AtualizarTabelaPrecoFundo,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Atualiza um registro da tabela de preços de fundo.
    """
    resultado = await db.execute(select(TabelaPrecoFundo).where(TabelaPrecoFundo.id == preco_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Preço de fundo não encontrado")

    if obj_in.tipo is not None:
        tipo_limpo = obj_in.tipo.strip()
        if tipo_limpo.lower() != db_obj.tipo.lower():
            dup = await db.execute(
                select(TabelaPrecoFundo).where(func.lower(TabelaPrecoFundo.tipo) == tipo_limpo.lower())
            )
            if dup.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Já existe preço cadastrado para este tipo de fundo")
        db_obj.tipo = tipo_limpo

    db_obj.preco_por_m2 = obj_in.preco_por_m2
    if obj_in.descricao is not None:
        db_obj.descricao = obj_in.descricao
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.delete("/tabela-fundo/{preco_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_preco_fundo(
    preco_id: int,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Remove uma entrada da tabela de preços de fundo.
    """
    resultado = await db.execute(select(TabelaPrecoFundo).where(TabelaPrecoFundo.id == preco_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Preço de fundo não encontrado")

    await db.delete(db_obj)
    await db.commit()


# --- Tabela de Preços de Paspatour ---
@router.get("/tabela-paspatour", response_model=list[RespostaTabelaPrecoPaspatour])
async def listar_tabela_paspatour(db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Lista todas as opções de paspatour cadastradas com preço por m².
    """
    resultado = await db.execute(select(TabelaPrecoPaspatour).order_by(TabelaPrecoPaspatour.descricao))
    return resultado.scalars().all()


@router.post("/tabela-paspatour", response_model=RespostaTabelaPrecoPaspatour, status_code=status.HTTP_201_CREATED)
async def criar_preco_paspatour(
    obj_in: CriarTabelaPrecoPaspatour,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Cria uma nova opção na tabela de preços de paspatour.
    """
    desc_limpa = obj_in.descricao.strip()
    existente = await db.execute(
        select(TabelaPrecoPaspatour).where(func.lower(TabelaPrecoPaspatour.descricao) == desc_limpa.lower())
    )
    if existente.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Já existe paspatour cadastrado com esta descrição")

    db_obj = TabelaPrecoPaspatour(descricao=desc_limpa, preco_por_m2=obj_in.preco_por_m2)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.put("/tabela-paspatour/{preco_id}", response_model=RespostaTabelaPrecoPaspatour)
async def atualizar_preco_paspatour(
    preco_id: int,
    obj_in: AtualizarTabelaPrecoPaspatour,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Atualiza descrição ou preço por m² de uma opção de paspatour.
    """
    resultado = await db.execute(select(TabelaPrecoPaspatour).where(TabelaPrecoPaspatour.id == preco_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Preço de paspatour não encontrado")

    if obj_in.descricao is not None:
        desc_limpa = obj_in.descricao.strip()
        if desc_limpa.lower() != db_obj.descricao.lower():
            dup = await db.execute(
                select(TabelaPrecoPaspatour).where(func.lower(TabelaPrecoPaspatour.descricao) == desc_limpa.lower())
            )
            if dup.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Já existe paspatour cadastrado com esta descrição")
        db_obj.descricao = desc_limpa

    db_obj.preco_por_m2 = obj_in.preco_por_m2
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.delete("/tabela-paspatour/{preco_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_preco_paspatour(
    preco_id: int,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Remove uma opção da tabela de preços de paspatour.
    """
    resultado = await db.execute(select(TabelaPrecoPaspatour).where(TabelaPrecoPaspatour.id == preco_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Preço de paspatour não encontrado")

    await db.delete(db_obj)
    await db.commit()
