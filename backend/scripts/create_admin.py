import asyncio
import getpass
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models.usuario import Usuario
from app.services.autenticacao import obter_hash_senha


def obter_senha_inicial() -> str:
    """
    Obtém a senha inicial do administrador via variável de ambiente, prompt interativo ou fallback seguro em debug.
    """
    senha = os.getenv("ADMIN_INITIAL_PASSWORD")
    if senha:
        return senha

    if sys.stdin.isatty():
        senha = getpass.getpass("Digite a senha inicial para o usuário administrador: ").strip()
        if senha:
            return senha

    if settings.debug:
        print(
            "AVISO (modo debug): ADMIN_INITIAL_PASSWORD não definida; utilizando senha padrão de desenvolvimento."
        )
        return "admin123"

    raise RuntimeError(
        "ADMIN_INITIAL_PASSWORD obrigatória quando debug=False em execução não interativa."
    )


async def criar_administrador() -> None:
    """
    Cria o usuário administrador inicial caso ainda não exista no banco de dados configurado.
    """
    print("Conectando ao banco de dados configurado...")
    engine = create_async_engine(settings.database_url)
    sessao_async = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with sessao_async() as sessao:
            print("Buscando usuário administrador...")
            resultado = await sessao.execute(select(Usuario).where(Usuario.nome_usuario == "admin"))
            usuario = resultado.scalar_one_or_none()

            if usuario:
                print("Usuário administrador já existe.")
                return

            senha_inicial = obter_senha_inicial()
            print("Criando novo usuário administrador...")
            novo_usuario = Usuario(
                nome_usuario="admin",
                senha_hash=obter_hash_senha(senha_inicial),
                nome_completo="Administrador Sistema",
                esta_ativo=True,
            )
            sessao.add(novo_usuario)
            await sessao.commit()
            print("Usuário administrador criado com sucesso!")
    except Exception as erro:
        print(f"Erro ao criar administrador: {erro}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(criar_administrador())
