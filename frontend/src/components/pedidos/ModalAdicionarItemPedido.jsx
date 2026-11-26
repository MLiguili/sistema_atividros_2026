import React, { useState } from 'react';
import api from '../../api/config';
import Dialog from '../ui/Dialog';
import Button from '../ui/Button';
import Field from '../ui/Field';
import Callout from '../ui/Callout';
import FormComposicaoQuadro from '../calculadora/FormComposicaoQuadro';
import PainelResultadoCalculo from '../calculadora/PainelResultadoCalculo';

const DADOS_INICIAIS = {
  obra_largura: '50',
  obra_altura: '40',
  quantidade: '1',
  paspatour: false,
  tamanho_paspatour: '5',
  paspatour_id: '',
  molduras: [],
  vidro_tipo: '',
  vidro_id: '',
  fundo_tipo: '',
  fundo_id: '',
  mao_de_obra: '0.00',
};

/**
 * Modal unificado para adicionar Quadro Sob Medida, Vidro Avulso ou Serviço Livre a um pedido.
 *
 * @param {{
 *   open: boolean,
 *   onClose: () => void,
 *   catalogos: { molduras: Array, vidros: Array, fundos: Array, tabelaVidro: Array, tabelaFundo: Array, tabelaPaspatour: Array },
 *   onAdicionarItem: (item: object) => void
 * }} props Propriedades do modal.
 * @returns {JSX.Element | null} Modal de adição de item.
 */
const ModalAdicionarItemPedido = ({ open, onClose, catalogos, onAdicionarItem }) => {
  const [tipo, setTipo] = useState('quadro_sob_medida');
  const [dados, setDados] = useState({
    ...DADOS_INICIAIS,
    vidro_tipo: catalogos.tabelaVidro?.[0]?.tipo || '',
    paspatour_id: catalogos.tabelaPaspatour?.[0] ? String(catalogos.tabelaPaspatour[0].id) : '',
  });
  const [resultado, setResultado] = useState(null);
  const [servicoLivre, setServicoLivre] = useState({
    descricao: '',
    quantidade: '1',
    preco_unitario: '',
  });
  const [erro, setErro] = useState('');
  const [calculando, setCalculando] = useState(false);

  const calcular = async () => {
    setErro('');
    if (!dados.obra_largura || !dados.obra_altura || Number(dados.obra_largura) <= 0 || Number(dados.obra_altura) <= 0) {
      setErro('Informe largura e altura válidas maiores que zero.');
      return;
    }
    setCalculando(true);
    try {
      const resp =
        tipo === 'vidro_avulso'
          ? await api.post('/calculadora/vidro-avulso', {
              largura: parseFloat(dados.obra_largura),
              altura: parseFloat(dados.obra_altura),
              quantidade: parseInt(dados.quantidade || '1', 10),
              vidro_tipo: dados.vidro_tipo || 'incolor',
              vidro_id: dados.vidro_id ? parseInt(dados.vidro_id, 10) : null,
              mao_de_obra: parseFloat(dados.mao_de_obra || '0'),
            })
          : await api.post('/calculadora/quadro', {
              obra_largura: parseFloat(dados.obra_largura),
              obra_altura: parseFloat(dados.obra_altura),
              quantidade: parseInt(dados.quantidade || '1', 10),
              paspatour: Boolean(dados.paspatour),
              tamanho_paspatour: dados.paspatour ? parseFloat(dados.tamanho_paspatour || '0') : 0,
              paspatour_id: dados.paspatour && dados.paspatour_id ? parseInt(dados.paspatour_id, 10) : null,
              molduras: dados.molduras
                .filter((m) => m.moldura_id)
                .map((m, idx) => ({ moldura_id: parseInt(m.moldura_id, 10), ordem: idx })),
              vidro_tipo: dados.vidro_tipo || null,
              vidro_id: dados.vidro_id ? parseInt(dados.vidro_id, 10) : null,
              fundo_tipo: dados.fundo_tipo || null,
              fundo_id: dados.fundo_id ? parseInt(dados.fundo_id, 10) : null,
              mao_de_obra: parseFloat(dados.mao_de_obra || '0'),
            });
      setResultado(resp.data);
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao calcular item.');
    } finally {
      setCalculando(false);
    }
  };

  const confirmarCalculado = () => {
    if (!resultado) return;
    onAdicionarItem({
      tipo_item: tipo,
      descricao: resultado.descricao_sugerida,
      quantidade: parseInt(dados.quantidade || '1', 10),
      valor_sugerido: Number(resultado.valor_sugerido_unitario),
      preco_unitario: Number(resultado.valor_sugerido_unitario),
      obra_largura: parseFloat(dados.obra_largura),
      obra_altura: parseFloat(dados.obra_altura),
      paspatour: tipo === 'quadro_sob_medida' ? Boolean(dados.paspatour) : false,
      tamanho_paspatour:
        tipo === 'quadro_sob_medida' && dados.paspatour ? parseFloat(dados.tamanho_paspatour || '0') : 0,
      paspatour_id:
        tipo === 'quadro_sob_medida' && dados.paspatour && dados.paspatour_id
          ? parseInt(dados.paspatour_id, 10)
          : null,
      vidro_tipo: dados.vidro_tipo || null,
      vidro_id: dados.vidro_id ? parseInt(dados.vidro_id, 10) : null,
      fundo_tipo: tipo === 'quadro_sob_medida' ? dados.fundo_tipo || null : null,
      fundo_id: tipo === 'quadro_sob_medida' && dados.fundo_id ? parseInt(dados.fundo_id, 10) : null,
      mao_de_obra: parseFloat(dados.mao_de_obra || '0'),
      molduras:
        tipo === 'quadro_sob_medida'
          ? dados.molduras
              .filter((m) => m.moldura_id)
              .map((m, idx) => ({ moldura_id: parseInt(m.moldura_id, 10), ordem: idx }))
          : [],
    });
    setResultado(null);
    onClose();
  };

  const confirmarServicoLivre = (e) => {
    e.preventDefault();
    if (!servicoLivre.descricao.trim() || servicoLivre.preco_unitario === '') {
      setErro('Informe descrição e preço unitário para serviço livre.');
      return;
    }
    const preco = Number(servicoLivre.preco_unitario);
    onAdicionarItem({
      tipo_item: 'servico_livre',
      descricao: servicoLivre.descricao.trim(),
      quantidade: parseInt(servicoLivre.quantidade || '1', 10),
      valor_sugerido: preco,
      preco_unitario: preco,
      molduras: [],
    });
    setServicoLivre({ descricao: '', quantidade: '1', preco_unitario: '' });
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} title="Adicionar Item ao Pedido" size="lg">
      <div className="at-segmented" role="group" aria-label="Modalidade do item" style={{ marginBottom: 'var(--at-space-4)' }}>
        <button
          type="button"
          className="at-segmented__btn"
          aria-pressed={tipo !== 'servico_livre'}
          onClick={() => {
            setTipo('quadro_sob_medida');
            setErro('');
          }}
        >
          Calculado (Quadro / Vidro)
        </button>
        <button
          type="button"
          className="at-segmented__btn"
          aria-pressed={tipo === 'servico_livre'}
          onClick={() => {
            setTipo('servico_livre');
            setErro('');
          }}
        >
          Serviço Livre
        </button>
      </div>

      {erro && <Callout variant="danger">{erro}</Callout>}

      {tipo === 'servico_livre' ? (
        <form onSubmit={confirmarServicoLivre} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-3)' }}>
          <Field id="srv-desc" label="Descrição do Serviço / Produto" required>
            <input
              id="srv-desc"
              className="at-input"
              required
              placeholder="Ex.: Instalação em residência, troca de dobradiça..."
              value={servicoLivre.descricao}
              onChange={(e) => setServicoLivre({ ...servicoLivre, descricao: e.target.value })}
            />
          </Field>
          <div className="at-grid-2">
            <Field id="srv-qtd" label="Quantidade" required>
              <input
                id="srv-qtd"
                type="number"
                min="1"
                className="at-input at-num"
                value={servicoLivre.quantidade}
                onChange={(e) => setServicoLivre({ ...servicoLivre, quantidade: e.target.value })}
              />
            </Field>
            <Field id="srv-preco" label="Valor Unitário (R$)" required>
              <input
                id="srv-preco"
                type="number"
                step="0.01"
                min="0"
                className="at-input at-num"
                value={servicoLivre.preco_unitario}
                onChange={(e) => setServicoLivre({ ...servicoLivre, preco_unitario: e.target.value })}
              />
            </Field>
          </div>
          <div className="at-actions" style={{ justifyContent: 'flex-end' }}>
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary">
              Inserir no Pedido
            </Button>
          </div>
        </form>
      ) : (
        <div className="at-calc-grid">
          <FormComposicaoQuadro
            modo={tipo}
            onChangeModo={(novo) => {
              setTipo(novo);
              setResultado(null);
            }}
            dados={dados}
            onChangeDados={setDados}
            catalogos={catalogos}
            onCalcular={calcular}
            calculando={calculando}
          />
          <PainelResultadoCalculo
            resultado={resultado}
            quantidade={dados.quantidade}
            onLimpar={() => setResultado(null)}
            onAdicionarAoPedido={confirmarCalculado}
            textoBotaoAdicionar="Inserir no Pedido"
          />
        </div>
      )}
    </Dialog>
  );
};

export default ModalAdicionarItemPedido;
