from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./atividros.db"
    chave_secreta: str = "sua_chave_secreta_super_segura_aqui"
    algoritmo_jwt: str = "HS256"
    minutos_expiracao_token: int = 60 * 24
    debug: bool = True

    model_config = {"env_file": ".env"}


settings = Settings()
