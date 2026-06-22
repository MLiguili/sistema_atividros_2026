"""End-to-end test via Docker: logs in, creates client+moldura+pedido via API."""
import time
import pytest
import httpx

BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_e2e_fluxo_completo():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Login
        print("\n[E2E] 1. Login como admin")
        r = await client.post(
            "/autenticacao/entrar",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert r.status_code == 200, f"Login falhou: {r.text}"
        token = r.json()["token_acesso"]
        headers = {"Authorization": f"Bearer {token}"}
        print("    Login OK, token obtido")

        # 2. Dashboard
        print("\n[E2E] 2. Acessando Dashboard")
        r = await client.get("/")
        assert r.status_code == 200
        print(f"    {r.json()['message']}")

        # 3. Cadastrar Marcel
        print("\n[E2E] 3. Cadastrando cliente Marcel")
        r = await client.post("/clientes/", json={
            "nome": "Marcel",
            "sobrenome": "Liguili",
            "telefone": "(11) 99999-8888",
            "email": "marcel@email.com",
            "endereco": "Rua Exemplo, 123",
            "cep": "01234-567",
        }, headers=headers)
        assert r.status_code == 201, f"Erro: {r.text}"
        cliente_id = r.json()["id"]
        print(f"    Cliente ID {cliente_id} - Marcel Liguili")

        # 4. Listar clientes
        print("\n[E2E] 4. Localizando Marcel na lista")
        r = await client.get("/clientes/", headers=headers)
        assert r.status_code == 200
        assert any("Marcel" in c["nome"] for c in r.json())
        print("    OK")

        # 5. Cadastrar moldura
        cod_moldura = f"MDR-E2E-{int(time.time())}"
        print(f"\n[E2E] 5. Cadastrando moldura {cod_moldura}")
        r = await client.post("/estoque/molduras", json={
            "codigo": cod_moldura,
            "quantidade": 50,
            "preco_venda": 45.90,
            "preco_custo": 22.50,
            "cor": "Preto Fosco",
            "tamanho_barra": 2.5,
            "largura_barra": 3.0,
            "marca": "Marca Exemplo",
        }, headers=headers)
        assert r.status_code == 201, f"Erro: {r.text}"
        moldura_id = r.json()["id"]
        print(f"    Moldura ID {moldura_id} - {r.json()['codigo']} ({r.json()['cor']})")

        # 6. Criar pedido para Marcel
        print("\n[E2E] 6. Criando pedido para Marcel")
        r = await client.post("/pedidos/", json={
            "cliente_id": cliente_id,
            "itens": [{
                "descricao": "Quadro 50x70cm",
                "moldura_id": moldura_id,
                "quantidade": 1,
                "largura": 50.0,
                "altura": 70.0,
                "preco_unitario": 45.90,
            }],
            "valor_sinal": 20.00,
            "endereco_entrega": "Rua Exemplo, 123",
            "frete": 15.00,
        }, headers=headers)
        assert r.status_code == 201, f"Erro: {r.text}"
        p = r.json()
        print(f"    Pedido N {p['numero_pedido']} | R$ {p['valor_total']} | Sinal R$ {p['valor_sinal']}")
        assert p["status_geral"] == "rascunho"

        # 7. Listar pedidos
        print("\n[E2E] 7. Listando pedidos")
        r = await client.get("/pedidos/", headers=headers)
        assert r.status_code == 200
        print(f"    {len(r.json())} pedido(s) encontrado(s)")

        # 8. Detalhes do pedido
        print(f"\n[E2E] 8. Detalhes do pedido {p['id']}")
        r = await client.get(f"/pedidos/{p['id']}", headers=headers)
        assert r.status_code == 200
        d = r.json()
        print(f"    N: {d['numero_pedido']}, Itens: {len(d['itens'])}, Eventos: {len(d['eventos'])}")

        # 9. Verificar estoque
        print("\n[E2E] 9. Estoque de molduras")
        r = await client.get("/estoque/molduras", headers=headers)
        assert r.status_code == 200
        print(f"    {len(r.json())} moldura(s) cadastrada(s)")

        # 10. Testar frontend via Docker
        print("\n[E2E] 10. Acessando frontend (porta 80)")
        r = await client.get("http://localhost:80/")
        print(f"    Frontend: HTTP {r.status_code}")

        print("\n[E2E] FLUXO E2E COMPLETO VIA DOCKER - SUCESSO!\n")
