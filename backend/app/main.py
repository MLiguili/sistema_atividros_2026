from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import autenticacao, calculadora, clientes, estoque, pedidos

app = FastAPI(
    title="Sistema Atividros",
    description="API para gestão de loja de quadros e vidros",
    version="0.1.0"
)

app.include_router(autenticacao.router)
app.include_router(estoque.router)
app.include_router(clientes.router)
app.include_router(pedidos.router)
app.include_router(calculadora.router)






# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restringir ao domínio do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """
    Endpoint de saudação e verificação de integridade.
    """
    return {"message": "Bem-vindo ao Sistema Atividros API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
