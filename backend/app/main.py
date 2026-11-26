import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import autenticacao, calculadora, clientes, estoque, pedidos
from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

CHAVE_SECRETA_PADRAO = "sua_chave_secreta_super_segura_aqui"


def validar_configuracao_seguranca() -> None:
    """
    Valida que a chave secreta JWT atende aos requisitos mínimos fora do modo debug.
    """
    if not settings.debug and (
        settings.chave_secreta == CHAVE_SECRETA_PADRAO or len(settings.chave_secreta) < 32
    ):
        raise RuntimeError(
            "CHAVE_SECRETA insegura: defina uma chave com pelo menos 32 caracteres quando debug=False."
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação FastAPI validando segurança na inicialização.
    """
    validar_configuracao_seguranca()
    yield


app = FastAPI(
    title="Sistema Atividros",
    description="API para gestão de loja de quadros e vidros",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(autenticacao.router)
app.include_router(estoque.router)
app.include_router(clientes.router)
app.include_router(pedidos.router)
app.include_router(calculadora.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def manipulador_erro_interno(request: Request, exc: Exception) -> JSONResponse:
    """
    Captura exceções não tratadas e retorna resposta HTTP 500 sanitizada sem vazar detalhes internos.
    """
    logger.exception("Erro interno não tratado na rota %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno no servidor"})


@app.get("/")
async def root():
    """
    Endpoint de saudação e verificação de integridade.
    """
    return {"message": "Bem-vindo ao Sistema Atividros API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
