import logging

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from app.models.pedido import Pedido

logger = logging.getLogger(__name__)


class GeradorPDFPedido(FPDF):
    def __init__(self, pedido: Pedido):
        super().__init__()
        self.pedido = pedido

    def header(self):
        # Título
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "ATIVIDROS - ORÇAMENTO / PEDIDO", border=False, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.set_font("helvetica", "", 10)
        self.cell(0, 5, "Gestão de Quadros e Vidros", border=False, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.ln(10)

    def footer(self):
        # Rodapé com número de página
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")

    def gerar_pdf(self) -> bytes:
        self.add_page()
        self.alias_nb_pages()

        # Dados do Pedido
        self.set_font("helvetica", "B", 12)
        self.cell(0, 10, f"Pedido #{self.pedido.numero_pedido}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("helvetica", "", 10)

        data_criacao = self.pedido.criado_em.strftime("%d/%m/%Y %H:%M") if self.pedido.criado_em else "N/A"
        self.cell(0, 5, f"Data: {data_criacao}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        status = f"{self.pedido.status_geral.value} | {self.pedido.status_producao.value} | {self.pedido.status_financeiro.value}"
        self.cell(0, 5, f"Status: {status}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(5)

        # Dados do Cliente
        self.set_font("helvetica", "B", 11)
        self.cell(0, 8, "DADOS DO CLIENTE", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=False)
        self.set_font("helvetica", "", 10)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

        if self.pedido.cliente:
            cliente = self.pedido.cliente
            self.cell(0, 5, f"Nome: {cliente.nome} {cliente.sobrenome or ''}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.cell(0, 5, f"Telefone: {cliente.telefone or 'N/A'}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.cell(0, 5, f"Email: {cliente.email or 'N/A'}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.cell(0, 5, f"Endereço: {cliente.endereco or 'N/A'}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            self.cell(0, 5, "Cliente não identificado", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(5)

        # Itens do Pedido
        self.set_font("helvetica", "B", 11)
        self.cell(0, 8, "ITENS DO PEDIDO", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

        # Cabeçalho da Tabela
        self.set_font("helvetica", "B", 9)
        self.set_fill_color(240, 240, 240)
        self.cell(80, 7, "Descrição", border=1, fill=True)
        self.cell(20, 7, "Qtd", border=1, fill=True, align="C")
        self.cell(30, 7, "Medidas (cm)", border=1, fill=True, align="C")
        self.cell(30, 7, "Unitário", border=1, fill=True, align="R")
        self.cell(30, 7, "Subtotal", border=1, fill=True, align="R")
        self.ln()

        self.set_font("helvetica", "", 9)
        for item in self.pedido.itens:
            desc = []
            if item.moldura:
                desc.append(f"M:{item.moldura.codigo}")
            if item.vidro:
                desc.append(f"V:{item.vidro.tipo}")
            if item.fundo:
                desc.append(f"F:{item.fundo.tipo}")
            desc_str = " | ".join(desc) if desc else "Quadro Personalizado"

            self.cell(80, 7, desc_str, border=1)
            self.cell(20, 7, str(item.quantidade), border=1, align="C")
            self.cell(30, 7, f"{item.largura}x{item.altura}", border=1, align="C")
            self.cell(30, 7, f"R$ {float(item.preco_unitario):,.2f}", border=1, align="R")
            self.cell(30, 7, f"R$ {float(item.subtotal):,.2f}", border=1, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Total
        self.ln(5)
        self.set_font("helvetica", "B", 12)
        self.cell(160, 10, "TOTAL DO PEDIDO:", align="R")
        self.cell(30, 10, f"R$ {float(self.pedido.valor_total):,.2f}", align="R")

        return bytes(self.output())

def gerar_binary_pdf(pedido: Pedido) -> bytes:
    logger.debug("Gerando PDF para pedido %s", pedido.numero_pedido)
    pdf = GeradorPDFPedido(pedido)
    return pdf.gerar_pdf()
