import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.usuario import Usuario
from app.services.autenticacao import obter_hash_senha


async def criar_administrador():
    db_url = settings.database_url
    print(f"Conectando ao banco em {db_url}...")
    engine = create_async_engine(db_url)
    sessao_async = async_sessionmaker(engine, expire_on_commit=False)

    async with sessao_async() as sessao:
        print("Buscando usuário administrador...")
        try:
            resultado = await sessao.execute(select(Usuario).where(Usuario.nome_usuario == "admin"))
            usuario = resultado.scalar_one_or_none()

            if usuario:
                print("Usuário administrador já existe.")
                return

            print("Criando novo usuário administrador...")
            novo_usuario = Usuario(
                nome_usuario="admin",
                senha_hash=obter_hash_senha("admin123"),
                nome_completo="Administrador Sistema",
                esta_ativo=True,
            )
            sessao.add(novo_usuario)
            await sessao.commit()
            print("Usuário administrador criado com sucesso!")
        except Exception as e:
            print(f"Erro ao criar administrador: {e}")
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(criar_administrador())
