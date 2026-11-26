import logging
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estoque import Fundo, Moldura, Vidro
from app.models.tabela_preco import TabelaPrecoFundo, TabelaPrecoPaspatour, TabelaPrecoVidro
from app.schemas.calculadora import (
    AreasCalculo,
    DimensaoMolduraCalculada,
    DimensoesQuadro,
    EntradaCalculoQuadro,
    EntradaCalculoVidroAvulso,
    ItemCustoQuadro,
    Medida2D,
    ResultadoCalculoQuadro,
)

logger = logging.getLogger(__name__)

DUAS_CASAS = Decimal("0.01")
QUATRO_CASAS = Decimal("0.0001")


def arredondar_2(valor: Decimal) -> Decimal:
    """
    Arredonda um Decimal para 2 casas decimais usando ROUND_HALF_UP.
    """
    return valor.quantize(DUAS_CASAS, rounding=ROUND_HALF_UP)


def arredondar_4(valor: Decimal) -> Decimal:
    """
    Arredonda um Decimal para 4 casas decimais usando ROUND_HALF_UP.
    """
    return valor.quantize(QUATRO_CASAS, rounding=ROUND_HALF_UP)


def calcular_area_m2(largura_cm: Decimal, altura_cm: Decimal) -> Decimal:
    """
    Calcula a área em m² a partir de dimensões em centímetros com 4 casas decimais.
    """
    return arredondar_4((largura_cm * altura_cm) / Decimal("10000"))


def calcular_perimetro_m(largura_cm: Decimal, altura_cm: Decimal) -> Decimal:
    """
    Calcula o perímetro seco em metros a partir de dimensões em centímetros.
    """
    return arredondar_4((Decimal("2") * (largura_cm + altura_cm)) / Decimal("100"))


def calcular_perda_45_m(largura_barra_cm: Decimal) -> Decimal:
    """
    Calcula a perda técnica de corte em 45° (8 × largura da barra) em metros.
    """
    return arredondar_4((Decimal("8") * largura_barra_cm) / Decimal("100"))


def calcular_barras_sugeridas(metragem_total_m: Decimal, quantidade: int, tamanho_barra_m: Decimal) -> int:
    """
    Calcula a quantidade sugerida de barras inteiras arredondando para cima.
    """
    consumo_total = metragem_total_m * Decimal(quantidade)
    if consumo_total <= Decimal("0"):
        return 0
    return int((consumo_total / tamanho_barra_m).to_integral_value(rounding=ROUND_CEILING))


def calcular_dimensoes(
    obra_altura: Decimal,
    obra_largura: Decimal,
    paspatour_tamanho: Decimal,
    molduras: list[tuple[str, Decimal]],
) -> dict:
    """
    Propaga as dimensões da obra para vidro/paspatour e camadas de molduras (interna -> externa).
    """
    altura_vidro = obra_altura + (paspatour_tamanho * 2) if paspatour_tamanho > 0 else obra_altura
    largura_vidro = obra_largura + (paspatour_tamanho * 2) if paspatour_tamanho > 0 else obra_largura

    dimensoes = {
        "obra": {"altura": arredondar_2(obra_altura), "largura": arredondar_2(obra_largura)},
        "vidro": {"altura": arredondar_2(altura_vidro), "largura": arredondar_2(largura_vidro)},
        "molduras": [],
        "quadro_final": {},
    }

    altura_atual = altura_vidro
    largura_atual = largura_vidro

    for codigo, largura_barra in molduras:
        altura_atual = altura_atual + (largura_barra * 2)
        largura_atual = largura_atual + (largura_barra * 2)
        dimensoes["molduras"].append(
            {
                "codigo": codigo,
                "altura": arredondar_2(altura_atual),
                "largura": arredondar_2(largura_atual),
            }
        )

    dimensoes["quadro_final"] = {
        "altura": arredondar_2(altura_atual),
        "largura": arredondar_2(largura_atual),
    }
    return dimensoes


async def _resolver_tabela_vidro(
    vidro_tipo: str | None,
    vidro_id: int | None,
    db: AsyncSession,
) -> tuple[str | None, TabelaPrecoVidro | None]:
    """
    Valida referência de estoque de vidro (se informada) e resolve a tabela de preços por m².
    """
    tipo_efetivo = vidro_tipo.strip().lower() if vidro_tipo else None

    if vidro_id is not None:
        res_vidro = await db.execute(select(Vidro).where(Vidro.id == vidro_id))
        vidro_obj = res_vidro.scalar_one_or_none()
        if not vidro_obj:
            raise HTTPException(status_code=404, detail=f"Vidro id={vidro_id} não encontrado no estoque")
        if not tipo_efetivo:
            tipo_efetivo = vidro_obj.tipo.value

    if not tipo_efetivo:
        return None, None

    res_tabela = await db.execute(
        select(TabelaPrecoVidro).where(func.lower(TabelaPrecoVidro.tipo) == tipo_efetivo)
    )
    tabela_vidro = res_tabela.scalar_one_or_none()
    if not tabela_vidro:
        raise HTTPException(
            status_code=404,
            detail=f"Tabela de preço não cadastrada para vidro tipo '{tipo_efetivo}'",
        )
    return tipo_efetivo, tabela_vidro


async def _resolver_tabela_paspatour(
    paspatour_id: int | None,
    db: AsyncSession,
) -> TabelaPrecoPaspatour:
    """
    Resolve a opção selecionada de paspatour sem fallback implícito quando houver múltiplas opções.
    """
    if paspatour_id is not None:
        res = await db.execute(select(TabelaPrecoPaspatour).where(TabelaPrecoPaspatour.id == paspatour_id))
        obj = res.scalar_one_or_none()
        if not obj:
            raise HTTPException(status_code=404, detail=f"Paspatour id={paspatour_id} não encontrado na tabela de preços")
        return obj

    res_todos = await db.execute(select(TabelaPrecoPaspatour))
    opcoes = res_todos.scalars().all()
    if len(opcoes) == 1:
        return opcoes[0]
    if len(opcoes) == 0:
        raise HTTPException(status_code=404, detail="Nenhuma opção de paspatour cadastrada na tabela de preços")
    raise HTTPException(
        status_code=422,
        detail="Informe paspatour_id quando houver mais de uma opção cadastrada",
    )


async def _resolver_tabela_fundo(
    fundo_tipo: str | None,
    fundo_id: int | None,
    db: AsyncSession,
) -> tuple[str | None, TabelaPrecoFundo | None]:
    """
    Valida referência de estoque de fundo (se informada) e resolve a tabela de preços por m².
    """
    tipo_efetivo = fundo_tipo.strip() if fundo_tipo else None

    if fundo_id is not None:
        res_fundo = await db.execute(select(Fundo).where(Fundo.id == fundo_id))
        fundo_obj = res_fundo.scalar_one_or_none()
        if not fundo_obj:
            raise HTTPException(status_code=404, detail=f"Fundo id={fundo_id} não encontrado no estoque")
        if not tipo_efetivo:
            tipo_efetivo = fundo_obj.tipo

    if not tipo_efetivo:
        return None, None

    res_tabela = await db.execute(
        select(TabelaPrecoFundo).where(func.lower(TabelaPrecoFundo.tipo) == tipo_efetivo.lower())
    )
    tabela_fundo = res_tabela.scalar_one_or_none()
    if not tabela_fundo:
        raise HTTPException(
            status_code=404,
            detail=f"Tabela de preço não cadastrada para fundo tipo '{tipo_efetivo}'",
        )
    return tabela_fundo.tipo, tabela_fundo


async def calcular_quadro(dados: EntradaCalculoQuadro, db: AsyncSession) -> ResultadoCalculoQuadro:
    """
    Executa o motor único determinístico para cálculo de quadro sob medida.
    """
    ordens = [m.ordem for m in dados.molduras]
    if len(ordens) != len(set(ordens)):
        raise HTTPException(status_code=422, detail="As ordens das molduras não podem se repetir")

    if dados.paspatour and dados.tamanho_paspatour <= Decimal("0"):
        raise HTTPException(status_code=422, detail="tamanho_paspatour deve ser maior que zero quando paspatour=true")

    molduras_ord = sorted(dados.molduras, key=lambda m: m.ordem)
    molduras_db: list[Moldura] = []
    for moldura_entrada in molduras_ord:
        res_m = await db.execute(select(Moldura).where(Moldura.id == moldura_entrada.moldura_id))
        moldura_obj = res_m.scalar_one_or_none()
        if not moldura_obj:
            raise HTTPException(status_code=404, detail=f"Moldura id={moldura_entrada.moldura_id} não encontrada")
        molduras_db.append(moldura_obj)

    paspatour_tamanho = dados.tamanho_paspatour if dados.paspatour else Decimal("0.00")
    molduras_para_dimensoes = [(m.codigo, Decimal(str(m.largura_barra))) for m in molduras_db]
    dim_dict = calcular_dimensoes(dados.obra_altura, dados.obra_largura, paspatour_tamanho, molduras_para_dimensoes)

    area_real_m2 = calcular_area_m2(dim_dict["vidro"]["largura"], dim_dict["vidro"]["altura"])
    custos: list[ItemCustoQuadro] = []
    valor_unitario = Decimal("0.00")
    partes_desc = [f"Quadro {arredondar_2(dados.obra_largura)}x{arredondar_2(dados.obra_altura)}cm"]

    if dados.paspatour:
        tabela_pasp = await _resolver_tabela_paspatour(dados.paspatour_id, db)
        preco_pasp = arredondar_2(Decimal(str(tabela_pasp.preco_por_m2)))
        subtotal_pasp = arredondar_2(area_real_m2 * preco_pasp)
        custos.append(
            ItemCustoQuadro(
                nome=tabela_pasp.descricao,
                tipo="paspatour",
                medida=area_real_m2,
                unidade="m2",
                preco_unitario=preco_pasp,
                subtotal=subtotal_pasp,
            )
        )
        valor_unitario += subtotal_pasp
        partes_desc.append(f"Paspatour {arredondar_2(paspatour_tamanho)}cm")

    tipo_vidro_efetivo, tabela_vidro = await _resolver_tabela_vidro(dados.vidro_tipo, dados.vidro_id, db)
    area_minima_vidro = Decimal("0.0000")
    area_cobrada_vidro = area_real_m2
    if tabela_vidro is not None:
        area_minima_vidro = arredondar_4(Decimal(str(tabela_vidro.area_minima_m2)))
        area_cobrada_vidro = max(area_real_m2, area_minima_vidro)
        preco_vidro = arredondar_2(Decimal(str(tabela_vidro.preco_por_m2)))
        subtotal_vidro = arredondar_2(area_cobrada_vidro * preco_vidro)
        custos.append(
            ItemCustoQuadro(
                nome=f"Vidro {tipo_vidro_efetivo}",
                tipo="vidro",
                medida=area_cobrada_vidro,
                unidade="m2",
                preco_unitario=preco_vidro,
                subtotal=subtotal_vidro,
            )
        )
        valor_unitario += subtotal_vidro
        partes_desc.append(f"Vidro {tipo_vidro_efetivo}")

    molduras_calculadas: list[DimensaoMolduraCalculada] = []
    if molduras_db:
        codigos_molduras: list[str] = []
        for idx, moldura_obj in enumerate(molduras_db):
            camada = dim_dict["molduras"][idx]
            largura_barra = arredondar_2(Decimal(str(moldura_obj.largura_barra)))
            tamanho_barra = arredondar_2(Decimal(str(moldura_obj.tamanho_barra)))
            preco_m = arredondar_2(Decimal(str(moldura_obj.preco_venda)))

            perimetro_seco = calcular_perimetro_m(camada["largura"], camada["altura"])
            perda_45 = calcular_perda_45_m(largura_barra)
            metragem_total = arredondar_4(perimetro_seco + perda_45)
            barras_sug = calcular_barras_sugeridas(metragem_total, dados.quantidade, tamanho_barra)
            subtotal_m = arredondar_2(metragem_total * preco_m)

            molduras_calculadas.append(
                DimensaoMolduraCalculada(
                    moldura_id=moldura_obj.id,
                    ordem=molduras_ord[idx].ordem,
                    codigo=moldura_obj.codigo,
                    largura_barra_cm=largura_barra,
                    tamanho_barra_m=tamanho_barra,
                    preco_m_aplicado=preco_m,
                    altura=camada["altura"],
                    largura=camada["largura"],
                    perimetro_seco_m=perimetro_seco,
                    perda_45_m=perda_45,
                    metragem_total_m=metragem_total,
                    barras_sugeridas=barras_sug,
                )
            )
            custos.append(
                ItemCustoQuadro(
                    nome=f"Moldura {moldura_obj.codigo}",
                    tipo="moldura",
                    medida=metragem_total,
                    unidade="m",
                    preco_unitario=preco_m,
                    subtotal=subtotal_m,
                )
            )
            valor_unitario += subtotal_m
            codigos_molduras.append(moldura_obj.codigo)
        partes_desc.append(f"Moldura {' + '.join(codigos_molduras)}")

    tipo_fundo_efetivo, tabela_fundo = await _resolver_tabela_fundo(dados.fundo_tipo, dados.fundo_id, db)
    area_fundo_m2 = area_real_m2 if tabela_fundo is not None else Decimal("0.0000")
    if tabela_fundo is not None:
        preco_fundo = arredondar_2(Decimal(str(tabela_fundo.preco_por_m2)))
        subtotal_fundo = arredondar_2(area_fundo_m2 * preco_fundo)
        custos.append(
            ItemCustoQuadro(
                nome=f"Fundo {tipo_fundo_efetivo}",
                tipo="fundo",
                medida=area_fundo_m2,
                unidade="m2",
                preco_unitario=preco_fundo,
                subtotal=subtotal_fundo,
            )
        )
        valor_unitario += subtotal_fundo
        partes_desc.append(f"Fundo {tipo_fundo_efetivo}")

    mao_de_obra = arredondar_2(dados.mao_de_obra)
    if mao_de_obra > Decimal("0.00"):
        custos.append(
            ItemCustoQuadro(
                nome="Mão de obra",
                tipo="mao_de_obra",
                medida=Decimal("1"),
                unidade="un",
                preco_unitario=mao_de_obra,
                subtotal=mao_de_obra,
            )
        )
        valor_unitario += mao_de_obra

    valor_sugerido_unitario = arredondar_2(valor_unitario)
    total_sugerido = arredondar_2(valor_sugerido_unitario * Decimal(dados.quantidade))

    return ResultadoCalculoQuadro(
        dimensoes=DimensoesQuadro(
            obra=Medida2D(**dim_dict["obra"]),
            vidro=Medida2D(**dim_dict["vidro"]),
            molduras=molduras_calculadas,
            quadro_final=Medida2D(**dim_dict["quadro_final"]),
        ),
        areas=AreasCalculo(
            area_real_m2=area_real_m2,
            area_cobrada_vidro_m2=area_cobrada_vidro,
            area_minima_vidro_m2=area_minima_vidro,
            area_fundo_m2=area_fundo_m2,
        ),
        custos=custos,
        valor_sugerido_unitario=valor_sugerido_unitario,
        total_sugerido=total_sugerido,
        total_final=total_sugerido,
        descricao_sugerida=" | ".join(partes_desc),
    )


async def calcular_vidro_avulso(dados: EntradaCalculoVidroAvulso, db: AsyncSession) -> ResultadoCalculoQuadro:
    """
    Executa o motor único determinístico para cálculo de corte reto de vidro ou espelho avulso.
    """
    tipo_vidro_efetivo, tabela_vidro = await _resolver_tabela_vidro(dados.vidro_tipo, dados.vidro_id, db)
    assert tabela_vidro is not None and tipo_vidro_efetivo is not None

    largura = arredondar_2(dados.largura)
    altura = arredondar_2(dados.altura)
    area_real_m2 = calcular_area_m2(largura, altura)
    area_minima_vidro = arredondar_4(Decimal(str(tabela_vidro.area_minima_m2)))
    area_cobrada_vidro = max(area_real_m2, area_minima_vidro)
    preco_vidro = arredondar_2(Decimal(str(tabela_vidro.preco_por_m2)))
    subtotal_vidro = arredondar_2(area_cobrada_vidro * preco_vidro)

    custos = [
        ItemCustoQuadro(
            nome=f"Vidro {tipo_vidro_efetivo}",
            tipo="vidro",
            medida=area_cobrada_vidro,
            unidade="m2",
            preco_unitario=preco_vidro,
            subtotal=subtotal_vidro,
        )
    ]
    valor_unitario = subtotal_vidro

    mao_de_obra = arredondar_2(dados.mao_de_obra)
    if mao_de_obra > Decimal("0.00"):
        custos.append(
            ItemCustoQuadro(
                nome="Mão de obra",
                tipo="mao_de_obra",
                medida=Decimal("1"),
                unidade="un",
                preco_unitario=mao_de_obra,
                subtotal=mao_de_obra,
            )
        )
        valor_unitario += mao_de_obra

    valor_sugerido_unitario = arredondar_2(valor_unitario)
    total_sugerido = arredondar_2(valor_sugerido_unitario * Decimal(dados.quantidade))

    return ResultadoCalculoQuadro(
        dimensoes=DimensoesQuadro(
            obra=Medida2D(altura=altura, largura=largura),
            vidro=Medida2D(altura=altura, largura=largura),
            molduras=[],
            quadro_final=Medida2D(altura=altura, largura=largura),
        ),
        areas=AreasCalculo(
            area_real_m2=area_real_m2,
            area_cobrada_vidro_m2=area_cobrada_vidro,
            area_minima_vidro_m2=area_minima_vidro,
            area_fundo_m2=Decimal("0.0000"),
        ),
        custos=custos,
        valor_sugerido_unitario=valor_sugerido_unitario,
        total_sugerido=total_sugerido,
        total_final=total_sugerido,
        descricao_sugerida=f"Vidro Avulso {tipo_vidro_efetivo} {largura}x{altura}cm",
    )
