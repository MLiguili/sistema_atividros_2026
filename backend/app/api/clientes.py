
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import obter_db
from app.models.cliente import Cliente
from app.schemas.cliente import AtualizarCliente, CriarCliente, RespostaCliente
from app.services.autenticacao import obter_usuario_atual

router = APIRouter(prefix="/clientes", tags=["clientes"])

@router.get("/", response_model=list[RespostaCliente])
async def listar_clientes(db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(select(Cliente))
    return resultado.scalars().all()

@router.post("/", response_model=RespostaCliente, status_code=status.HTTP_201_CREATED)
async def criar_cliente(obj_in: CriarCliente, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    db_obj = Cliente(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/{cliente_id}", response_model=RespostaCliente)
async def obter_cliente(cliente_id: int, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    obj = resultado.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return obj

@router.put("/{cliente_id}", response_model=RespostaCliente)
async def atualizar_cliente(cliente_id: int, obj_in: AtualizarCliente, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    dados_atualizacao = obj_in.model_dump(exclude_unset=True)
    for campo, valor in dados_atualizacao.items():
        setattr(db_obj, campo, valor)

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_cliente(cliente_id: int, db: AsyncSession = Depends(obter_db), _ = Depends(obter_usuario_atual)):
    resultado = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    await db.delete(db_obj)
    await db.commit()
