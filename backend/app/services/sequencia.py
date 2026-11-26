import asyncio
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

ATRASOS_LOCK_SQLITE = (0.05, 0.1, 0.2)


def obter_ano_atual_loja() -> int:
    """
    Retorna o ano corrente considerando o fuso horário da loja (America/Sao_Paulo).
    """
    try:
        fuso = ZoneInfo("America/Sao_Paulo")
    except ZoneInfoNotFoundError:
        fuso = timezone(timedelta(hours=-3))
    return datetime.now(fuso).year


async def gerar_numero_pedido(db: AsyncSession, ano: int | None = None) -> str:
    """
    Gera o próximo número sequencial anual (YYYYNNNNN) de forma atômica compatível com SQLite e PostgreSQL.
    """
    ano_efetivo = ano if ano is not None else obter_ano_atual_loja()
    dialeto = db.bind.dialect.name if db.bind is not None else ""

    stmt_upsert = text(
        "INSERT INTO sequencia_numeracao (ano, ultimo_valor) "
        "VALUES (:ano, 1) "
        "ON CONFLICT (ano) DO UPDATE "
        "SET ultimo_valor = sequencia_numeracao.ultimo_valor + 1 "
        "RETURNING ultimo_valor"
    )

    ultimo_erro: OperationalError | None = None
    for tentativa in range(len(ATRASOS_LOCK_SQLITE) + 1):
        try:
            if dialeto == "sqlite" and not db.in_transaction():
                await db.execute(text("BEGIN IMMEDIATE"))
            resultado = await db.execute(stmt_upsert, {"ano": ano_efetivo})
            sequencial = int(resultado.scalar_one())
            return f"{ano_efetivo}{sequencial:05d}"
        except OperationalError as erro:
            ultimo_erro = erro
            if tentativa < len(ATRASOS_LOCK_SQLITE):
                await asyncio.sleep(ATRASOS_LOCK_SQLITE[tentativa])
                continue
            raise

    assert ultimo_erro is not None
    raise ultimo_erro
