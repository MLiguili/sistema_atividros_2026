import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estoque import Fundo, Moldura
from app.models.tabela_preco import TabelaPrecoPaspatour, TabelaPrecoVidro
from app.schemas.calculadora import (
    DimensoesQuadro,
    EntradaCalculoQuadro,
    ItemCustoQuadro,
    ResultadoCalculoQuadro,
)

logger = logging.getLogger(__name__)


def calcular_dimensoes(
    obra_altura: Decimal,
    obra_largura: Decimal,
    paspatour_tamanho: Decimal,
    molduras: list[tuple[str, Decimal]],
) -> dict:
    dimensoes = {"obra": {"altura": obra_altura, "largura": obra_largura}, "vidro": {}, "molduras": [], "quadro_final": {}}

    if paspatour_tamanho > 0:
        dimensoes["vidro"]["altura"] = obra_altura + (paspatour_tamanho * 2)
        dimensoes["vidro"]["largura"] = obra_largura + (paspatour_tamanho * 2)
    else:
        dimensoes["vidro"]["altura"] = obra_altura
        dimensoes["vidro"]["largura"] = obra_largura

    altura_atual = dimensoes["vidro"]["altura"]
    largura_atual = dimensoes["vidro"]["largura"]

    for codigo, largura_barra in molduras:
        altura_atual = altura_atual + (largura_barra * 2)
        largura_atual = largura_atual + (largura_barra * 2)
        dimensoes["molduras"].append({"codigo": codigo, "altura": altura_atual, "largura": largura_atual})

    dimensoes["quadro_final"]["altura"] = altura_atual
    dimensoes["quadro_final"]["largura"] = largura_atual

    return dimensoes


def calcular_area_m2(largura_cm: Decimal, altura_cm: Decimal) -> Decimal:
    return (largura_cm * altura_cm) / Decimal("10000")


def calcular_perimetro_m(largura_cm: Decimal, altura_cm: Decimal) -> Decimal:
    return (Decimal("2") * (largura_cm + altura_cm)) / Decimal("100")


async def calcular_precos(
    dimensoes: dict,
    molduras_db: list[dict],
    vidro_preco_m2: Decimal,
    paspatour_preco_m2: Decimal,
    fundo_preco: Decimal | None,
    tem_paspatour: bool,
    quantidade: int,
) -> tuple[list[ItemCustoQuadro], Decimal]:
    custos = []
    total = Decimal("0.0")

    if tem_paspatour and paspatour_preco_m2 > 0:
        area_vidro = calcular_area_m2(dimensoes["vidro"]["largura"], dimensoes["vidro"]["altura"])
        subtotal = (area_vidro * paspatour_preco_m2).quantize(Decimal("0.01"))
        custos.append(ItemCustoQuadro(nome="Paspatour", tipo="paspatour", medida=area_vidro, unidade="m2", preco_unitario=paspatour_preco_m2, subtotal=subtotal))
        total += subtotal

    if vidro_preco_m2 > 0:
        area_vidro = calcular_area_m2(dimensoes["vidro"]["largura"], dimensoes["vidro"]["altura"])
        subtotal = (area_vidro * vidro_preco_m2).quantize(Decimal("0.01"))
        custos.append(ItemCustoQuadro(nome="Vidro", tipo="vidro", medida=area_vidro, unidade="m2", preco_unitario=vidro_preco_m2, subtotal=subtotal))
        total += subtotal

    for moldura_info in molduras_db:
        if "preco_venda" in moldura_info and moldura_info["preco_venda"] > 0:
            perimetro = calcular_perimetro_m(moldura_info["altura"], moldura_info["largura"])
            subtotal = (perimetro * Decimal(str(moldura_info["preco_venda"]))).quantize(Decimal("0.01"))
            custos.append(ItemCustoQuadro(nome=f"Moldura {moldura_info['codigo']}", tipo="moldura", medida=perimetro, unidade="m", preco_unitario=Decimal(str(moldura_info["preco_venda"])), subtotal=subtotal))
            total += subtotal

    if fundo_preco is not None and fundo_preco > 0:
        area_fundo = calcular_area_m2(dimensoes["obra"]["largura"], dimensoes["obra"]["altura"])
        subtotal = (area_fundo * fundo_preco).quantize(Decimal("0.01"))
        custos.append(ItemCustoQuadro(nome="Fundo", tipo="fundo", medida=area_fundo, unidade="m2", preco_unitario=fundo_preco, subtotal=subtotal))
        total += subtotal

    if quantidade > 1:
        for custo in custos:
            custo.subtotal = (custo.subtotal * quantidade).quantize(Decimal("0.01"))
        total = (total * quantidade).quantize(Decimal("0.01"))

    return custos, total


async def calcular_quadro(dados: EntradaCalculoQuadro, db: AsyncSession) -> ResultadoCalculoQuadro:
    molduras_db = []
    molduras_ord = sorted(dados.molduras, key=lambda m: m.ordem)
    molduras_para_dimensoes = []

    for moldura_entrada in molduras_ord:
        resultado = await db.execute(select(Moldura).where(Moldura.id == moldura_entrada.moldura_id))
        moldura = resultado.scalar_one_or_none()
        if moldura:
            molduras_para_dimensoes.append((moldura.codigo, Decimal(str(moldura.largura_barra))))
            molduras_db.append({"codigo": moldura.codigo, "preco_venda": moldura.preco_venda, "altura": Decimal("0"), "largura": Decimal("0")})

    paspatour_tamanho = dados.tamanho_paspatour if dados.paspatour else Decimal("0")
    dimensoes = calcular_dimensoes(dados.obra_altura, dados.obra_largura, paspatour_tamanho, molduras_para_dimensoes)

    for i, moldura_info in enumerate(molduras_db):
        if i < len(dimensoes["molduras"]):
            moldura_info["altura"] = dimensoes["molduras"][i]["altura"]
            moldura_info["largura"] = dimensoes["molduras"][i]["largura"]

    vidro_preco = Decimal("0")
    if dados.vidro_tipo:
        resultado = await db.execute(select(TabelaPrecoVidro).where(TabelaPrecoVidro.tipo == dados.vidro_tipo))
        tabela_vidro = resultado.scalar_one_or_none()
        if tabela_vidro:
            vidro_preco = Decimal(str(tabela_vidro.preco_por_m2))

    paspatour_preco = Decimal("0")
    if dados.paspatour:
        resultado = await db.execute(select(TabelaPrecoPaspatour).limit(1))
        tabela_paspatour = resultado.scalar_one_or_none()
        if tabela_paspatour:
            paspatour_preco = Decimal(str(tabela_paspatour.preco_por_m2))

    fundo_preco = None
    if dados.fundo_id:
        resultado = await db.execute(select(Fundo).where(Fundo.id == dados.fundo_id))
        fundo = resultado.scalar_one_or_none()
        if fundo:
            fundo_preco = Decimal("30.0")

    custos, total = await calcular_precos(
        dimensoes,
        molduras_db,
        vidro_preco,
        paspatour_preco,
        fundo_preco,
        dados.paspatour,
        dados.quantidade,
    )

    dimensoes_schema = DimensoesQuadro(
        obra=dimensoes["obra"],
        vidro=dimensoes["vidro"],
        molduras=dimensoes["molduras"],
        quadro_final=dimensoes["quadro_final"],
    )

    return ResultadoCalculoQuadro(dimensoes=dimensoes_schema, custos=custos, total_sugerido=total, total_final=total)
