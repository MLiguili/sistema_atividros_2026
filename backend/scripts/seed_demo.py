import asyncio
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessaoAsyncLocal
from app.models.cliente import Cliente
from app.models.estoque import Fundo, Moldura, Suplemento, TipoVidro, Vidro
from app.models.pedido import Eixo, FormaPagamento, Pedido, TipoDesconto, TipoItemPedido
from app.models.tabela_preco import TabelaPrecoFundo, TabelaPrecoPaspatour, TabelaPrecoVidro
from app.models.usuario import Usuario
from app.schemas.pedido import (
    ConfirmarBaixaEstoque,
    CriarItemPedido,
    CriarPagamentoPedido,
    CriarPedido,
    ItemPedidoMolduraInput,
)
from app.services.autenticacao import obter_hash_senha
from app.services.pedido import (
    atualizar_status_pedido,
    criar_novo_pedido,
    realizar_baixa_estoque_assistida,
    registrar_pagamento_pedido,
)


async def garantir_admin(db: AsyncSession) -> Usuario:
    """
    Garante a existência do usuário administrador 'admin' com senha padrão 'admin123'.
    """
    res = await db.execute(select(Usuario).where(Usuario.nome_usuario == "admin"))
    usuario = res.scalar_one_or_none()
    senha_hash = obter_hash_senha("admin123")

    if usuario:
        usuario.senha_hash = senha_hash
        usuario.esta_ativo = True
        await db.commit()
        return usuario

    usuario = Usuario(
        nome_usuario="admin",
        senha_hash=senha_hash,
        nome_completo="Administrador Atividros",
        esta_ativo=True,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


async def popular_tabelas_preco(db: AsyncSession) -> dict[str, object]:
    """
    Popula tabelas de preço iniciais para vidros, fundos e paspatours caso ainda não existam.
    """
    vidros_dados = [
        ("incolor", Decimal("135.00"), Decimal("0.2500"), "Vidro Incolor 2mm/3mm padrão"),
        ("antireflexo", Decimal("245.00"), Decimal("0.2500"), "Vidro Antirreflexo museológico"),
        ("espelho", Decimal("210.00"), Decimal("0.2500"), "Espelho Prata 3mm/4mm"),
    ]
    for tipo, preco, area_min, desc in vidros_dados:
        existe = (await db.execute(select(TabelaPrecoVidro).where(TabelaPrecoVidro.tipo == tipo))).scalar_one_or_none()
        if not existe:
            db.add(TabelaPrecoVidro(tipo=tipo, preco_por_m2=preco, area_minima_m2=area_min, descricao=desc))

    fundos_dados = [
        ("MDF 3mm", Decimal("45.00"), "Chapa MDF cru 3mm"),
        ("Eucatex 3mm", Decimal("38.00"), "Chapa Eucatex padrão"),
        ("Foam Board 5mm", Decimal("115.00"), "Foam Board livre de ácido para conservação"),
    ]
    for tipo, preco, desc in fundos_dados:
        existe = (await db.execute(select(TabelaPrecoFundo).where(TabelaPrecoFundo.tipo == tipo))).scalar_one_or_none()
        if not existe:
            db.add(TabelaPrecoFundo(tipo=tipo, preco_por_m2=preco, descricao=desc))

    paspatours_dados = [
        ("Paspatour Branco Clássico 5cm", Decimal("85.00")),
        ("Paspatour Preto Museológico", Decimal("95.00")),
        ("Paspatour Off-White Texturizado", Decimal("90.00")),
    ]
    paspatours: list[TabelaPrecoPaspatour] = []
    for desc, preco in paspatours_dados:
        p = (await db.execute(select(TabelaPrecoPaspatour).where(TabelaPrecoPaspatour.descricao == desc))).scalar_one_or_none()
        if not p:
            p = TabelaPrecoPaspatour(descricao=desc, preco_por_m2=preco)
            db.add(p)
        paspatours.append(p)

    await db.commit()
    for p in paspatours:
        await db.refresh(p)

    return {"paspatours": paspatours}


async def popular_estoque(db: AsyncSession) -> dict[str, list]:
    """
    Popula molduras, vidros, fundos e suplementos com cenários normais e de estoque crítico.
    """
    molduras_spec = [
        ("MLD-PRETA-2CM", 18, 5, "85.00", "32.00", "Preto Fosco", "2.75", "2.00", "Moldurarte"),
        ("MLD-FREIJO-3CM", 12, 4, "115.00", "45.00", "Freijó Natural", "2.75", "3.00", "Moldurarte"),
        ("MLD-DOURADA-4CM", 3, 5, "165.00", "68.00", "Dourado Envelhecido", "2.75", "4.00", "Italiano"),
        ("MLD-BRANCA-2CM", 15, 5, "82.00", "30.00", "Branco Laca", "2.75", "2.00", "Brazil Frame"),
        ("MLD-CAIXA-5CM", 2, 4, "145.00", "58.00", "Preto Caixa Alta", "2.75", "5.00", "Brazil Frame"),
        ("MLD-PRATA-3CM", 9, 3, "125.00", "49.00", "Prata Escovado", "2.75", "3.00", "Italiano"),
    ]
    molduras: list[Moldura] = []
    for cod, qtd, est_min, pv, pc, cor, tam, larg, marca in molduras_spec:
        m = (await db.execute(select(Moldura).where(Moldura.codigo == cod))).scalar_one_or_none()
        if not m:
            m = Moldura(
                codigo=cod,
                quantidade=qtd,
                estoque_minimo=est_min,
                preco_venda=Decimal(pv),
                preco_custo=Decimal(pc),
                cor=cor,
                tamanho_barra=Decimal(tam),
                largura_barra=Decimal(larg),
                marca=marca,
            )
            db.add(m)
        molduras.append(m)

    vidros_spec = [
        (TipoVidro.incolor, Decimal("2.00"), "Transparente", Decimal("14.5000"), Decimal("4.0000")),
        (TipoVidro.antireflexo, Decimal("2.00"), "Fosco", Decimal("1.8000"), Decimal("3.0000")),
        (TipoVidro.espelho, Decimal("4.00"), "Prata", Decimal("9.2000"), Decimal("3.0000")),
    ]
    vidros: list[Vidro] = []
    for tipo, esp, cor, area, min_m2 in vidros_spec:
        v = (
            await db.execute(select(Vidro).where(Vidro.tipo == tipo, Vidro.espessura == esp))
        ).scalar_one_or_none()
        if not v:
            v = Vidro(tipo=tipo, espessura=esp, cor=cor, area_disponivel_m2=area, estoque_minimo_m2=min_m2)
            db.add(v)
        vidros.append(v)

    fundos_spec = [
        ("MDF 3mm", Decimal("3.00"), "Natural", Decimal("16.0000"), Decimal("4.0000")),
        ("Eucatex 3mm", Decimal("3.00"), "Marrom", Decimal("2.2000"), Decimal("4.0000")),
        ("Foam Board 5mm", Decimal("5.00"), "Branco", Decimal("6.5000"), Decimal("2.0000")),
    ]
    fundos: list[Fundo] = []
    for tipo, esp, cor, area, min_m2 in fundos_spec:
        f = (await db.execute(select(Fundo).where(Fundo.tipo == tipo))).scalar_one_or_none()
        if not f:
            f = Fundo(tipo=tipo, espessura=esp, cor=cor, area_disponivel_m2=area, estoque_minimo_m2=min_m2)
            db.add(f)
        fundos.append(f)

    suplementos_spec = [
        ("Grampo Flexível (Caixa)", 24, "caixas"),
        ("Pendurador Jacaré Dourado", 180, "unidades"),
        ("Fita Kraft Gomada 50mm", 14, "rolos"),
        ("Cola PVA Madeira 1kg", 6, "frascos"),
    ]
    for nome, qtd, un in suplementos_spec:
        s = (await db.execute(select(Suplemento).where(Suplemento.nome == nome))).scalar_one_or_none()
        if not s:
            db.add(Suplemento(nome=nome, quantidade=qtd, unidade=un))

    await db.commit()
    for obj in [*molduras, *vidros, *fundos]:
        await db.refresh(obj)

    return {"molduras": molduras, "vidros": vidros, "fundos": fundos}


async def popular_clientes(db: AsyncSession) -> list[Cliente]:
    """
    Popula carteira inicial de clientes fictícios para navegação e histórico.
    """
    clientes_spec = [
        ("Marina", "Albuquerque", "(11) 99123-4567", "marina.arte@exemplo.com", "Rua das Palmeiras, 140 - Jardins"),
        ("Galeria", "Horizonte", "(11) 98456-1122", "contato@galeriahorizonte.com.br", "Av. Paulista, 1800, Cj 42"),
        ("Ricardo", "Mendonça", "(11) 97234-8899", "ricardo.m@exemplo.com", "Rua Harmonia, 512 - Vila Madalena"),
        ("Studio", "Vértice Arquitetura", "(11) 96655-3300", "projetos@studiovertice.com.br", "Al. Lorena, 920"),
        ("Camila", "Ferreira", "(11) 95544-7788", None, "Retirada no balcão"),
    ]
    clientes: list[Cliente] = []
    for nome, sobre, tel, email, end in clientes_spec:
        c = (
            await db.execute(select(Cliente).where(Cliente.nome == nome, Cliente.sobrenome == sobre))
        ).scalar_one_or_none()
        if not c:
            c = Cliente(nome=nome, sobrenome=sobre, telefone=tel, email=email, endereco=end)
            db.add(c)
        clientes.append(c)

    await db.commit()
    for c in clientes:
        await db.refresh(c)
    return clientes


async def popular_pedidos(
    db: AsyncSession,
    clientes: list[Cliente],
    estoque: dict[str, list],
    tabelas: dict[str, object],
) -> int:
    """
    Popula pedidos distribuídos entre rascunho, todas as 6 colunas do Kanban e entregue.
    """
    molduras: list[Moldura] = estoque["molduras"]
    vidros: list[Vidro] = estoque["vidros"]
    fundos: list[Fundo] = estoque["fundos"]
    paspatours: list[TabelaPrecoPaspatour] = tabelas["paspatours"]
    hoje = date.today()

    # 1. Orçamento em rascunho (2 itens: quadro com paspatour + serviço livre)
    await criar_novo_pedido(
        CriarPedido(
            cliente_id=clientes[0].id,
            prazo_entrega=hoje + timedelta(days=7),
            frete=Decimal("25.00"),
            desconto_valor=Decimal("5.00"),
            desconto_tipo=TipoDesconto.percentual,
            observacoes="Cliente avaliando cor do paspatour.",
            itens=[
                CriarItemPedido(
                    tipo_item=TipoItemPedido.quadro_sob_medida,
                    quantidade=1,
                    obra_largura=Decimal("50.00"),
                    obra_altura=Decimal("70.00"),
                    paspatour=True,
                    tamanho_paspatour=Decimal("5.00"),
                    paspatour_id=paspatours[0].id,
                    vidro_tipo="incolor",
                    vidro_id=vidros[0].id,
                    fundo_id=fundos[0].id,
                    mao_de_obra=Decimal("40.00"),
                    molduras=[ItemPedidoMolduraInput(moldura_id=molduras[0].id, ordem=0)],
                ),
                CriarItemPedido(
                    tipo_item=TipoItemPedido.servico_livre,
                    descricao="Instalação em parede de alvenaria",
                    quantidade=1,
                    preco_unitario=Decimal("75.00"),
                ),
            ],
        ),
        db,
    )

    # 2. Confirmado -> Pendente (com preço abaixo do sugerido para testar Callout)
    p2 = await criar_novo_pedido(
        CriarPedido(
            cliente_id=clientes[1].id,
            prazo_entrega=hoje + timedelta(days=4),
            itens=[
                CriarItemPedido(
                    tipo_item=TipoItemPedido.quadro_sob_medida,
                    quantidade=2,
                    obra_largura=Decimal("40.00"),
                    obra_altura=Decimal("50.00"),
                    vidro_tipo="antireflexo",
                    vidro_id=vidros[1].id,
                    fundo_id=fundos[2].id,
                    mao_de_obra=Decimal("35.00"),
                    molduras=[ItemPedidoMolduraInput(moldura_id=molduras[1].id, ordem=0)],
                    preco_unitario=Decimal("180.00"),
                )
            ],
        ),
        db,
    )
    await atualizar_status_pedido(p2.id, Eixo.geral, "confirmado", "Aprovado por WhatsApp", db)

    # 3. Confirmado -> Aguardando Material (moldura dourada crítica)
    p3 = await criar_novo_pedido(
        CriarPedido(
            cliente_id=clientes[2].id,
            prazo_entrega=hoje + timedelta(days=6),
            itens=[
                CriarItemPedido(
                    tipo_item=TipoItemPedido.quadro_sob_medida,
                    quantidade=1,
                    obra_largura=Decimal("80.00"),
                    obra_altura=Decimal("100.00"),
                    vidro_tipo="incolor",
                    vidro_id=vidros[0].id,
                    fundo_id=fundos[0].id,
                    mao_de_obra=Decimal("60.00"),
                    molduras=[ItemPedidoMolduraInput(moldura_id=molduras[2].id, ordem=0)],
                )
            ],
        ),
        db,
    )
    await atualizar_status_pedido(p3.id, Eixo.geral, "confirmado", "Confirmado aguardando lote", db)
    await atualizar_status_pedido(p3.id, Eixo.producao, "aguardando_material", "Falta chegar barra dourada", db)

    # 4. Confirmado -> Na Fila (com pagamento parcial 50% PIX confirmando automaticamente)
    p4 = await criar_novo_pedido(
        CriarPedido(
            cliente_id=clientes[3].id,
            prazo_entrega=hoje + timedelta(days=3),
            itens=[
                CriarItemPedido(
                    tipo_item=TipoItemPedido.vidro_avulso,
                    quantidade=2,
                    obra_largura=Decimal("60.00"),
                    obra_altura=Decimal("90.00"),
                    vidro_tipo="espelho",
                    vidro_id=vidros[2].id,
                    mao_de_obra=Decimal("25.00"),
                )
            ],
        ),
        db,
    )
    sinal_p4 = (Decimal(str(p4.valor_total)) / Decimal("2")).quantize(Decimal("0.01"))
    await registrar_pagamento_pedido(
        p4.id,
        CriarPagamentoPedido(valor=sinal_p4, forma_pagamento=FormaPagamento.pix, observacao="Sinal 50%"),
        db,
    )
    await atualizar_status_pedido(p4.id, Eixo.producao, "na_fila", "Pronto para bancada", db)

    # 5. Confirmado -> Em Produção (com Baixa Assistida executada)
    p5 = await criar_novo_pedido(
        CriarPedido(
            cliente_id=clientes[4].id,
            prazo_entrega=hoje + timedelta(days=2),
            itens=[
                CriarItemPedido(
                    tipo_item=TipoItemPedido.quadro_sob_medida,
                    quantidade=1,
                    obra_largura=Decimal("30.00"),
                    obra_altura=Decimal("40.00"),
                    paspatour=True,
                    tamanho_paspatour=Decimal("4.00"),
                    paspatour_id=paspatours[1].id,
                    vidro_tipo="incolor",
                    vidro_id=vidros[0].id,
                    fundo_id=fundos[0].id,
                    mao_de_obra=Decimal("30.00"),
                    molduras=[ItemPedidoMolduraInput(moldura_id=molduras[3].id, ordem=0)],
                )
            ],
        ),
        db,
    )
    await registrar_pagamento_pedido(
        p5.id,
        CriarPagamentoPedido(valor=Decimal("100.00"), forma_pagamento=FormaPagamento.cartao_debito, observacao="Sinal"),
        db,
    )
    await realizar_baixa_estoque_assistida(p5.id, ConfirmarBaixaEstoque(observacao="Corte iniciado"), db)

    # 6. Confirmado -> Embalando (Pago Total)
    p6 = await criar_novo_pedido(
        CriarPedido(
            cliente_id=clientes[0].id,
            prazo_entrega=hoje + timedelta(days=1),
            itens=[
                CriarItemPedido(
                    tipo_item=TipoItemPedido.quadro_sob_medida,
                    quantidade=1,
                    obra_largura=Decimal("45.00"),
                    obra_altura=Decimal("60.00"),
                    vidro_tipo="incolor",
                    vidro_id=vidros[0].id,
                    fundo_id=fundos[0].id,
                    mao_de_obra=Decimal("30.00"),
                    molduras=[ItemPedidoMolduraInput(moldura_id=molduras[0].id, ordem=0)],
                )
            ],
        ),
        db,
    )
    await registrar_pagamento_pedido(
        p6.id,
        CriarPagamentoPedido(valor=Decimal(str(p6.valor_total)), forma_pagamento=FormaPagamento.cartao_credito),
        db,
    )
    await realizar_baixa_estoque_assistida(p6.id, ConfirmarBaixaEstoque(observacao="Baixa padrão"), db)
    await atualizar_status_pedido(p6.id, Eixo.producao, "embalando", "Protegendo cantoneiras", db)

    # 7. Confirmado -> Pronto para Entrega
    p7 = await criar_novo_pedido(
        CriarPedido(
            cliente_id=clientes[1].id,
            prazo_entrega=hoje,
            itens=[
                CriarItemPedido(
                    tipo_item=TipoItemPedido.quadro_sob_medida,
                    quantidade=1,
                    obra_largura=Decimal("50.00"),
                    obra_altura=Decimal("50.00"),
                    vidro_tipo="espelho",
                    vidro_id=vidros[2].id,
                    fundo_id=fundos[0].id,
                    mao_de_obra=Decimal("40.00"),
                    molduras=[ItemPedidoMolduraInput(moldura_id=molduras[5].id, ordem=0)],
                )
            ],
        ),
        db,
    )
    await registrar_pagamento_pedido(
        p7.id,
        CriarPagamentoPedido(valor=Decimal("120.00"), forma_pagamento=FormaPagamento.dinheiro),
        db,
    )
    await realizar_baixa_estoque_assistida(p7.id, ConfirmarBaixaEstoque(observacao="Corte espelho"), db)
    await atualizar_status_pedido(p7.id, Eixo.producao, "embalando", "Embalagem ok", db)
    await atualizar_status_pedido(p7.id, Eixo.producao, "pronto_entrega", "Disponível no balcão", db)

    # 8. Entregue e Pago Total
    p8 = await criar_novo_pedido(
        CriarPedido(
            cliente_id=clientes[3].id,
            prazo_entrega=hoje - timedelta(days=1),
            itens=[
                CriarItemPedido(
                    tipo_item=TipoItemPedido.quadro_sob_medida,
                    quantidade=1,
                    obra_largura=Decimal("35.00"),
                    obra_altura=Decimal("45.00"),
                    vidro_tipo="incolor",
                    vidro_id=vidros[0].id,
                    fundo_id=fundos[1].id,
                    mao_de_obra=Decimal("25.00"),
                    molduras=[ItemPedidoMolduraInput(moldura_id=molduras[1].id, ordem=0)],
                )
            ],
        ),
        db,
    )
    await registrar_pagamento_pedido(
        p8.id,
        CriarPagamentoPedido(valor=Decimal(str(p8.valor_total)), forma_pagamento=FormaPagamento.pix),
        db,
    )
    await realizar_baixa_estoque_assistida(p8.id, ConfirmarBaixaEstoque(observacao="Baixa concluída"), db)
    await atualizar_status_pedido(p8.id, Eixo.producao, "embalando", "Embalado", db)
    await atualizar_status_pedido(p8.id, Eixo.producao, "pronto_entrega", "Finalizado", db)
    await atualizar_status_pedido(p8.id, Eixo.geral, "entregue", "Retirado pelo cliente", db)

    return 8


async def executar_seed() -> None:
    """
    Executa a carga idempotente do usuário admin e massa de demonstração no banco configurado.
    """
    async with SessaoAsyncLocal() as db:
        await garantir_admin(db)
        pedidos_existentes = (await db.execute(select(Pedido.id))).scalars().first()
        if pedidos_existentes is not None:
            print("Admin verificado (admin/admin123) e dados de demonstração já existem.")
            return

        tabelas = await popular_tabelas_preco(db)
        estoque = await popular_estoque(db)
        clientes = await popular_clientes(db)
        total_pedidos = await popular_pedidos(db, clientes, estoque, tabelas)
        print(
            f"Seed concluído com sucesso! Admin: admin/admin123 | "
            f"Clientes: {len(clientes)} | Molduras: {len(estoque['molduras'])} | "
            f"Vidros: {len(estoque['vidros'])} | Fundos: {len(estoque['fundos'])} | Pedidos: {total_pedidos}"
        )


if __name__ == "__main__":
    asyncio.run(executar_seed())
