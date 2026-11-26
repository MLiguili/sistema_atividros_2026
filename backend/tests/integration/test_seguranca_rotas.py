import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("metodo", "rota"),
    [
        ("GET", "/autenticacao/me"),
        ("GET", "/clientes/"),
        ("POST", "/clientes/"),
        ("GET", "/clientes/1"),
        ("GET", "/clientes/1/pedidos"),
        ("GET", "/estoque/molduras"),
        ("POST", "/estoque/molduras"),
        ("GET", "/estoque/vidros"),
        ("GET", "/estoque/vidros/1"),
        ("POST", "/estoque/vidros/1/entrada-chapas"),
        ("POST", "/estoque/vidros/1/ajuste-m2"),
        ("GET", "/estoque/fundos"),
        ("GET", "/estoque/fundos/1"),
        ("POST", "/estoque/fundos/1/entrada-chapas"),
        ("POST", "/estoque/fundos/1/ajuste-m2"),
        ("GET", "/estoque/suplementos"),
        ("POST", "/calculadora/quadro"),
        ("POST", "/calculadora/vidro-avulso"),
        ("GET", "/calculadora/tabela-vidro"),
        ("GET", "/calculadora/tabela-fundo"),
        ("GET", "/calculadora/tabela-paspatour"),
        ("GET", "/pedidos/"),
        ("POST", "/pedidos/"),
        ("GET", "/pedidos/1"),
        ("GET", "/pedidos/1/pagamentos"),
        ("POST", "/pedidos/1/pagamentos"),
        ("GET", "/pedidos/1/previsao-baixa"),
        ("POST", "/pedidos/1/baixa-estoque"),
        ("GET", "/pedidos/1/pdf"),
        ("GET", "/dashboard/resumo"),
    ],
)
async def test_todos_endpoints_de_negocio_exigem_jwt(client: AsyncClient, metodo: str, rota: str):
    """
    Varredura sistemática garantindo que todas as rotas de negócio rejeitam requisições sem token (HTTP 401).
    """
    resposta = await client.request(metodo, rota)
    assert resposta.status_code == 401
