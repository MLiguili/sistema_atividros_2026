from decimal import Decimal

from app.models.pedido import TipoDesconto
from app.services.pedido import calcular_totais_pedido


def test_calcular_totais_com_frete_e_desconto_valor():
    """
    Valida soma do frete ao subtotal e subtração de desconto em valor fixo.
    """
    desc, total, saldo = calcular_totais_pedido(
        subtotal_itens=Decimal("500.00"),
        frete=Decimal("35.00"),
        desconto_valor=Decimal("50.00"),
        desconto_tipo=TipoDesconto.valor,
        valor_pago=Decimal("200.00"),
    )
    assert desc == Decimal("50.00")
    assert total == Decimal("485.00")
    assert saldo == Decimal("285.00")


def test_calcular_totais_com_desconto_percentual_e_limite_zero():
    """
    Valida desconto percentual sobre subtotal_itens e piso zero quando desconto excede itens+frete.
    """
    desc, total, saldo = calcular_totais_pedido(
        subtotal_itens=Decimal("545.00"),
        frete=Decimal("30.00"),
        desconto_valor=Decimal("10.00"),
        desconto_tipo=TipoDesconto.percentual,
        valor_pago=Decimal("200.00"),
    )
    assert desc == Decimal("54.50")
    assert total == Decimal("520.50")
    assert saldo == Decimal("320.50")

    desc_100, total_100, saldo_100 = calcular_totais_pedido(
        subtotal_itens=Decimal("100.00"),
        frete=Decimal("0.00"),
        desconto_valor=Decimal("100.00"),
        desconto_tipo=TipoDesconto.percentual,
        valor_pago=Decimal("0.00"),
    )
    assert desc_100 == Decimal("100.00")
    assert total_100 == Decimal("0.00")
    assert saldo_100 == Decimal("0.00")

    _, total_excedente, saldo_excedente = calcular_totais_pedido(
        subtotal_itens=Decimal("80.00"),
        frete=Decimal("10.00"),
        desconto_valor=Decimal("150.00"),
        desconto_tipo=TipoDesconto.valor,
        valor_pago=Decimal("50.00"),
    )
    assert total_excedente == Decimal("0.00")
    assert saldo_excedente == Decimal("0.00")
