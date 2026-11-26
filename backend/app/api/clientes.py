from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import obter_db
from app.models.cliente import Cliente
from app.models.pedido import Pedido
from app.schemas.cliente import AtualizarCliente, CriarCliente, RespostaCliente
from app.schemas.pedido import RespostaPedidoResumo
from app.services.autenticacao import obter_usuario_atual

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("/", response_model=list[RespostaCliente])
async def listar_clientes(
    q: str | None = Query(default=None, description="Busca por nome, sobrenome, telefone ou e-mail"),
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Lista clientes cadastrados com filtro opcional case-insensitive no servidor.
    """
    stmt = select(Cliente)
    if q and q.strip():
        termo = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Cliente.nome).like(termo),
                func.lower(Cliente.sobrenome).like(termo),
                func.lower(Cliente.telefone).like(termo),
                func.lower(func.coalesce(Cliente.email, "")).like(termo),
            )
        )
    stmt = stmt.order_by(Cliente.nome.asc(), Cliente.sobrenome.asc())
    resultado = await db.execute(stmt)
    return resultado.scalars().all()


@router.post("/", response_model=RespostaCliente, status_code=status.HTTP_201_CREATED)
async def criar_cliente(obj_in: CriarCliente, db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Cadastra um novo cliente na base.
    """
    db_obj = Cliente(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


@router.get("/{cliente_id}", response_model=RespostaCliente)
async def obter_cliente(cliente_id: int, db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Obtém os dados cadastrais de um cliente pelo ID.
    """
    resultado = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    obj = resultado.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return obj


@router.get("/{cliente_id}/pedidos", response_model=list[RespostaPedidoResumo])
async def listar_pedidos_cliente(
    cliente_id: int,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Retorna o histórico resumido de pedidos de um cliente ordenado do mais recente ao mais antigo.
    """
    cliente_res = await db.execute(select(Cliente.id).where(Cliente.id == cliente_id))
    if cliente_res.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    resultado = await db.execute(
        select(Pedido).where(Pedido.cliente_id == cliente_id).order_by(Pedido.criado_em.desc())
    )
    return resultado.scalars().all()


@router.put("/{cliente_id}", response_model=RespostaCliente)
async def atualizar_cliente(
    cliente_id: int,
    obj_in: AtualizarCliente,
    db: AsyncSession = Depends(obter_db),
    _=Depends(obter_usuario_atual),
):
    """
    Atualiza dados cadastrais de um cliente existente.
    """
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
async def deletar_cliente(cliente_id: int, db: AsyncSession = Depends(obter_db), _=Depends(obter_usuario_atual)):
    """
    Exclui um cliente caso não possua pedidos vinculados (409 Conflict caso contrário).
    """
    resultado = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
    db_obj = resultado.scalar_one_or_none()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    vinculo = await db.execute(select(Pedido.id).where(Pedido.cliente_id == cliente_id).limit(1))
    if vinculo.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Cliente possui pedidos vinculados e não pode ser excluído",
        )

    try:
        await db.delete(db_obj)
        await db.commit()
    except IntegrityError as erro:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Cliente possui pedidos vinculados e não pode ser excluído",
        ) from erro
