import logging
from decimal import Decimal

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from app.models.pedido import Pedido, StatusGeral, TipoDesconto, TipoItemPedido

logger = logging.getLogger(__name__)

SUBSTITUICOES_LATIN1 = {
    "•": "-",
    "—": "-",
    "–": "-",
    "×": "x",
    "→": "->",
    "←": "<-",
    "⇄": "<->",
    "²": "2",
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
}


def sanitizar_texto_pdf(texto: object) -> str:
    """
    Normaliza caracteres fora do padrão Latin-1 para evitar falhas de codificação na fonte Helvetica do FPDF2.
    """
    conteudo = str(texto if texto is not None else "")
    for origem, destino in SUBSTITUICOES_LATIN1.items():
        conteudo = conteudo.replace(origem, destino)
    return conteudo.encode("latin-1", "replace").decode("latin-1")


def formatar_moeda_pdf(valor: Decimal | float | int) -> str:
    """
    Formata valores numéricos em padrão monetário brasileiro (R$ X.XXX,XX).
    """
    num = Decimal(str(valor or 0))
    formatado = f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatado}"


class GeradorPDFPedido(FPDF):
    """
    Gerador do documento PDF Único A4 do Atividros adaptável ao status comercial do pedido.
    """

    def __init__(self, pedido: Pedido):
        """
        Inicializa o documento A4 em memória com os dados completos do pedido.
        """
        super().__init__(orientation="P", unit="mm", format="A4")
        self.pedido = pedido
        self.set_auto_page_break(auto=True, margin=18)

    def header(self) -> None:
        """
        Renderiza o cabeçalho institucional e banner contextual (Orçamento / OS / Cancelado).
        """
        self.set_font("helvetica", "B", 15)
        self.cell(
            0,
            8,
            sanitizar_texto_pdf("ATIVIDROS - Molduras, Vidros e Espelhos"),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="L",
        )

        status_geral = self.pedido.status_geral
        if status_geral == StatusGeral.rascunho:
            titulo = f"ORÇAMENTO #{self.pedido.numero_pedido}"
            data_ref = (
                f"Validade: {self.pedido.data_validade_orcamento.strftime('%d/%m/%Y')}"
                if self.pedido.data_validade_orcamento
                else "Validade: A combinar"
            )
            self.set_fill_color(245, 240, 225)
            self.set_text_color(120, 75, 10)
        elif status_geral == StatusGeral.cancelado:
            titulo = f"PEDIDO CANCELADO #{self.pedido.numero_pedido}"
            data_ref = "Status: CANCELADO"
            self.set_fill_color(250, 230, 232)
            self.set_text_color(160, 25, 35)
        else:
            titulo = f"PEDIDO / ORDEM DE SERVIÇO #{self.pedido.numero_pedido}"
            data_ref = (
                f"Prazo de Entrega: {self.pedido.prazo_entrega.strftime('%d/%m/%Y')}"
                if self.pedido.prazo_entrega
                else "Prazo de Entrega: A combinar"
            )
            self.set_fill_color(230, 242, 238)
            self.set_text_color(10, 85, 65)

        self.set_font("helvetica", "B", 11)
        self.cell(125, 9, sanitizar_texto_pdf(f" {titulo}"), border=1, fill=True, align="L")
        self.cell(65, 9, sanitizar_texto_pdf(f"{data_ref} "), border=1, fill=True, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_text_color(40, 40, 40)
        self.set_font("helvetica", "", 9)
        emissao = self.pedido.criado_em.strftime("%d/%m/%Y %H:%M") if self.pedido.criado_em else "N/A"
        situacao = f"Emissão: {emissao}  |  Geral: {self.pedido.status_geral.value}  |  Produção: {self.pedido.status_producao.value}"
        self.cell(0, 6, sanitizar_texto_pdf(situacao), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def footer(self) -> None:
        """
        Renderiza rodapé padrão com numeração de página.
        """
        self.set_y(-13)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, sanitizar_texto_pdf(f"ATIVIDROS · Página {self.page_no()}/{{nb}}"), align="C")

    def _linhas_tecnicas_item(self, item) -> list[str]:
        """
        Extrai as medidas técnicas imutáveis de corte do snapshot sem incluir valores internos sigilosos.
        """
        linhas: list[str] = []
        if item.tipo_item == TipoItemPedido.servico_livre:
            return linhas

        snap = item.snapshot_calculo if isinstance(item.snapshot_calculo, dict) else {}
        dim = snap.get("dimensoes") if isinstance(snap, dict) else None
        if isinstance(dim, dict):
            obra = dim.get("obra") or {}
            vidro = dim.get("vidro") or {}
            final = dim.get("quadro_final") or {}
            molduras = dim.get("molduras") or []

            if item.tipo_item == TipoItemPedido.vidro_avulso:
                linhas.append(
                    f"  - Corte Vidro/Espelho ({item.vidro_tipo or '-'}): {obra.get('largura', '-')} x {obra.get('altura', '-')} cm"
                )
                return linhas

            linhas.append(f"  - Obra: {obra.get('largura', '-')} x {obra.get('altura', '-')} cm")
            if item.paspatour:
                linhas.append(f"  - Paspatour: {item.tamanho_paspatour} cm")
            if item.vidro_tipo or item.fundo_tipo:
                linhas.append(
                    f"  - Vidro/Fundo ({item.vidro_tipo or '-'} / {item.fundo_tipo or '-'}): {vidro.get('largura', '-')} x {vidro.get('altura', '-')} cm"
                )
            for idx, m in enumerate(molduras, start=1):
                linhas.append(
                    f"  - Moldura {idx} ({m.get('codigo')}, {m.get('largura_barra_cm')}cm): corte {m.get('largura')} x {m.get('altura')} cm"
                )
            linhas.append(f"  - QUADRO FINAL: {final.get('largura', '-')} x {final.get('altura', '-')} cm")
        elif item.obra_largura is not None and item.obra_altura is not None:
            linhas.append(f"  - Medidas: {item.obra_largura} x {item.obra_altura} cm")

        return linhas

    def gerar_pdf(self) -> bytes:
        """
        Compõe todas as seções do documento A4 e retorna os bytes do arquivo PDF gerado.
        """
        self.alias_nb_pages()
        self.add_page()
        self.set_text_color(20, 20, 20)

        # Dados do Cliente e Entrega
        self.set_font("helvetica", "B", 10)
        self.cell(0, 6, sanitizar_texto_pdf("DADOS DO CLIENTE E ENTREGA"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

        self.set_font("helvetica", "", 9)
        if self.pedido.cliente:
            cli = self.pedido.cliente
            self.cell(105, 5, sanitizar_texto_pdf(f"Cliente: {cli.nome} {cli.sobrenome}"), new_x=XPos.RIGHT)
            self.cell(85, 5, sanitizar_texto_pdf(f"Telefone: {cli.telefone}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.cell(105, 5, sanitizar_texto_pdf(f"E-mail: {cli.email or 'N/A'}"), new_x=XPos.RIGHT)
            self.cell(85, 5, sanitizar_texto_pdf(f"CEP: {cli.cep or 'N/A'}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.multi_cell(0, 5, sanitizar_texto_pdf(f"Endereço Cliente: {cli.endereco or 'N/A'}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            self.cell(0, 5, sanitizar_texto_pdf("Cliente não identificado"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        if self.pedido.endereco_entrega:
            self.multi_cell(
                0,
                5,
                sanitizar_texto_pdf(f"Endereço de Entrega: {self.pedido.endereco_entrega}"),
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
        self.ln(3)

        # Tabela de Itens e Medidas Técnicas
        self.set_font("helvetica", "B", 10)
        self.cell(0, 6, sanitizar_texto_pdf("ITENS E MEDIDAS TÉCNICAS"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("helvetica", "B", 9)
        self.set_fill_color(235, 238, 242)
        self.cell(112, 7, sanitizar_texto_pdf("Item / Composição e Medidas de Corte"), border=1, fill=True)
        self.cell(16, 7, "Qtd", border=1, fill=True, align="C")
        self.cell(31, 7, sanitizar_texto_pdf("Unitário"), border=1, fill=True, align="R")
        self.cell(31, 7, "Subtotal", border=1, fill=True, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        for idx, item in enumerate(self.pedido.itens, start=1):
            linhas_tec = self._linhas_tecnicas_item(item)
            altura_estimada = 8 + (len(linhas_tec) * 4.5)
            if self.get_y() + altura_estimada > 268:
                self.add_page()

            self.set_font("helvetica", "B", 9)
            y_inicio = self.get_y()
            self.multi_cell(
                112,
                5.5,
                sanitizar_texto_pdf(f"{idx}. {item.descricao}"),
                border="LTR",
                new_x=XPos.RIGHT,
                new_y=YPos.TOP,
            )
            y_apos_desc = self.get_y()
            altura_titulo = max(5.5, y_apos_desc - y_inicio)
            self.set_xy(122, y_inicio)
            self.set_font("helvetica", "", 9)
            self.cell(16, altura_titulo, str(item.quantidade), border="LTR", align="C")
            self.cell(31, altura_titulo, formatar_moeda_pdf(item.preco_unitario), border="LTR", align="R")
            self.cell(
                31,
                altura_titulo,
                formatar_moeda_pdf(item.subtotal),
                border="LTR",
                align="R",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )

            if linhas_tec:
                self.set_font("helvetica", "", 8)
                texto_tec = "\n".join(linhas_tec)
                y_tec = self.get_y()
                self.multi_cell(112, 4.3, sanitizar_texto_pdf(texto_tec), border="LBR", new_x=XPos.RIGHT, new_y=YPos.TOP)
                alt_tec = self.get_y() - y_tec
                self.set_xy(122, y_tec)
                self.cell(16, alt_tec, "", border="LBR")
                self.cell(31, alt_tec, "", border="LBR")
                self.cell(31, alt_tec, "", border="LBR", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            else:
                self.line(10, self.get_y(), 200, self.get_y())

        self.ln(4)

        # Resumo Financeiro
        if self.get_y() > 220:
            self.add_page()

        self.set_font("helvetica", "B", 10)
        self.cell(0, 6, sanitizar_texto_pdf("RESUMO FINANCEIRO"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

        desconto_calc = Decimal(str(self.pedido.desconto_valor or 0))
        rotulo_desc = "Desconto (-)"
        if self.pedido.desconto_tipo == TipoDesconto.percentual:
            rotulo_desc = f"Desconto (- {desconto_calc:.2f}%)"
            desconto_calc = (Decimal(str(self.pedido.subtotal_itens)) * desconto_calc) / Decimal("100")

        self.set_font("helvetica", "", 9)
        self.cell(150, 5.5, "Subtotal dos itens:", align="R")
        self.cell(40, 5.5, formatar_moeda_pdf(self.pedido.subtotal_itens), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.cell(150, 5.5, "Frete (+):", align="R")
        self.cell(40, 5.5, formatar_moeda_pdf(self.pedido.frete), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.cell(150, 5.5, sanitizar_texto_pdf(f"{rotulo_desc}:"), align="R")
        self.cell(40, 5.5, f"- {formatar_moeda_pdf(desconto_calc)}", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font("helvetica", "B", 10)
        self.cell(150, 6.5, "TOTAL DO PEDIDO:", align="R")
        self.cell(40, 6.5, formatar_moeda_pdf(self.pedido.valor_total), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font("helvetica", "", 9)
        self.cell(150, 5.5, "Total Pago:", align="R")
        self.cell(40, 5.5, formatar_moeda_pdf(self.pedido.valor_pago), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font("helvetica", "B", 10)
        if self.pedido.status_geral == StatusGeral.cancelado:
            self.cell(
                0,
                7,
                sanitizar_texto_pdf("STATUS: CANCELADO (SEM COBRANÇA ATIVA)"),
                align="R",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            if Decimal(str(self.pedido.valor_pago)) > Decimal("0.00"):
                self.set_font("helvetica", "I", 9)
                self.cell(
                    0,
                    5.5,
                    sanitizar_texto_pdf(
                        f"Atenção: estorno pendente referente ao total pago de {formatar_moeda_pdf(self.pedido.valor_pago)}."
                    ),
                    align="R",
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                )
        else:
            self.cell(150, 6.5, "SALDO DEVEDOR:", align="R")
            self.cell(40, 6.5, formatar_moeda_pdf(self.pedido.saldo_devedor), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Pagamentos registrados
        pagamentos_ativos = [p for p in (self.pedido.pagamentos or []) if not p.estornado]
        if pagamentos_ativos:
            self.ln(2)
            self.set_font("helvetica", "B", 9)
            self.cell(0, 5.5, sanitizar_texto_pdf("Pagamentos Registrados:"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_font("helvetica", "", 8.5)
            for pag in pagamentos_ativos:
                dt = pag.data_pagamento.strftime("%d/%m/%Y") if pag.data_pagamento else ""
                obs = f" ({pag.observacao})" if pag.observacao else ""
                self.cell(
                    0,
                    4.8,
                    sanitizar_texto_pdf(f"- {dt} | {pag.forma_pagamento.value} | {formatar_moeda_pdf(pag.valor)}{obs}"),
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                )

        # Observações
        if self.pedido.observacoes:
            self.ln(3)
            self.set_font("helvetica", "B", 9)
            self.cell(0, 5.5, sanitizar_texto_pdf("Observações:"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_font("helvetica", "", 9)
            self.multi_cell(0, 5, sanitizar_texto_pdf(self.pedido.observacoes), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Assinaturas
        self.ln(10)
        if self.get_y() > 260:
            self.add_page()
            self.ln(10)

        self.set_font("helvetica", "", 8.5)
        y_ass = self.get_y()
        self.line(12, y_ass, 95, y_ass)
        self.line(115, y_ass, 198, y_ass)
        self.cell(95, 5, sanitizar_texto_pdf("Assinatura do Cliente / Aprovação"), align="C", new_x=XPos.RIGHT)
        self.cell(95, 5, sanitizar_texto_pdf("Conferência Oficina  |  ___/___/____"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        return bytes(self.output())


def gerar_binary_pdf(pedido: Pedido) -> bytes:
    """
    Gera em memória os bytes do documento PDF Único A4 para o pedido informado.
    """
    logger.info("Gerando PDF para pedido %s", pedido.numero_pedido)
    pdf = GeradorPDFPedido(pedido)
    return pdf.gerar_pdf()
