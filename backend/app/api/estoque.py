
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import obter_db
from app.models.estoque import Fundo, Moldura, Suplemento, Vidro
from app.schemas.estoque import (
    AtualizarFundo,
    AtualizarMoldura,
    AtualizarSuplemento,
    AtualizarVidro,
    CriarFundo,
    CriarMoldura,
    CriarSuplemento,
    CriarVidro,
    RespostaFundo,
    RespostaMoldura,
    RespostaSuplemento,
    RespostaVidro,
)
from app.services.autenticacao import obter_usuario_atual

router = APIRouter(prefix="/estoque", tags=["estoque"])

# --- MOLDURAS ---
@router.post("/molduras", response_model=RespostaMoldura, status_code=status.HTTP_201_CREATED)
async def criar_moldura(obj_in: CriarMoldura, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(select(Moldura).where(Moldura.codigo == obj_in.codigo))
    if resultado.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Já existe uma moldura com este código")

    db_obj = Moldura(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/molduras", response_model=list[RespostaMoldura])
async def listar_molduras(db: AsyncSession = Depends(obter_db)):
    resultado = await db.execute(select(Moldura))
    return resultado.scalars().all()

@router.put("/molduras/{item_id}", response_model=RespostaMoldura)
async def atualizar_moldura(item_id: int, obj_in: AtualizarMoldura, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
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
async def deletar_moldura(item_id: int, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(select(Moldura).where(Moldura.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Moldura não encontrada")

    await db.delete(db_obj)
    await db.commit()

# --- VIDROS ---
@router.post("/vidros", response_model=RespostaVidro, status_code=status.HTTP_201_CREATED)
async def criar_vidro(obj_in: CriarVidro, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    db_obj = Vidro(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/vidros", response_model=list[RespostaVidro])
async def listar_vidros(db: AsyncSession = Depends(obter_db)):
    resultado = await db.execute(select(Vidro))
    return resultado.scalars().all()

@router.get("/vidros/{item_id}", response_model=RespostaVidro)
async def obter_vidro(item_id: int, db: AsyncSession = Depends(obter_db)):
    resultado = await db.execute(select(Vidro).where(Vidro.id == item_id))
    obj = resultado.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Vidro não encontrado")
    return obj

@router.put("/vidros/{item_id}", response_model=RespostaVidro)
async def atualizar_vidro(item_id: int, obj_in: AtualizarVidro, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(select(Vidro).where(Vidro.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Vidro não encontrado")

    for campo, valor in obj_in.model_dump(exclude_unset=True).items():
        setattr(db_obj, campo, valor)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.delete("/vidros/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_vidro(item_id: int, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(select(Vidro).where(Vidro.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Vidro não encontrado")

    await db.delete(db_obj)
    await db.commit()

# --- FUNDOS ---
@router.post("/fundos", response_model=RespostaFundo, status_code=status.HTTP_201_CREATED)
async def criar_fundo(obj_in: CriarFundo, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    db_obj = Fundo(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/fundos", response_model=list[RespostaFundo])
async def listar_fundos(db: AsyncSession = Depends(obter_db)):
    resultado = await db.execute(select(Fundo))
    return resultado.scalars().all()

@router.get("/fundos/{item_id}", response_model=RespostaFundo)
async def obter_fundo(item_id: int, db: AsyncSession = Depends(obter_db)):
    resultado = await db.execute(select(Fundo).where(Fundo.id == item_id))
    obj = resultado.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Fundo não encontrado")
    return obj

@router.put("/fundos/{item_id}", response_model=RespostaFundo)
async def atualizar_fundo(item_id: int, obj_in: AtualizarFundo, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(select(Fundo).where(Fundo.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Fundo não encontrado")

    for campo, valor in obj_in.model_dump(exclude_unset=True).items():
        setattr(db_obj, campo, valor)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.delete("/fundos/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_fundo(item_id: int, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(select(Fundo).where(Fundo.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Fundo não encontrado")

    await db.delete(db_obj)
    await db.commit()

# --- SUPLEMENTOS ---
@router.post("/suplementos", response_model=RespostaSuplemento, status_code=status.HTTP_201_CREATED)
async def criar_suplemento(obj_in: CriarSuplemento, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    db_obj = Suplemento(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/suplementos", response_model=list[RespostaSuplemento])
async def listar_suplementos(db: AsyncSession = Depends(obter_db)):
    resultado = await db.execute(select(Suplemento))
    return resultado.scalars().all()

@router.put("/suplementos/{item_id}", response_model=RespostaSuplemento)
async def atualizar_suplemento(item_id: int, obj_in: AtualizarSuplemento, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
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
async def deletar_suplemento(item_id: int, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(select(Suplemento).where(Suplemento.id == item_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Suplemento não encontrado")

    await db.delete(db_obj)
    await db.commit()
