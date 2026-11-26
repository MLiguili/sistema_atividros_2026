import logging
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cliente import Cliente
from app.models.estoque import Fundo, Moldura, TipoVidro, Vidro
from app.models.pedido import (
    Eixo,
    ItemPedido,
    ItemPedidoMoldura,
    PagamentoPedido,
    Pedido,
    PedidoEvento,
    StatusFinanceiro,
    StatusGeral,
    StatusProducao,
    TipoDesconto,
    TipoItemPedido,
)
from app.schemas.calculadora import EntradaCalculoQuadro, EntradaCalculoVidroAvulso, MolduraEntrada
from app.schemas.pedido import (
    ConfirmarBaixaEstoque,
    CriarItemPedido,
    CriarPagamentoPedido,
    CriarPedido,
    MaterialBaixado,
    PrevisaoArea,
    PrevisaoMoldura,
    RespostaPrevisaoBaixa,
)
from app.services.calculadora import arredondar_2, arredondar_4, calcular_quadro, calcular_vidro_avulso
from app.services.sequencia import gerar_numero_pedido

logger = logging.getLogger(__name__)

TRANSICOES_GERAIS: dict[str, list[str]] = {
    StatusGeral.rascunho.value: [StatusGeral.confirmado.value, StatusGeral.cancelado.value],
    StatusGeral.confirmado.value: [StatusGeral.entregue.value, StatusGeral.cancelado.value],
    StatusGeral.entregue.value: [StatusGeral.arquivado.value],
    StatusGeral.cancelado.value: [],
    StatusGeral.arquivado.value: [],
}

TRANSICOES_PRODUCAO: dict[str, list[str]] = {
    StatusProducao.pendente.value: [StatusProducao.aguardando_material.value, StatusProducao.na_fila.value],
    StatusProducao.aguardando_material.value: [StatusProducao.pendente.value, StatusProducao.na_fila.value],
    StatusProducao.na_fila.value: [StatusProducao.pendente.value, StatusProducao.aguardando_material.value],
    StatusProducao.em_producao.value: [StatusProducao.embalando.value],
    StatusProducao.embalando.value: [StatusProducao.em_producao.value, StatusProducao.pronto_entrega.value],
    StatusProducao.pronto_entrega.value: [StatusProducao.embalando.value],
}

ESTAGIOS_PRE_PRODUCAO = {
    StatusProducao.pendente.value,
    StatusProducao.aguardando_material.value,
    StatusProducao.na_fila.value,
}


def calcular_totais_pedido(
    subtotal_itens: Decimal,
    frete: Decimal,
    desconto_valor: Decimal,
    desconto_tipo: TipoDesconto,
    valor_pago: Decimal = Decimal("0.00"),
) -> tuple[Decimal, Decimal, Decimal]:
    """
    Calcula (desconto_calculado, valor_total, saldo_devedor) exclusivamente em Decimal no backend.
    """
    sub = arredondar_2(subtotal_itens)
    frete_val = arredondar_2(frete)
    desc_in = Decimal(str(desconto_valor))

    if desconto_tipo == TipoDesconto.percentual:
        desconto_calc = ((sub * desc_in) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        desconto_calc = arredondar_2(desc_in)

    valor_total = max(Decimal("0.00"), arredondar_2(sub + frete_val - desconto_calc))
    pago = arredondar_2(valor_pago)
    saldo_devedor = max(Decimal("0.00"), arredondar_2(valor_total - pago))
    return desconto_calc, valor_total, saldo_devedor


def recalcular_totais_e_status_financeiro(
    pedido: Pedido,
    itens: list[ItemPedido] | None = None,
    pagamentos: list[PagamentoPedido] | None = None,
) -> None:
    """
    Atualiza subtotal_itens, valor_total, valor_pago, saldo_devedor e deriva status_financeiro.
    """
    lista_itens = itens if itens is not None else list(pedido.itens)
    lista_pagamentos = pagamentos if pagamentos is not None else list(pedido.pagamentos or [])
    subtotal_itens = sum((Decimal(str(item.subtotal)) for item in lista_itens), Decimal("0.00"))
    valor_pago = sum(
        (Decimal(str(p.valor)) for p in lista_pagamentos if not p.estornado),
        Decimal("0.00"),
    )

    _, valor_total, saldo_devedor = calcular_totais_pedido(
        subtotal_itens=subtotal_itens,
        frete=Decimal(str(pedido.frete)),
        desconto_valor=Decimal(str(pedido.desconto_valor)),
        desconto_tipo=pedido.desconto_tipo,
        valor_pago=valor_pago,
    )

    pedido.subtotal_itens = arredondar_2(subtotal_itens)
    pedido.valor_total = valor_total
    pedido.valor_pago = arredondar_2(valor_pago)
    pedido.saldo_devedor = saldo_devedor

    if len(lista_pagamentos) > 0 and pedido.valor_pago == Decimal("0.00"):
        pedido.status_financeiro = StatusFinanceiro.estornado
    elif pedido.valor_pago > Decimal("0.00"):
        if pedido.valor_pago >= pedido.valor_total:
            pedido.status_financeiro = StatusFinanceiro.pago_total
        else:
            pedido.status_financeiro = StatusFinanceiro.pagamento_parcial
    else:
        if pedido.valor_total == Decimal("0.00") and pedido.status_geral in (
            StatusGeral.confirmado,
            StatusGeral.entregue,
            StatusGeral.arquivado,
        ):
            pedido.status_financeiro = StatusFinanceiro.pago_total
        else:
            pedido.status_financeiro = StatusFinanceiro.sem_pagamento


def validar_transicao(eixo: Eixo, status_atual: str, novo_status: str) -> bool:
    """
    Verifica se uma transição de status é permitida no eixo informado.
    """
    if eixo == Eixo.geral:
        return novo_status in TRANSICOES_GERAIS.get(status_atual, [])
    if eixo == Eixo.producao:
        return novo_status in TRANSICOES_PRODUCAO.get(status_atual, [])
    return False


def opcoes_carregamento_pedido():
    """
    Retorna as opções eager-load padrão para carregar um pedido completo com segurança assíncrona.
    """
    return (
        selectinload(Pedido.cliente),
        selectinload(Pedido.itens).selectinload(ItemPedido.molduras).selectinload(ItemPedidoMoldura.moldura),
        selectinload(Pedido.itens).selectinload(ItemPedido.vidro),
        selectinload(Pedido.itens).selectinload(ItemPedido.fundo),
        selectinload(Pedido.pagamentos),
        selectinload(Pedido.eventos),
    )


async def carregar_pedido_completo(pedido_id: int, db: AsyncSession) -> Pedido:
    """
    Busca um pedido completo por ID com todos os relacionamentos carregados ou lança HTTP 404.
    """
    resultado = await db.execute(
        select(Pedido)
        .where(Pedido.id == pedido_id)
        .options(*opcoes_carregamento_pedido())
        .execution_options(populate_existing=True)
    )
    pedido = resultado.scalar_one_or_none()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido


async def _resolver_vidro_id_por_tipo(vidro_tipo: str | None, db: AsyncSession) -> int | None:
    """
    Localiza automaticamente a chapa de vidro no estoque correspondente ao tipo informado.
    """
    if not vidro_tipo:
        return None
    tipo_limpo = vidro_tipo.strip().lower()
    if tipo_limpo not in {t.value for t in TipoVidro}:
        return None
    res = await db.execute(
        select(Vidro.id)
        .where(Vidro.tipo == TipoVidro(tipo_limpo))
        .order_by(Vidro.area_disponivel_m2.desc(), Vidro.id.asc())
        .limit(1)
    )
    return res.scalar_one_or_none()


async def _resolver_fundo_id_por_tipo(fundo_tipo: str | None, db: AsyncSession) -> int | None:
    """
    Localiza automaticamente a chapa de fundo no estoque correspondente ao tipo informado.
    """
    if not fundo_tipo:
        return None
    res = await db.execute(
        select(Fundo.id)
        .where(func.lower(Fundo.tipo) == fundo_tipo.strip().lower())
        .order_by(Fundo.area_disponivel_m2.desc(), Fundo.id.asc())
        .limit(1)
    )
    return res.scalar_one_or_none()


async def _construir_item_pedido(item_in: CriarItemPedido, db: AsyncSession) -> ItemPedido:
    """
    Executa o motor único de cálculo (quando aplicável) e monta a entidade ItemPedido com snapshot.
    """
    if item_in.tipo_item == TipoItemPedido.servico_livre:
        preco_unit = arredondar_2(item_in.preco_unitario or Decimal("0.00"))
        subtotal = arredondar_2(preco_unit * Decimal(item_in.quantidade))
        return ItemPedido(
            tipo_item=TipoItemPedido.servico_livre,
            descricao=(item_in.descricao or "").strip(),
            quantidade=item_in.quantidade,
            valor_sugerido=preco_unit,
            preco_unitario=preco_unit,
            subtotal=subtotal,
            mao_de_obra=Decimal("0.00"),
            snapshot_calculo=None,
        )

    if item_in.tipo_item == TipoItemPedido.vidro_avulso:
        assert item_in.obra_largura is not None and item_in.obra_altura is not None
        tipo_vidro = item_in.vidro_tipo
        if not tipo_vidro and item_in.vidro_id is not None:
            res_v = await db.execute(select(Vidro).where(Vidro.id == item_in.vidro_id))
            v_obj = res_v.scalar_one_or_none()
            if not v_obj:
                raise HTTPException(status_code=404, detail=f"Vidro id={item_in.vidro_id} não encontrado no estoque")
            tipo_vidro = v_obj.tipo.value

        resultado = await calcular_vidro_avulso(
            EntradaCalculoVidroAvulso(
                largura=item_in.obra_largura,
                altura=item_in.obra_altura,
                quantidade=item_in.quantidade,
                vidro_tipo=tipo_vidro or "incolor",
                vidro_id=item_in.vidro_id,
                mao_de_obra=item_in.mao_de_obra,
            ),
            db,
        )
    else:
        assert item_in.obra_largura is not None and item_in.obra_altura is not None
        resultado = await calcular_quadro(
            EntradaCalculoQuadro(
                obra_largura=item_in.obra_largura,
                obra_altura=item_in.obra_altura,
                quantidade=item_in.quantidade,
                paspatour=item_in.paspatour,
                tamanho_paspatour=item_in.tamanho_paspatour,
                paspatour_id=item_in.paspatour_id,
                molduras=[MolduraEntrada(moldura_id=m.moldura_id, ordem=m.ordem) for m in item_in.molduras],
                vidro_tipo=item_in.vidro_tipo,
                vidro_id=item_in.vidro_id,
                fundo_id=item_in.fundo_id,
                fundo_tipo=item_in.fundo_tipo,
                mao_de_obra=item_in.mao_de_obra,
            ),
            db,
        )

    valor_sugerido = resultado.valor_sugerido_unitario
    preco_unit = arredondar_2(item_in.preco_unitario) if item_in.preco_unitario is not None else valor_sugerido
    subtotal = arredondar_2(preco_unit * Decimal(item_in.quantidade))
    descricao = (
        item_in.descricao.strip()
        if item_in.descricao and item_in.descricao.strip()
        else resultado.descricao_sugerida
    )

    vidro_tipo_resolvido = item_in.vidro_tipo
    if not vidro_tipo_resolvido and item_in.vidro_id is not None:
        res_v = await db.execute(select(Vidro.tipo).where(Vidro.id == item_in.vidro_id))
        tipo_v = res_v.scalar_one_or_none()
        vidro_tipo_resolvido = tipo_v.value if tipo_v else None

    vidro_id_resolvido = item_in.vidro_id
    if vidro_id_resolvido is None and vidro_tipo_resolvido:
        vidro_id_resolvido = await _resolver_vidro_id_por_tipo(vidro_tipo_resolvido, db)

    fundo_tipo_resolvido = item_in.fundo_tipo
    if not fundo_tipo_resolvido and item_in.fundo_id is not None:
        res_f = await db.execute(select(Fundo.tipo).where(Fundo.id == item_in.fundo_id))
        fundo_tipo_resolvido = res_f.scalar_one_or_none()

    fundo_id_resolvido = item_in.fundo_id
    if fundo_id_resolvido is None and fundo_tipo_resolvido:
        fundo_id_resolvido = await _resolver_fundo_id_por_tipo(fundo_tipo_resolvido, db)

    item_db = ItemPedido(
        tipo_item=item_in.tipo_item,
        descricao=descricao,
        quantidade=item_in.quantidade,
        valor_sugerido=valor_sugerido,
        preco_unitario=preco_unit,
        subtotal=subtotal,
        obra_largura=item_in.obra_largura,
        obra_altura=item_in.obra_altura,
        paspatour=item_in.paspatour,
        tamanho_paspatour=item_in.tamanho_paspatour if item_in.paspatour else Decimal("0.00"),
        paspatour_id=item_in.paspatour_id,
        vidro_id=vidro_id_resolvido,
        vidro_tipo=vidro_tipo_resolvido,
        fundo_id=fundo_id_resolvido,
        fundo_tipo=fundo_tipo_resolvido,
        mao_de_obra=arredondar_2(item_in.mao_de_obra),
        snapshot_calculo=resultado.model_dump(mode="json"),
    )

    for moldura_calc in resultado.dimensoes.molduras:
        item_db.molduras.append(
            ItemPedidoMoldura(
                moldura_id=moldura_calc.moldura_id,
                ordem=moldura_calc.ordem,
                codigo_moldura_snapshot=moldura_calc.codigo,
                largura_barra_cm=moldura_calc.largura_barra_cm,
                tamanho_barra_m=moldura_calc.tamanho_barra_m,
                preco_m_aplicado=moldura_calc.preco_m_aplicado,
                altura_calculada_cm=moldura_calc.altura,
                largura_calculada_cm=moldura_calc.largura,
                metragem_total_m=moldura_calc.metragem_total_m,
                barras_sugeridas=moldura_calc.barras_sugeridas,
            )
        )

    return item_db


async def criar_novo_pedido(dados: CriarPedido, db: AsyncSession) -> Pedido:
    """
    Cria um novo orçamento/pedido em rascunho com número sequencial atômico e snapshots dos itens.
    """
    cliente_existe = await db.execute(select(Cliente.id).where(Cliente.id == dados.cliente_id))
    if cliente_existe.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    numero = await gerar_numero_pedido(db)
    validade = dados.data_validade_orcamento or (date.today() + timedelta(days=7))

    logger.info("Criando pedido %s para cliente_id=%s", numero, dados.cliente_id)

    novo_pedido = Pedido(
        cliente_id=dados.cliente_id,
        numero_pedido=numero,
        status_geral=StatusGeral.rascunho,
        status_producao=StatusProducao.pendente,
        status_financeiro=StatusFinanceiro.sem_pagamento,
        data_validade_orcamento=validade,
        prazo_entrega=dados.prazo_entrega,
        endereco_entrega=dados.endereco_entrega,
        frete=arredondar_2(dados.frete),
        desconto_valor=arredondar_2(dados.desconto_valor),
        desconto_tipo=dados.desconto_tipo,
        observacoes=dados.observacoes,
    )
    db.add(novo_pedido)
    await db.flush()

    itens_criados: list[ItemPedido] = []
    for item_in in dados.itens:
        item_db = await _construir_item_pedido(item_in, db)
        item_db.pedido_id = novo_pedido.id
        db.add(item_db)
        itens_criados.append(item_db)

    recalcular_totais_e_status_financeiro(novo_pedido, itens=itens_criados, pagamentos=[])

    evento = PedidoEvento(
        pedido_id=novo_pedido.id,
        eixo=Eixo.geral,
        status_anterior=None,
        status_novo=StatusGeral.rascunho.value,
        observacao="Orçamento criado",
    )
    db.add(evento)
    await db.commit()

    return await carregar_pedido_completo(novo_pedido.id, db)


async def atualizar_pedido_rascunho(pedido_id: int, dados: CriarPedido, db: AsyncSession) -> Pedido:
    """
    Atualiza itens, valores, prazos e cliente de um pedido exclusivamente enquanto estiver em rascunho.
    """
    pedido = await carregar_pedido_completo(pedido_id, db)
    if pedido.status_geral != StatusGeral.rascunho:
        raise HTTPException(status_code=400, detail="Apenas pedidos em rascunho podem ser editados")

    cliente_existe = await db.execute(select(Cliente.id).where(Cliente.id == dados.cliente_id))
    if cliente_existe.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    pedido.cliente_id = dados.cliente_id
    pedido.data_validade_orcamento = dados.data_validade_orcamento or pedido.data_validade_orcamento
    pedido.prazo_entrega = dados.prazo_entrega
    pedido.endereco_entrega = dados.endereco_entrega
    pedido.frete = arredondar_2(dados.frete)
    pedido.desconto_valor = arredondar_2(dados.desconto_valor)
    pedido.desconto_tipo = dados.desconto_tipo
    pedido.observacoes = dados.observacoes

    pedido.itens.clear()
    await db.flush()

    novos_itens: list[ItemPedido] = []
    for item_in in dados.itens:
        item_db = await _construir_item_pedido(item_in, db)
        item_db.pedido_id = pedido.id
        db.add(item_db)
        novos_itens.append(item_db)

    recalcular_totais_e_status_financeiro(pedido, itens=novos_itens)
    await db.commit()
    return await carregar_pedido_completo(pedido.id, db)


async def atualizar_status_pedido(
    pedido_id: int,
    eixo: Eixo,
    novo_status: str,
    observacao: str,
    db: AsyncSession,
) -> Pedido:
    """
    Executa transição validada nos eixos geral ou produção, registrando evento de auditoria.
    """
    pedido = await carregar_pedido_completo(pedido_id, db)

    if eixo == Eixo.financeiro:
        raise HTTPException(
            status_code=400,
            detail="Status financeiro é derivado dos lançamentos de pagamento e não pode ser alterado manualmente.",
        )
    if eixo == Eixo.estoque:
        raise HTTPException(status_code=400, detail="Eixo estoque é apenas para auditoria automática.")

    if pedido.status_geral in (StatusGeral.cancelado, StatusGeral.arquivado) and eixo != Eixo.geral:
        raise HTTPException(
            status_code=400,
            detail=f"Pedido {pedido.status_geral.value}. Movimentações de produção estão congeladas.",
        )

    if eixo == Eixo.producao and novo_status == StatusProducao.em_producao.value:
        raise HTTPException(
            status_code=400,
            detail="A transição para 'em_producao' deve ser feita via Baixa Assistida (/baixa-estoque).",
        )

    status_atual = pedido.status_geral.value if eixo == Eixo.geral else pedido.status_producao.value

    if not validar_transicao(eixo, status_atual, novo_status):
        raise HTTPException(
            status_code=400,
            detail=f"Transição de '{status_atual}' para '{novo_status}' não permitida no eixo {eixo.value}",
        )

    logger.info("Pedido %s: %s.%s -> %s", pedido.numero_pedido, eixo.value, status_atual, novo_status)

    obs_evento = observacao.strip() if observacao else None
    if eixo == Eixo.geral:
        pedido.status_geral = StatusGeral(novo_status)
        if novo_status == StatusGeral.confirmado.value:
            recalcular_totais_e_status_financeiro(pedido)
        elif novo_status == StatusGeral.cancelado.value and Decimal(str(pedido.valor_pago)) > Decimal("0.00"):
            aviso_estorno = (
                f"Cancelado com valor pago de R$ {Decimal(str(pedido.valor_pago)):.2f}: estorno pendente."
            )
            obs_evento = f"{obs_evento} | {aviso_estorno}" if obs_evento else aviso_estorno
            logger.warning("Pedido %s cancelado requerendo estorno de R$ %s", pedido.numero_pedido, pedido.valor_pago)
    else:
        pedido.status_producao = StatusProducao(novo_status)

    evento = PedidoEvento(
        pedido_id=pedido.id,
        eixo=eixo,
        status_anterior=status_atual,
        status_novo=novo_status,
        observacao=obs_evento,
    )
    db.add(evento)
    await db.commit()
    return await carregar_pedido_completo(pedido.id, db)


async def registrar_pagamento_pedido(
    pedido_id: int,
    dados: CriarPagamentoPedido,
    db: AsyncSession,
) -> Pedido:
    """
    Registra um pagamento parcial ou integral, confirma rascunho automaticamente e recalcula saldos.
    """
    pedido = await carregar_pedido_completo(pedido_id, db)

    if pedido.status_geral in (StatusGeral.cancelado, StatusGeral.arquivado):
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível registrar pagamento em pedido '{pedido.status_geral.value}'.",
        )

    valor_pag = arredondar_2(dados.valor)
    saldo_atual = arredondar_2(Decimal(str(pedido.saldo_devedor)))
    if valor_pag > saldo_atual:
        raise HTTPException(
            status_code=400,
            detail=f"Valor do pagamento (R$ {valor_pag:.2f}) excede o saldo devedor (R$ {saldo_atual:.2f}).",
        )

    status_fin_anterior = pedido.status_financeiro.value
    if pedido.status_geral == StatusGeral.rascunho:
        pedido.status_geral = StatusGeral.confirmado
        db.add(
            PedidoEvento(
                pedido_id=pedido.id,
                eixo=Eixo.geral,
                status_anterior=StatusGeral.rascunho.value,
                status_novo=StatusGeral.confirmado.value,
                observacao="Confirmado automaticamente ao registrar pagamento",
            )
        )

    pagamento = PagamentoPedido(
        pedido_id=pedido.id,
        valor=valor_pag,
        forma_pagamento=dados.forma_pagamento,
        data_pagamento=dados.data_pagamento or datetime.now(UTC),
        observacao=dados.observacao,
        estornado=False,
    )
    pedido.pagamentos.append(pagamento)
    recalcular_totais_e_status_financeiro(pedido)

    obs_fin = f"Pagamento {dados.forma_pagamento.value} de R$ {valor_pag:.2f}"
    if dados.observacao:
        obs_fin = f"{obs_fin} ({dados.observacao})"

    db.add(
        PedidoEvento(
            pedido_id=pedido.id,
            eixo=Eixo.financeiro,
            status_anterior=status_fin_anterior,
            status_novo=pedido.status_financeiro.value,
            observacao=obs_fin,
        )
    )
    logger.info("Pagamento registrado no pedido %s: R$ %s (%s)", pedido.numero_pedido, valor_pag, dados.forma_pagamento.value)
    await db.commit()
    return await carregar_pedido_completo(pedido.id, db)


async def estornar_pagamento_pedido(
    pedido_id: int,
    pagamento_id: int,
    motivo: str | None,
    db: AsyncSession,
) -> Pedido:
    """
    Marca um pagamento como estornado mantendo trilha histórica e recalculando o eixo financeiro.
    """
    pedido = await carregar_pedido_completo(pedido_id, db)

    if pedido.status_geral == StatusGeral.arquivado:
        raise HTTPException(status_code=400, detail="Pedidos arquivados não permitem estorno de pagamento.")

    pagamento = next((p for p in pedido.pagamentos if p.id == pagamento_id), None)
    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado para este pedido.")

    if pagamento.estornado:
        raise HTTPException(status_code=400, detail="Este pagamento já foi estornado.")

    status_fin_anterior = pedido.status_financeiro.value
    pagamento.estornado = True
    recalcular_totais_e_status_financeiro(pedido)

    obs_estorno = f"Estorno pagamento #{pagamento.id} (R$ {Decimal(str(pagamento.valor)):.2f})"
    if motivo and motivo.strip():
        obs_estorno = f"{obs_estorno}: {motivo.strip()}"

    db.add(
        PedidoEvento(
            pedido_id=pedido.id,
            eixo=Eixo.financeiro,
            status_anterior=status_fin_anterior,
            status_novo=pedido.status_financeiro.value,
            observacao=obs_estorno,
        )
    )
    logger.info("Estorno no pedido %s pagamento id=%s", pedido.numero_pedido, pagamento.id)
    await db.commit()
    return await carregar_pedido_completo(pedido.id, db)


def _validar_elegibilidade_baixa(pedido: Pedido) -> None:
    """
    Valida se o pedido está confirmado e em estágio anterior a em_producao.
    """
    if pedido.status_geral != StatusGeral.confirmado:
        raise HTTPException(
            status_code=400,
            detail="Baixa de estoque só é permitida para pedidos com status geral 'confirmado'.",
        )
    if pedido.status_producao.value not in ESTAGIOS_PRE_PRODUCAO:
        raise HTTPException(
            status_code=400,
            detail="Baixa de estoque só é permitida quando produção está em 'pendente', 'aguardando_material' ou 'na_fila'.",
        )


def _extrair_area_real_item_m2(item: ItemPedido) -> Decimal:
    """
    Extrai a área real unitária em m² a partir do snapshot imutável do item.
    """
    if item.snapshot_calculo and isinstance(item.snapshot_calculo, dict):
        areas = item.snapshot_calculo.get("areas") or {}
        area_str = areas.get("area_real_m2")
        if area_str is not None:
            return arredondar_4(Decimal(str(area_str)))

    if item.obra_largura is not None and item.obra_altura is not None:
        altura = Decimal(str(item.obra_altura))
        largura = Decimal(str(item.obra_largura))
        if item.paspatour and item.tamanho_paspatour:
            pasp = Decimal(str(item.tamanho_paspatour)) * Decimal("2")
            altura += pasp
            largura += pasp
        return arredondar_4((altura * largura) / Decimal("10000"))

    return Decimal("0.0000")


def _coletar_materiais_para_compra(pedido: Pedido) -> list[str]:
    """
    Identifica materiais com tipo definido no pedido porém sem chapa física cadastrada no estoque.
    """
    vidros_sem_estoque: dict[str, Decimal] = {}
    fundos_sem_estoque: dict[str, Decimal] = {}

    for item in pedido.itens:
        area_total_m2 = arredondar_4(_extrair_area_real_item_m2(item) * Decimal(item.quantidade))
        if area_total_m2 <= Decimal("0.0000"):
            continue

        if item.vidro_tipo and item.vidro_id is None:
            chave_v = item.vidro_tipo.strip()
            vidros_sem_estoque[chave_v] = arredondar_4(vidros_sem_estoque.get(chave_v, Decimal("0.0000")) + area_total_m2)

        if item.fundo_tipo and item.fundo_id is None:
            chave_f = item.fundo_tipo.strip()
            fundos_sem_estoque[chave_f] = arredondar_4(fundos_sem_estoque.get(chave_f, Decimal("0.0000")) + area_total_m2)

    mensagens: list[str] = []
    for tipo_v, area in vidros_sem_estoque.items():
        mensagens.append(f"Vidro '{tipo_v}' ({area} m²) não cadastrado no estoque — precisa ser comprado.")
    for tipo_f, area in fundos_sem_estoque.items():
        mensagens.append(f"Fundo '{tipo_f}' ({area} m²) não cadastrado no estoque — precisa ser comprado.")
    return mensagens


def _agrupar_insumos_pedido(pedido: Pedido) -> tuple[dict[int, dict], dict[int, dict], dict[int, dict]]:
    """
    Agrupa consumo previsto por moldura_id (barras), vidro_id (m² reais) e fundo_id (m² reais).
    """
    molduras_map: dict[int, dict] = {}
    vidros_map: dict[int, dict] = {}
    fundos_map: dict[int, dict] = {}

    for item in pedido.itens:
        for ipm in item.molduras:
            if ipm.moldura_id not in molduras_map:
                molduras_map[ipm.moldura_id] = {
                    "moldura": ipm.moldura,
                    "barras_sugeridas": 0,
                }
            molduras_map[ipm.moldura_id]["barras_sugeridas"] += int(ipm.barras_sugeridas)

        area_unit_m2 = _extrair_area_real_item_m2(item)
        area_total_m2 = arredondar_4(area_unit_m2 * Decimal(item.quantidade))

        if item.vidro_id is not None and item.vidro is not None and area_total_m2 > Decimal("0.0000"):
            if item.vidro_id not in vidros_map:
                vidros_map[item.vidro_id] = {"vidro": item.vidro, "area_a_baixar_m2": Decimal("0.0000")}
            vidros_map[item.vidro_id]["area_a_baixar_m2"] = arredondar_4(
                vidros_map[item.vidro_id]["area_a_baixar_m2"] + area_total_m2
            )

        if item.fundo_id is not None and item.fundo is not None and area_total_m2 > Decimal("0.0000"):
            if item.fundo_id not in fundos_map:
                fundos_map[item.fundo_id] = {"fundo": item.fundo, "area_a_baixar_m2": Decimal("0.0000")}
            fundos_map[item.fundo_id]["area_a_baixar_m2"] = arredondar_4(
                fundos_map[item.fundo_id]["area_a_baixar_m2"] + area_total_m2
            )

    return molduras_map, vidros_map, fundos_map


async def obter_previsao_baixa_estoque(pedido_id: int, db: AsyncSession) -> RespostaPrevisaoBaixa:
    """
    Calcula previsão de consumo de barras e m² reais antes da confirmação da Baixa Assistida.
    """
    pedido = await carregar_pedido_completo(pedido_id, db)
    _validar_elegibilidade_baixa(pedido)

    molduras_map, vidros_map, fundos_map = _agrupar_insumos_pedido(pedido)

    molduras_prev: list[PrevisaoMoldura] = []
    for mid, info in molduras_map.items():
        mol: Moldura = info["moldura"]
        sug = info["barras_sugeridas"]
        saldo_proj = mol.quantidade - sug
        molduras_prev.append(
            PrevisaoMoldura(
                moldura_id=mid,
                codigo=mol.codigo,
                cor=mol.cor,
                barras_sugeridas=sug,
                estoque_atual_barras=mol.quantidade,
                saldo_projetado=saldo_proj,
                em_ruptura=saldo_proj < 0,
            )
        )

    vidros_prev: list[PrevisaoArea] = []
    for vid, info in vidros_map.items():
        v_obj: Vidro = info["vidro"]
        baixar = info["area_a_baixar_m2"]
        disp = arredondar_4(Decimal(str(v_obj.area_disponivel_m2)))
        saldo_proj = arredondar_4(disp - baixar)
        vidros_prev.append(
            PrevisaoArea(
                id=vid,
                descricao=f"Vidro {v_obj.tipo.value} {v_obj.espessura}mm",
                area_a_baixar_m2=baixar,
                area_disponivel_m2=disp,
                saldo_projetado_m2=saldo_proj,
                em_ruptura=saldo_proj < Decimal("0.0000"),
            )
        )

    fundos_prev: list[PrevisaoArea] = []
    for fid, info in fundos_map.items():
        f_obj: Fundo = info["fundo"]
        baixar = info["area_a_baixar_m2"]
        disp = arredondar_4(Decimal(str(f_obj.area_disponivel_m2)))
        saldo_proj = arredondar_4(disp - baixar)
        fundos_prev.append(
            PrevisaoArea(
                id=fid,
                descricao=f"Fundo {f_obj.tipo} {f_obj.espessura}mm",
                area_a_baixar_m2=baixar,
                area_disponivel_m2=disp,
                saldo_projetado_m2=saldo_proj,
                em_ruptura=saldo_proj < Decimal("0.0000"),
            )
        )

    materiais_compra = _coletar_materiais_para_compra(pedido)
    possui_insumos = bool(molduras_prev or vidros_prev or fundos_prev)
    return RespostaPrevisaoBaixa(
        possui_insumos_estoque=possui_insumos,
        molduras=molduras_prev,
        vidros=vidros_prev,
        fundos=fundos_prev,
        materiais_para_compra=materiais_compra,
    )


async def realizar_baixa_estoque_assistida(
    pedido_id: int,
    dados: ConfirmarBaixaEstoque | None,
    db: AsyncSession,
) -> tuple[Pedido, list[MaterialBaixado], list[str]]:
    """
    Executa Baixa Assistida não-bloqueante (com ajustes manuais de barras) e move para em_producao.
    """
    pedido = await carregar_pedido_completo(pedido_id, db)
    _validar_elegibilidade_baixa(pedido)

    status_prod_anterior = pedido.status_producao.value
    molduras_map, vidros_map, fundos_map = _agrupar_insumos_pedido(pedido)
    ajustes_por_id = {aj.moldura_id: aj.barras_baixadas for aj in (dados.ajustes_molduras if dados else [])}

    materiais_baixados: list[MaterialBaixado] = []
    alertas_ruptura: list[str] = []
    resumos_evento: list[str] = []

    for mid, info in molduras_map.items():
        mol: Moldura = info["moldura"]
        barras = ajustes_por_id.get(mid, info["barras_sugeridas"])
        mol.quantidade -= barras
        em_ruptura = mol.quantidade < 0
        materiais_baixados.append(
            MaterialBaixado(
                tipo="moldura",
                id=mid,
                descricao=f"Moldura {mol.codigo}",
                consumo=Decimal(barras),
                unidade="barras",
                saldo_atual=Decimal(mol.quantidade),
                em_ruptura=em_ruptura,
            )
        )
        resumos_evento.append(f"Moldura {mol.codigo}: -{barras} bar (saldo {mol.quantidade})")
        if em_ruptura:
            msg = f"Moldura {mol.codigo} ficou com saldo negativo ({mol.quantidade} barras)."
            alertas_ruptura.append(msg)
            logger.warning("Ruptura na baixa pedido %s: %s", pedido.numero_pedido, msg)

    for vid, info in vidros_map.items():
        v_obj: Vidro = info["vidro"]
        baixar = info["area_a_baixar_m2"]
        v_obj.area_disponivel_m2 = arredondar_4(Decimal(str(v_obj.area_disponivel_m2)) - baixar)
        em_ruptura = v_obj.area_disponivel_m2 < Decimal("0.0000")
        desc = f"Vidro {v_obj.tipo.value} {v_obj.espessura}mm"
        materiais_baixados.append(
            MaterialBaixado(
                tipo="vidro",
                id=vid,
                descricao=desc,
                consumo=baixar,
                unidade="m2",
                saldo_atual=v_obj.area_disponivel_m2,
                em_ruptura=em_ruptura,
            )
        )
        resumos_evento.append(f"{desc}: -{baixar} m2 (saldo {v_obj.area_disponivel_m2} m2)")
        if em_ruptura:
            msg = f"{desc} ficou com saldo negativo ({v_obj.area_disponivel_m2} m2)."
            alertas_ruptura.append(msg)
            logger.warning("Ruptura na baixa pedido %s: %s", pedido.numero_pedido, msg)

    for fid, info in fundos_map.items():
        f_obj: Fundo = info["fundo"]
        baixar = info["area_a_baixar_m2"]
        f_obj.area_disponivel_m2 = arredondar_4(Decimal(str(f_obj.area_disponivel_m2)) - baixar)
        em_ruptura = f_obj.area_disponivel_m2 < Decimal("0.0000")
        desc = f"Fundo {f_obj.tipo} {f_obj.espessura}mm"
        materiais_baixados.append(
            MaterialBaixado(
                tipo="fundo",
                id=fid,
                descricao=desc,
                consumo=baixar,
                unidade="m2",
                saldo_atual=f_obj.area_disponivel_m2,
                em_ruptura=em_ruptura,
            )
        )
        resumos_evento.append(f"{desc}: -{baixar} m2 (saldo {f_obj.area_disponivel_m2} m2)")
        if em_ruptura:
            msg = f"{desc} ficou com saldo negativo ({f_obj.area_disponivel_m2} m2)."
            alertas_ruptura.append(msg)
            logger.warning("Ruptura na baixa pedido %s: %s", pedido.numero_pedido, msg)

    pedido.status_producao = StatusProducao.em_producao

    materiais_compra = _coletar_materiais_para_compra(pedido)
    for msg_compra in materiais_compra:
        alertas_ruptura.append(msg_compra)
        resumos_evento.append(msg_compra)
        logger.warning("Material sem cadastro em estoque pedido %s: %s", pedido.numero_pedido, msg_compra)

    obs_usuario = dados.observacao.strip() if dados and dados.observacao else None
    obs_producao = obs_usuario or "Produção iniciada via Baixa Assistida"
    db.add(
        PedidoEvento(
            pedido_id=pedido.id,
            eixo=Eixo.producao,
            status_anterior=status_prod_anterior,
            status_novo=StatusProducao.em_producao.value,
            observacao=obs_producao,
        )
    )

    if resumos_evento:
        db.add(
            PedidoEvento(
                pedido_id=pedido.id,
                eixo=Eixo.estoque,
                status_anterior=status_prod_anterior,
                status_novo="baixa_realizada",
                observacao="; ".join(resumos_evento),
            )
        )

    logger.info("Baixa assistida concluída pedido %s (rupturas=%d)", pedido.numero_pedido, len(alertas_ruptura))
    await db.commit()
    pedido_atualizado = await carregar_pedido_completo(pedido.id, db)
    return pedido_atualizado, materiais_baixados, alertas_ruptura
