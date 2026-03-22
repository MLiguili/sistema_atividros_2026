import logging
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.estoque import Fundo, Moldura, Vidro
from app.models.pedido import Eixo, ItemPedido, Pedido, PedidoEvento, StatusFinanceiro, StatusGeral, StatusProducao
from app.schemas.pedido import CriarPedido

logger = logging.getLogger(__name__)

TRANSICOES_GERAIS = {
    "rascunho": ["confirmado", "cancelado"],
    "confirmado": ["entregue", "cancelado"],
    "entregue": ["arquivado"],
    "cancelado": [],
    "arquivado": [],
}

TRANSICOES_PRODUCAO = {
    "pendente": ["aguardando_material", "em_producao"],
    "aguardando_material": ["pendente", "em_producao"],
    "em_producao": ["pendente", "aguardando_material", "para_embalar"],
    "para_embalar": ["em_producao", "pronto_entrega"],
    "pronto_entrega": ["para_embalar", "entregue"],
    "entregue": ["pronto_entrega"],
}

TRANSICOES_FINANCEIRO = {
    "sem_pagamento": ["sinal_recebido", "estornado"],
    "sinal_recebido": ["pago_total", "estornado"],
    "pago_total": ["estornado"],
    "estornado": ["sem_pagamento"],
}

NUMERO_COUNTER = {"valor": 1}


def gerar_numero_pedido(db: AsyncSession) -> str:
    ano = 2026
    seq = NUMERO_COUNTER["valor"]
    NUMERO_COUNTER["valor"] += 1
    return f"{ano}{seq:05d}"


async def validar_transicao(eixo: Eixo, status_atual: str, novo_status: str) -> bool:
    if eixo == Eixo.geral:
        permitidas = TRANSICOES_GERAIS.get(status_atual, [])
    elif eixo == Eixo.producao:
        permitidas = TRANSICOES_PRODUCAO.get(status_atual, [])
    elif eixo == Eixo.financeiro:
        permitidas = TRANSICOES_FINANCEIRO.get(status_atual, [])
    else:
        return False
    return novo_status in permitidas


async def obter_detalhes_calculo(item: dict, db: AsyncSession) -> tuple:
    detalhes = []
    total = Decimal("0.0")

    if item.get("moldura_id"):
        resultado = await db.execute(select(Moldura).where(Moldura.id == item["moldura_id"]))
        obj = resultado.scalar_one_or_none()
        if obj:
            metragem = (Decimal(2) * (Decimal(str(item["largura"])) + Decimal(str(item["altura"])))) / Decimal("100")
            preco = (metragem * obj.preco_venda).quantize(Decimal("0.01"))
            detalhes.append({
                "tipo": "moldura",
                "nome": f"Moldura {obj.codigo} ({obj.cor})",
                "medida_calculada": float(metragem),
                "unidade": "m",
                "preco_estimado": float(preco)
            })
            total += preco

    if item.get("vidro_id"):
        resultado = await db.execute(select(Vidro).where(Vidro.id == item["vidro_id"]))
        obj = resultado.scalar_one_or_none()
        if obj:
            area = (Decimal(str(item["largura"])) * Decimal(str(item["altura"]))) / Decimal("10000")
            preco = (area * Decimal("100.0")).quantize(Decimal("0.01"))
            detalhes.append({
                "tipo": "vidro",
                "nome": f"Vidro {obj.tipo} {obj.espessura}mm",
                "medida_calculada": float(area),
                "unidade": "m2",
                "preco_estimado": float(preco)
            })
            total += preco

    if item.get("fundo_id"):
        resultado = await db.execute(select(Fundo).where(Fundo.id == item["fundo_id"]))
        obj = resultado.scalar_one_or_none()
        if obj:
            area = (Decimal(str(item["largura"])) * Decimal(str(item["altura"]))) / Decimal("10000")
            preco = (area * Decimal("30.0")).quantize(Decimal("0.01"))
            detalhes.append({
                "tipo": "fundo",
                "nome": f"Fundo {obj.tipo}",
                "medida_calculada": float(area),
                "unidade": "m2",
                "preco_estimado": float(preco)
            })
            total += preco

    return detalhes, total


async def criar_novo_pedido(dados: CriarPedido, db: AsyncSession) -> Pedido:
    numero = gerar_numero_pedido(db)
    logger.debug("Criando pedido %s para cliente %s", numero, dados.cliente_id)
    novo_pedido = Pedido(
        cliente_id=dados.cliente_id,
        numero_pedido=numero,
        status_geral=StatusGeral.rascunho,
        status_producao=StatusProducao.pendente,
        status_financeiro=StatusFinanceiro.sem_pagamento,
        valor_sinal=dados.valor_sinal,
        endereco_entrega=dados.endereco_entrega,
        frete=dados.frete
    )
    db.add(novo_pedido)
    await db.flush()

    total_pedido = Decimal("0.0")

    for item_in in dados.itens:
        if not item_in.descricao:
            item_dict = item_in.model_dump()
            _, preco_unit = await obter_detalhes_calculo(item_dict, db)
            desc_parts = []
            if item_dict.get("moldura_id"):
                desc_parts.append("Moldura")
            if item_dict.get("vidro_id"):
                desc_parts.append("Vidro")
            if item_dict.get("fundo_id"):
                desc_parts.append("Fundo")
            item_in.descricao = f"Quadro {item_dict['largura']}x{item_dict['altura']}cm"

        subtotal = item_in.preco_unitario * item_in.quantidade
        item_db = ItemPedido(
            pedido_id=novo_pedido.id,
            **item_in.model_dump(),
            subtotal=subtotal
        )
        db.add(item_db)
        total_pedido += subtotal

    novo_pedido.valor_total = total_pedido
    novo_pedido.saldo_devedor = total_pedido - novo_pedido.valor_sinal

    evento = PedidoEvento(
        pedido_id=novo_pedido.id,
        eixo=Eixo.geral,
        status_anterior=None,
        status_novo=StatusGeral.rascunho.value,
        observacao="Pedido criado"
    )
    db.add(evento)

    await db.commit()

    resultado = await db.execute(
        select(Pedido).where(Pedido.id == novo_pedido.id).options(
            selectinload(Pedido.itens),
            selectinload(Pedido.eventos)
        )
    )
    return resultado.scalar_one()


async def verificar_estoque_disponivel(pedido: Pedido, db: AsyncSession) -> dict:
    resultado = await db.execute(
        select(ItemPedido).where(ItemPedido.pedido_id == pedido.id).options(
            selectinload(ItemPedido.moldura),
            selectinload(ItemPedido.vidro),
            selectinload(ItemPedido.fundo)
        )
    )
    itens = resultado.scalars().all()

    faltando = []
    for item in itens:
        if item.moldura_id and item.moldura:
            if item.moldura.quantidade < item.quantidade:
                faltando.append(f"Moldura {item.moldura.codigo}: disponivel {item.moldura.quantidade}, necessario {item.quantidade}")
        if item.vidro_id and item.vidro:
            if item.vidro.quantidade < item.quantidade:
                faltando.append(f"Vidro {item.vidro.tipo}: disponivel {item.vidro.quantidade}, necessario {item.quantidade}")
        if item.fundo_id and item.fundo:
            if item.fundo.quantidade < item.quantidade:
                faltando.append(f"Fundo {item.fundo.tipo}: disponivel {item.fundo.quantidade}, necessario {item.quantidade}")

    return {"disponivel": len(faltando) == 0, "faltando": faltando}


async def realizar_baixa_estoque(pedido: Pedido, db: AsyncSession) -> dict:
    logger.debug("Realizando baixa de estoque para pedido %s", pedido.numero_pedido)
    resultado = await db.execute(
        select(ItemPedido).where(ItemPedido.pedido_id == pedido.id).options(
            selectinload(ItemPedido.moldura),
            selectinload(ItemPedido.vidro),
            selectinload(ItemPedido.fundo)
        )
    )
    itens = resultado.scalars().all()

    baixas = []
    for item in itens:
        if item.moldura_id and item.moldura:
            item.moldura.quantidade -= item.quantidade
            baixas.append(f"Moldura {item.moldura.codigo}: -{item.quantidade}")
            logger.debug("Baixa moldura %s: -%d (restante: %d)", item.moldura.codigo, item.quantidade, item.moldura.quantidade)
        if item.vidro_id and item.vidro:
            item.vidro.quantidade -= item.quantidade
            baixas.append(f"Vidro {item.vidro.tipo}: -{item.quantidade}")
            logger.debug("Baixa vidro %s: -%d (restante: %d)", item.vidro.tipo, item.quantidade, item.vidro.quantidade)
        if item.fundo_id and item.fundo:
            item.fundo.quantidade -= item.quantidade
            baixas.append(f"Fundo {item.fundo.tipo}: -{item.quantidade}")
            logger.debug("Baixa fundo %s: -%d (restante: %d)", item.fundo.tipo, item.quantidade, item.fundo.quantidade)

    observacao_baixa = "Baixa de estoque: " + ", ".join(baixas) if baixas else "Sem itens para baixa"

    pedido.status_producao = StatusProducao.em_producao

    evento = PedidoEvento(
        pedido_id=pedido.id,
        eixo=Eixo.producao,
        status_anterior=StatusProducao.pendente.value,
        status_novo=StatusProducao.em_producao.value,
        observacao=observacao_baixa
    )
    db.add(evento)

    await db.commit()
    await db.refresh(pedido)

    return {"baixas": baixas}


async def atualizar_status_pedido(pedido: Pedido, eixo: Eixo, novo_status: str, observacao: str, db: AsyncSession, valor_sinal: Decimal | None = None) -> Pedido:
    if pedido.status_geral == StatusGeral.cancelado and eixo != Eixo.geral:
        raise HTTPException(status_code=400, detail="Pedido cancelado. Eixos de producao e financeiro estao congelados.")

    if eixo == Eixo.geral:
        status_atual = pedido.status_geral.value
    elif eixo == Eixo.producao:
        status_atual = pedido.status_producao.value
    else:
        status_atual = pedido.status_financeiro.value

    logger.debug("Pedido %s: %s.%s -> %s", pedido.numero_pedido, eixo.value, status_atual, novo_status)

    if not await validar_transicao(eixo, status_atual, novo_status):
        raise HTTPException(status_code=400, detail=f"Transicao de '{status_atual}' para '{novo_status}' nao permitida no eixo {eixo.value}")

    if eixo == Eixo.geral:
        pedido.status_geral = StatusGeral(novo_status)
        if novo_status == "cancelado":
            if pedido.status_financeiro == StatusFinanceiro.sinal_recebido:
                pedido.status_financeiro = StatusFinanceiro.estornado
                pedido.valor_sinal = Decimal("0.00")
                pedido.saldo_devedor = pedido.valor_total
                evento_estorno = PedidoEvento(
                    pedido_id=pedido.id,
                    eixo=Eixo.financeiro,
                    status_anterior=StatusFinanceiro.sinal_recebido.value,
                    status_novo=StatusFinanceiro.estornado.value,
                    observacao="Estorno automatico por cancelamento do pedido"
                )
                db.add(evento_estorno)
    elif eixo == Eixo.producao:
        pedido.status_producao = StatusProducao(novo_status)
    else:
        if novo_status == "sinal_recebido" and valor_sinal is not None:
            if valor_sinal > pedido.valor_total:
                raise HTTPException(status_code=400, detail="Valor do sinal nao pode exceder o total do pedido.")
            if valor_sinal < Decimal("0"):
                raise HTTPException(status_code=400, detail="Valor do sinal nao pode ser negativo.")
            pedido.valor_sinal = valor_sinal
            observacao = f"Sinal de R$ {valor_sinal:.2f}"
        elif novo_status == "sinal_recebido" and valor_sinal is None:
            raise HTTPException(status_code=400, detail="Valor do sinal e obrigatorio ao receber sinal.")
        pedido.status_financeiro = StatusFinanceiro(novo_status)
        if novo_status == "sinal_recebido":
            pedido.saldo_devedor = pedido.valor_total - pedido.valor_sinal
            if pedido.status_geral == StatusGeral.rascunho:
                pedido.status_geral = StatusGeral.confirmado
                evento_geral = PedidoEvento(
                    pedido_id=pedido.id,
                    eixo=Eixo.geral,
                    status_anterior="rascunho",
                    status_novo="confirmado",
                    observacao="Confirmado automaticamente ao receber sinal"
                )
                db.add(evento_geral)
        elif novo_status == "pago_total":
            pedido.saldo_devedor = Decimal("0.00")

    evento = PedidoEvento(
        pedido_id=pedido.id,
        eixo=eixo,
        status_anterior=status_atual,
        status_novo=novo_status,
        observacao=observacao
    )
    db.add(evento)

    await db.commit()
    await db.refresh(pedido)

    resultado = await db.execute(
        select(Pedido).where(Pedido.id == pedido.id).options(
            selectinload(Pedido.itens),
            selectinload(Pedido.eventos)
        )
    )
    return resultado.scalar_one()
