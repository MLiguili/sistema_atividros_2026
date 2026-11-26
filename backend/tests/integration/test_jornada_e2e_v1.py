import re
import zlib
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.usuario import Usuario
from app.services.autenticacao import obter_hash_senha


def _extrair_texto_streams_pdf(conteudo_pdf: bytes) -> str:
    """
    Descomprime streams FlateDecode de um PDF gerado pelo FPDF2 para inspeção de conteúdo em testes.
    """
    blocos = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", conteudo_pdf, flags=re.DOTALL):
        bruto = match.group(1)
        try:
            blocos.append(zlib.decompress(bruto).decode("latin-1", errors="ignore"))
        except zlib.error:
            blocos.append(bruto.decode("latin-1", errors="ignore"))
    return "\n".join(blocos).lower()


@pytest.mark.asyncio
async def test_jornada_e2e_v1_completa_balcao_e_oficina(
    client: AsyncClient,
    db_session,
):
    """
    Executa a jornada completa V1.0 do Atividros:
    Login -> Estoque -> Calculadora -> Pedido Rascunho -> Pagamento Parcial (confirmação) ->
    Baixa Assistida -> Etapas Kanban -> Quitação -> Entrega -> PDF seguro -> Dashboard -> Arquivamento.
    """
    # 1. Healthcheck (rota raiz)
    resp_health = await client.get("/")
    assert resp_health.status_code == 200

    # 2. Login real via /autenticacao/entrar
    operador = Usuario(
        nome_usuario="operador_e2e",
        senha_hash=obter_hash_senha("SenhaForte123!"),
        nome_completo="Operador E2E",
        esta_ativo=True,
    )
    db_session.add(operador)
    await db_session.commit()

    resp_token = await client.post(
        "/autenticacao/entrar",
        data={"username": "operador_e2e", "password": "SenhaForte123!"},
    )
    assert resp_token.status_code == 200
    headers = {"Authorization": f"Bearer {resp_token.json()['token_acesso']}"}

    # 3. Configurar tabelas de preço, moldura e vidro com entrada em chapas
    resp_tv = await client.post(
        "/calculadora/tabela-vidro",
        headers=headers,
        json={"tipo": "incolor_e2e", "preco_por_m2": "120.00", "area_minima_m2": "0.2500"},
    )
    assert resp_tv.status_code in (200, 201)

    resp_m = await client.post(
        "/estoque/molduras",
        headers=headers,
        json={
            "codigo": "MLD-E2E-01",
            "cor": "Freijó",
            "quantidade": 5,
            "estoque_minimo": 2,
            "preco_venda": "80.00",
            "preco_custo": "32.50",
            "tamanho_barra": "2.75",
            "largura_barra": "3.00",
        },
    )
    assert resp_m.status_code in (200, 201)
    moldura_id = resp_m.json()["id"]

    resp_v = await client.post(
        "/estoque/vidros",
        headers=headers,
        json={
            "tipo": "incolor",
            "espessura": "3.00",
            "area_disponivel_m2": "0.0000",
            "estoque_minimo_m2": "1.0000",
        },
    )
    assert resp_v.status_code in (200, 201)
    vidro_id = resp_v.json()["id"]

    resp_chapas = await client.post(
        f"/estoque/vidros/{vidro_id}/entrada-chapas",
        headers=headers,
        json={
            "quantidade_chapas": 2,
            "largura_cm": "100.00",
            "altura_cm": "200.00",
        },
    )
    assert resp_chapas.status_code == 200
    assert Decimal(str(resp_chapas.json()["area_disponivel_m2"])) == Decimal("4.0000")

    # 4. Criar cliente
    resp_cli = await client.post(
        "/clientes/",
        headers=headers,
        json={"nome": "Oficina", "sobrenome": "Arte E2E", "telefone": "11988887777"},
    )
    assert resp_cli.status_code in (200, 201)
    cliente_id = resp_cli.json()["id"]

    # 5. Simular na calculadora unificada
    resp_calc = await client.post(
        "/calculadora/quadro",
        headers=headers,
        json={
            "obra_largura": "50.00",
            "obra_altura": "40.00",
            "quantidade": 1,
            "paspatour": False,
            "vidro_tipo": "incolor_e2e",
            "vidro_id": vidro_id,
            "mao_de_obra": "35.00",
            "molduras": [{"moldura_id": moldura_id, "ordem": 0}],
        },
    )
    assert resp_calc.status_code == 200
    sugerido = Decimal(str(resp_calc.json()["valor_sugerido_unitario"]))
    assert sugerido > Decimal("0.00")

    # 6. Criar pedido em rascunho com preço praticado abaixo do sugerido e depois editar rascunho
    preco_negociado = (sugerido - Decimal("15.00")).quantize(Decimal("0.01"))
    resp_ped = await client.post(
        "/pedidos/",
        headers=headers,
        json={
            "cliente_id": cliente_id,
            "frete": "20.00",
            "desconto_valor": "0.00",
            "desconto_tipo": "valor",
            "itens": [
                {
                    "tipo_item": "quadro_sob_medida",
                    "quantidade": 1,
                    "obra_largura": "50.00",
                    "obra_altura": "40.00",
                    "vidro_tipo": "incolor_e2e",
                    "vidro_id": vidro_id,
                    "mao_de_obra": "35.00",
                    "molduras": [{"moldura_id": moldura_id, "ordem": 0}],
                    "preco_unitario": str(preco_negociado),
                }
            ],
        },
    )
    assert resp_ped.status_code in (200, 201)
    ped = resp_ped.json()
    ped_id = ped["id"]
    assert ped["status_geral"] == "rascunho"
    assert ped["tem_item_abaixo_do_sugerido"] is True

    # Editar rascunho adicionando serviço livre
    resp_put = await client.put(
        f"/pedidos/{ped_id}",
        headers=headers,
        json={
            "cliente_id": cliente_id,
            "frete": "20.00",
            "desconto_valor": "0.00",
            "desconto_tipo": "valor",
            "itens": [
                {
                    "tipo_item": "quadro_sob_medida",
                    "quantidade": 1,
                    "obra_largura": "50.00",
                    "obra_altura": "40.00",
                    "vidro_tipo": "incolor_e2e",
                    "vidro_id": vidro_id,
                    "mao_de_obra": "35.00",
                    "molduras": [{"moldura_id": moldura_id, "ordem": 0}],
                    "preco_unitario": str(preco_negociado),
                },
                {
                    "tipo_item": "servico_livre",
                    "descricao": "Pendurador duplo especial",
                    "quantidade": 1,
                    "preco_unitario": "15.00",
                },
            ],
        },
    )
    assert resp_put.status_code == 200
    total_pedido = Decimal(str(resp_put.json()["valor_total"]))

    # 7. Registrar 1º pagamento parcial -> confirma rascunho automaticamente
    resp_pag1 = await client.post(
        f"/pedidos/{ped_id}/pagamentos",
        headers=headers,
        json={"valor": "50.00", "forma_pagamento": "pix", "observacao": "Sinal"},
    )
    assert resp_pag1.status_code == 201
    ped_conf = resp_pag1.json()
    assert ped_conf["status_geral"] == "confirmado"
    assert ped_conf["status_financeiro"] == "pagamento_parcial"

    # 8. Previsão e Baixa Assistida de Estoque
    resp_prev = await client.get(f"/pedidos/{ped_id}/previsao-baixa", headers=headers)
    assert resp_prev.status_code == 200
    assert resp_prev.json()["possui_insumos_estoque"] is True

    resp_baixa = await client.post(
        f"/pedidos/{ped_id}/baixa-estoque",
        headers=headers,
        json={
            "ajustes_molduras": [{"moldura_id": moldura_id, "barras_baixadas": 1}],
            "observacao": "Corte oficina E2E",
        },
    )
    assert resp_baixa.status_code == 200
    assert resp_baixa.json()["pedido"]["status_producao"] == "em_producao"

    # Confirmar débito de 1 barra na moldura e 0.2000 m² no vidro (5 -> 4 barras, 4.0000 -> 3.8000 m²)
    molduras_lista = (await client.get("/estoque/molduras", headers=headers)).json()
    m_atual = next(m for m in molduras_lista if m["id"] == moldura_id)
    v_atual = (await client.get(f"/estoque/vidros/{vidro_id}", headers=headers)).json()
    assert m_atual["quantidade"] == 4
    assert Decimal(str(v_atual["area_disponivel_m2"])) == Decimal("3.8000")

    # 9. Avançar produção e quitar pagamento restante
    for prox in ("embalando", "pronto_entrega"):
        r_st = await client.patch(
            f"/pedidos/{ped_id}/status",
            headers=headers,
            json={"eixo": "producao", "novo_status": prox},
        )
        assert r_st.status_code == 200

    restante = (total_pedido - Decimal("50.00")).quantize(Decimal("0.01"))
    resp_pag2 = await client.post(
        f"/pedidos/{ped_id}/pagamentos",
        headers=headers,
        json={"valor": str(restante), "forma_pagamento": "cartao_credito"},
    )
    assert resp_pag2.status_code == 201
    assert resp_pag2.json()["status_financeiro"] == "pago_total"

    # Marcar entregue
    resp_entregue = await client.patch(
        f"/pedidos/{ped_id}/status",
        headers=headers,
        json={"eixo": "geral", "novo_status": "entregue"},
    )
    assert resp_entregue.status_code == 200
    assert resp_entregue.json()["status_geral"] == "entregue"

    # 10. Gerar PDF e garantir ausência de campos internos
    resp_pdf = await client.get(f"/pedidos/{ped_id}/pdf", headers=headers)
    assert resp_pdf.status_code == 200
    assert resp_pdf.content.startswith(b"%PDF")
    texto_pdf = _extrair_texto_streams_pdf(resp_pdf.content)
    assert len(texto_pdf) > 50
    assert "sugerido" not in texto_pdf
    assert "32.50" not in texto_pdf

    # 11. Verificar Dashboard e histórico do cliente
    resp_dash = await client.get("/dashboard/resumo", headers=headers)
    assert resp_dash.status_code == 200
    assert resp_dash.json()["pedidos_ativos"] >= 0

    resp_hist = await client.get(f"/clientes/{cliente_id}/pedidos", headers=headers)
    assert resp_hist.status_code == 200
    assert len(resp_hist.json()) == 1

    # 12. Arquivar pedido entregue
    resp_arq = await client.patch(
        f"/pedidos/{ped_id}/status",
        headers=headers,
        json={"eixo": "geral", "novo_status": "arquivado"},
    )
    assert resp_arq.status_code == 200
    assert resp_arq.json()["status_geral"] == "arquivado"
