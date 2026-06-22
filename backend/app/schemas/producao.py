from pydantic import BaseModel


class IniciarProducao(BaseModel):
    pedido_ids: list[int]


class ResultadoBatch(BaseModel):
    pedido_id: int
    sucesso: bool
    mensagem: str


class ResumoProducao(BaseModel):
    pendente: int = 0
    aguardando_material: int = 0
    em_producao: int = 0
    para_embalar: int = 0
    pronto_entrega: int = 0
    entregue: int = 0
    total: int = 0
