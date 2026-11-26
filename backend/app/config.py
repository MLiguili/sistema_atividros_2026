import json
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    """
    Configurações centrais da aplicação carregadas a partir de variáveis de ambiente.
    """

    database_url: str = "sqlite+aiosqlite:///./atividros.db"
    chave_secreta: str = "sua_chave_secreta_super_segura_aqui"
    algoritmo_jwt: str = "HS256"
    minutos_expiracao_token: int = 60 * 24
    debug: bool = True
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    log_level: str = "INFO"

    model_config = {"env_file": ".env"}

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, valor: object) -> list[str]:
        """
        Converte uma lista, JSON array ou string separada por vírgulas em lista de origens CORS.
        """
        if isinstance(valor, list):
            return [str(item).strip() for item in valor if str(item).strip()]
        if isinstance(valor, str):
            texto = valor.strip()
            if not texto:
                return []
            if texto.startswith("["):
                carregado = json.loads(texto)
                if isinstance(carregado, list):
                    return [str(item).strip() for item in carregado if str(item).strip()]
            return [parte.strip() for parte in texto.split(",") if parte.strip()]
        raise ValueError("cors_origins deve ser uma lista ou string separada por vírgulas")


settings = Settings()
