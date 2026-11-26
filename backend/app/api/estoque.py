import logging
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import obter_db
from app.models.estoque import Fundo, Moldura, Suplemento, Vidro
from app.models.pedido import ItemPedido, ItemPedidoMoldura
from app.schemas.estoque import (
    AjusteAreaM2,
    AtualizarFundo,
    AtualizarMoldura,
    AtualizarSuplemento,
    AtualizarVidro,
    CriarFundo,
    CriarMoldura,
    CriarSuplemento,
    CriarVidro,
    EntradaChapas,
    RespostaEntradaChapas,
    RespostaFundo,
    RespostaMoldura,
    RespostaSuplemento,
    RespostaVidro,
)
from app.services.autenticacao import obter_usuario_atual

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/estoque", tags=["estoque"])

QUATRO_CASAS = Decimal("0.0001")


def calcular_area_chapas_m2(quantidade_chapas: int, largura_cm: Decimal, altura_cm: Decimal) -> Decimal:
    """
    Converte quantidade e dimensões de chapas em centímetros para metros quadrados (4 casas).
    """
    area = (Decimal(quantidade_chapas) * largura_cm * altura_cm) / Decimal("10000")
    return area.quantize(QUATRO_CASAS, rounding=ROUND_HALF_UP)


# --- MOLDURAS ---
@router.post("/molduras", response_model=RespostaMoldura, status_code=status.HTTP_201_CREATED)
async def criar_moldura(obj_in: CriarMoldura, db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Cadastra uma nova moldura no estoque com preços em R$/m.
    """
    resultado = await db.execute(select(Moldura).where(Moldura.codigo == obj_in.codigo))
    if resultado.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Já existe uma moldura com este código")

    db_obj = Moldura(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.get("/molduras", response_model=list[RespostaMoldura])
async def listar_molduras(
    q: str | None = Query(default=None, description="Filtro por código, cor ou marca"),
    critico: bool = Query(default=False, description="Quando true, retorna apenas molduras abaixo ou no mínimo"),
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Lista molduras cadastradas com suporte a filtro textual e estoque crítico.
    """
    stmt = select(Moldura)
    if q and q.strip():
        termo = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Moldura.codigo).like(termo),
                func.lower(Moldura.cor).like(termo),
                func.lower(func.coalesce(Moldura.marca, "")).like(termo),
            )
        )
    if critico:
        stmt = stmt.where(Moldura.quantidade <= Moldura.estoque_minimo).order_by(Moldura.quantidade.asc())
    else:
        stmt = stmt.order_by(Moldura.codigo.asc())

    resultado = await db.execute(stmt)
    return resultado.scalars().all()


@router.put("/molduras/{item_id}", response_model=RespostaMoldura)
async def atualizar_moldura(
    item_id: int,
    obj_in: AtualizarMoldura,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Atualiza dados ou saldo de barras de uma moldura existente.
    """
    resultado = await db.execute(select(Moldura).where(Moldura.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Moldura não encontrada")

    if obj_in.codigo and obj_in.codigo != db_obj.codigo:
        existe = await db.execute(select(Moldura).where(Moldura.codigo == obj_in.codigo))
        if existe.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Já existe uma moldura com este código")

    for campo, valor in obj_in.model_dump(exclude_unset=True).items():
        setattr(db_obj, campo, valor)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.delete("/molduras/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_moldura(item_id: int, db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Exclui uma moldura caso não esteja vinculada a nenhum item de pedido.
    """
    resultado = await db.execute(select(Moldura).where(Moldura.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Moldura não encontrada")

    vinculo = await db.execute(
        select(ItemPedidoMoldura.id).where(ItemPedidoMoldura.moldura_id == item_id).limit(1)
    )
    if vinculo.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Moldura vinculada a itens de pedido não pode ser excluída",
        )

    try:
        await db.delete(db_obj)
        await db.commit()
    except IntegrityError as erro:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Moldura vinculada a itens de pedido não pode ser excluída",
        ) from erro


# --- VIDROS ---
@router.post("/vidros", response_model=RespostaVidro, status_code=status.HTTP_201_CREATED)
async def criar_vidro(obj_in: CriarVidro, db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Cadastra um tipo/espessura de vidro com saldo contínuo em m².
    """
    dados = obj_in.model_dump()
    dados["area_disponivel_m2"] = Decimal(str(dados["area_disponivel_m2"])).quantize(
        QUATRO_CASAS, rounding=ROUND_HALF_UP
    )
    dados["estoque_minimo_m2"] = Decimal(str(dados["estoque_minimo_m2"])).quantize(
        QUATRO_CASAS, rounding=ROUND_HALF_UP
    )
    db_obj = Vidro(**dados)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.get("/vidros", response_model=list[RespostaVidro])
async def listar_vidros(
    q: str | None = Query(default=None, description="Filtro por tipo ou cor"),
    critico: bool = Query(default=False, description="Quando true, retorna apenas vidros em estoque crítico"),
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Lista vidros cadastrados com suporte a filtro textual e estoque crítico em m².
    """
    stmt = select(Vidro)
    if q and q.strip():
        termo = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(cast(Vidro.tipo, String)).like(termo),
                func.lower(func.coalesce(Vidro.cor, "")).like(termo),
            )
        )
    if critico:
        stmt = stmt.where(Vidro.area_disponivel_m2 <= Vidro.estoque_minimo_m2).order_by(
            Vidro.area_disponivel_m2.asc()
        )
    else:
        stmt = stmt.order_by(Vidro.tipo.asc(), Vidro.espessura.asc())

    resultado = await db.execute(stmt)
    return resultado.scalars().all()


@router.get("/vidros/{item_id}", response_model=RespostaVidro)
async def obter_vidro(item_id: int, db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Obtém um vidro específico pelo ID.
    """
    resultado = await db.execute(select(Vidro).where(Vidro.id == item_id))
    obj = resultado.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Vidro não encontrado")
    return obj


@router.put("/vidros/{item_id}", response_model=RespostaVidro)
async def atualizar_vidro(
    item_id: int,
    obj_in: AtualizarVidro,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Atualiza os atributos cadastrais ou saldo de um vidro.
    """
    resultado = await db.execute(select(Vidro).where(Vidro.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Vidro não encontrado")

    for campo, valor in obj_in.model_dump(exclude_unset=True).items():
        if campo in ("area_disponivel_m2", "estoque_minimo_m2") and valor is not None:
            valor = Decimal(str(valor)).quantize(QUATRO_CASAS, rounding=ROUND_HALF_UP)
        setattr(db_obj, campo, valor)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.post("/vidros/{item_id}/entrada-chapas", response_model=RespostaEntradaChapas)
async def entrada_chapas_vidro(
    item_id: int,
    dados: EntradaChapas,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Converte chapas físicas (qtd × L × A / 10000) em m² e soma ao saldo do vidro.
    """
    resultado = await db.execute(select(Vidro).where(Vidro.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Vidro não encontrado")

    area_adicionada = calcular_area_chapas_m2(dados.quantidade_chapas, dados.largura_cm, dados.altura_cm)
    db_obj.area_disponivel_m2 = (
        Decimal(str(db_obj.area_disponivel_m2)) + area_adicionada
    ).quantize(QUATRO_CASAS, rounding=ROUND_HALF_UP)

    logger.info(
        "Entrada de chapas vidro id=%s: +%s m2 (%s chapas %sx%scm) -> saldo=%s m2",
        db_obj.id,
        area_adicionada,
        dados.quantidade_chapas,
        dados.largura_cm,
        dados.altura_cm,
        db_obj.area_disponivel_m2,
    )
    await db.commit()
    await db.refresh(db_obj)

    return RespostaEntradaChapas(
        id=db_obj.id,
        area_adicionada_m2=area_adicionada,
        area_disponivel_m2=db_obj.area_disponivel_m2,
    )


@router.post("/vidros/{item_id}/ajuste-m2", response_model=RespostaVidro)
async def ajuste_m2_vidro(
    item_id: int,
    dados: AjusteAreaM2,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Ajusta manualmente o saldo disponível em m² de um vidro para conferência de inventário.
    """
    resultado = await db.execute(select(Vidro).where(Vidro.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Vidro não encontrado")

    saldo_anterior = db_obj.area_disponivel_m2
    db_obj.area_disponivel_m2 = dados.nova_area_m2.quantize(QUATRO_CASAS, rounding=ROUND_HALF_UP)

    logger.info(
        "Ajuste manual vidro id=%s: %s -> %s m2 (motivo=%s)",
        db_obj.id,
        saldo_anterior,
        db_obj.area_disponivel_m2,
        dados.motivo or "-",
    )
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.delete("/vidros/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_vidro(item_id: int, db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Exclui um vidro caso não esteja vinculado a nenhum item de pedido.
    """
    resultado = await db.execute(select(Vidro).where(Vidro.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Vidro não encontrado")

    vinculo = await db.execute(select(ItemPedido.id).where(ItemPedido.vidro_id == item_id).limit(1))
    if vinculo.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Vidro vinculado a itens de pedido não pode ser excluído")

    try:
        await db.delete(db_obj)
        await db.commit()
    except IntegrityError as erro:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Vidro vinculado a itens de pedido não pode ser excluído",
        ) from erro


# --- FUNDOS ---
@router.post("/fundos", response_model=RespostaFundo, status_code=status.HTTP_201_CREATED)
async def criar_fundo(obj_in: CriarFundo, db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Cadastra um tipo/espessura de fundo com saldo contínuo em m².
    """
    dados = obj_in.model_dump()
    dados["area_disponivel_m2"] = Decimal(str(dados["area_disponivel_m2"])).quantize(
        QUATRO_CASAS, rounding=ROUND_HALF_UP
    )
    dados["estoque_minimo_m2"] = Decimal(str(dados["estoque_minimo_m2"])).quantize(
        QUATRO_CASAS, rounding=ROUND_HALF_UP
    )
    db_obj = Fundo(**dados)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.get("/fundos", response_model=list[RespostaFundo])
async def listar_fundos(
    q: str | None = Query(default=None, description="Filtro por tipo ou cor"),
    critico: bool = Query(default=False, description="Quando true, retorna apenas fundos em estoque crítico"),
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Lista fundos cadastrados com suporte a filtro textual e estoque crítico em m².
    """
    stmt = select(Fundo)
    if q and q.strip():
        termo = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Fundo.tipo).like(termo),
                func.lower(func.coalesce(Fundo.cor, "")).like(termo),
            )
        )
    if critico:
        stmt = stmt.where(Fundo.area_disponivel_m2 <= Fundo.estoque_minimo_m2).order_by(
            Fundo.area_disponivel_m2.asc()
        )
    else:
        stmt = stmt.order_by(Fundo.tipo.asc(), Fundo.espessura.asc())

    resultado = await db.execute(stmt)
    return resultado.scalars().all()


@router.get("/fundos/{item_id}", response_model=RespostaFundo)
async def obter_fundo(item_id: int, db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Obtém um fundo específico pelo ID.
    """
    resultado = await db.execute(select(Fundo).where(Fundo.id == item_id))
    obj = resultado.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Fundo não encontrado")
    return obj


@router.put("/fundos/{item_id}", response_model=RespostaFundo)
async def atualizar_fundo(
    item_id: int,
    obj_in: AtualizarFundo,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Atualiza os atributos cadastrais ou saldo de um fundo.
    """
    resultado = await db.execute(select(Fundo).where(Fundo.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Fundo não encontrado")

    for campo, valor in obj_in.model_dump(exclude_unset=True).items():
        if campo in ("area_disponivel_m2", "estoque_minimo_m2") and valor is not None:
            valor = Decimal(str(valor)).quantize(QUATRO_CASAS, rounding=ROUND_HALF_UP)
        setattr(db_obj, campo, valor)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.post("/fundos/{item_id}/entrada-chapas", response_model=RespostaEntradaChapas)
async def entrada_chapas_fundo(
    item_id: int,
    dados: EntradaChapas,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Converte chapas físicas de fundo em m² e soma ao saldo disponível.
    """
    resultado = await db.execute(select(Fundo).where(Fundo.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Fundo não encontrado")

    area_adicionada = calcular_area_chapas_m2(dados.quantidade_chapas, dados.largura_cm, dados.altura_cm)
    db_obj.area_disponivel_m2 = (
        Decimal(str(db_obj.area_disponivel_m2)) + area_adicionada
    ).quantize(QUATRO_CASAS, rounding=ROUND_HALF_UP)

    logger.info(
        "Entrada de chapas fundo id=%s: +%s m2 (%s chapas %sx%scm) -> saldo=%s m2",
        db_obj.id,
        area_adicionada,
        dados.quantidade_chapas,
        dados.largura_cm,
        dados.altura_cm,
        db_obj.area_disponivel_m2,
    )
    await db.commit()
    await db.refresh(db_obj)

    return RespostaEntradaChapas(
        id=db_obj.id,
        area_adicionada_m2=area_adicionada,
        area_disponivel_m2=db_obj.area_disponivel_m2,
    )


@router.post("/fundos/{item_id}/ajuste-m2", response_model=RespostaFundo)
async def ajuste_m2_fundo(
    item_id: int,
    dados: AjusteAreaM2,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Ajusta manualmente o saldo disponível em m² de um fundo para inventário.
    """
    resultado = await db.execute(select(Fundo).where(Fundo.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Fundo não encontrado")

    saldo_anterior = db_obj.area_disponivel_m2
    db_obj.area_disponivel_m2 = dados.nova_area_m2.quantize(QUATRO_CASAS, rounding=ROUND_HALF_UP)

    logger.info(
        "Ajuste manual fundo id=%s: %s -> %s m2 (motivo=%s)",
        db_obj.id,
        saldo_anterior,
        db_obj.area_disponivel_m2,
        dados.motivo or "-",
    )
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.delete("/fundos/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_fundo(item_id: int, db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Exclui um fundo caso não esteja vinculado a nenhum item de pedido.
    """
    resultado = await db.execute(select(Fundo).where(Fundo.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Fundo não encontrado")

    vinculo = await db.execute(select(ItemPedido.id).where(ItemPedido.fundo_id == item_id).limit(1))
    if vinculo.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Fundo vinculado a itens de pedido não pode ser excluído")

    try:
        await db.delete(db_obj)
        await db.commit()
    except IntegrityError as erro:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Fundo vinculado a itens de pedido não pode ser excluído",
        ) from erro


# --- SUPLEMENTOS ---
@router.post("/suplementos", response_model=RespostaSuplemento, status_code=status.HTTP_201_CREATED)
async def criar_suplemento(
    obj_in: CriarSuplemento,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Cadastra um suplemento de controle manual.
    """
    existente = await db.execute(
        select(Suplemento).where(func.lower(Suplemento.nome) == obj_in.nome.strip().lower())
    )
    if existente.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Já existe um suplemento com este nome")

    db_obj = Suplemento(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.get("/suplementos", response_model=list[RespostaSuplemento])
async def listar_suplementos(db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Lista todos os suplementos cadastrados no estoque.
    """
    resultado = await db.execute(select(Suplemento).order_by(Suplemento.nome.asc()))
    return resultado.scalars().all()


@router.put("/suplementos/{item_id}", response_model=RespostaSuplemento)
async def atualizar_suplemento(
    item_id: int,
    obj_in: AtualizarSuplemento,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Atualiza dados ou quantidade de um suplemento manual.
    """
    resultado = await db.execute(select(Suplemento).where(Suplemento.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Suplemento não encontrado")

    for campo, valor in obj_in.model_dump(exclude_unset=True).items():
        setattr(db_obj, campo, valor)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.delete("/suplementos/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_suplemento(item_id: int, db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Remove um suplemento do estoque.
    """
    resultado = await db.execute(select(Suplemento).where(Suplemento.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Suplemento não encontrado")

    await db.delete(db_obj)
    await db.commit()
