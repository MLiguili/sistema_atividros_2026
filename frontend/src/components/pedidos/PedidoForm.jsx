import React, { useEffect, useState } from 'react';
import { Plus, Trash2, UserPlus } from 'lucide-react';
import api from '../../api/config';
import Dialog from '../ui/Dialog';
import Button from '../ui/Button';
import Field from '../ui/Field';
import Callout from '../ui/Callout';
import ModalAdicionarItemPedido from './ModalAdicionarItemPedido';
import { calcularTotaisPreviewPedido, formatarMoeda } from '../../utils/formatadores';

/**
 * Formulário modal para criação de novo orçamento/pedido ou edição de rascunho existente.
 * Permite alteração do preço praticado abaixo do sugerido com alerta persistente não bloqueante.
 *
 * @param {{
 *   open: boolean,
 *   onClose: () => void,
 *   pedidoEdicao?: object | null,
 *   itemInicialCalculadora?: object | null,
 *   clientes: Array<object>,
 *   onClienteCriado: (cliente: object) => void,
 *   catalogos: object,
 *   onSalvo: (pedido: object) => void
 * }} props Propriedades do formulário.
 * @returns {JSX.Element | null} Formulário de pedido.
 */
const PedidoForm = ({
  open,
  onClose,
  pedidoEdicao = null,
  itemInicialCalculadora = null,
  clientes,
  onClienteCriado,
  catalogos,
  onSalvo,
}) => {
  const [clienteId, setClienteId] = useState('');
  const [prazoEntrega, setPrazoEntrega] = useState('');
  const [validadeOrcamento, setValidadeOrcamento] = useState('');
  const [enderecoEntrega, setEnderecoEntrega] = useState('');
  const [frete, setFrete] = useState('0');
  const [descontoValor, setDescontoValor] = useState('0');
  const [descontoTipo, setDescontoTipo] = useState('valor');
  const [observacoes, setObservacoes] = useState('');
  const [itens, setItens] = useState([]);
  const [modalItemAberto, setModalItemAberto] = useState(false);
  const [modalClienteAberto, setModalClienteAberto] = useState(false);
  const [novoCliente, setNovoCliente] = useState({ nome: '', telefone: '' });
  const [erro, setErro] = useState('');
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    if (!open) return;
    setErro('');
    if (pedidoEdicao) {
      setClienteId(String(pedidoEdicao.cliente_id || ''));
      setPrazoEntrega(pedidoEdicao.prazo_entrega || '');
      setValidadeOrcamento(pedidoEdicao.data_validade_orcamento || '');
      setEnderecoEntrega(pedidoEdicao.endereco_entrega || '');
      setFrete(String(pedidoEdicao.frete ?? '0'));
      setDescontoValor(String(pedidoEdicao.desconto_valor ?? '0'));
      setDescontoTipo(pedidoEdicao.desconto_tipo || 'valor');
      setObservacoes(pedidoEdicao.observacoes || '');
      const baseItens = (pedidoEdicao.itens || []).map((it) => ({
        tipo_item: it.tipo_item,
        descricao: it.descricao,
        quantidade: it.quantidade,
        valor_sugerido: Number(it.valor_sugerido),
        preco_unitario: Number(it.preco_unitario),
        obra_largura: it.obra_largura ? Number(it.obra_largura) : null,
        obra_altura: it.obra_altura ? Number(it.obra_altura) : null,
        paspatour: Boolean(it.paspatour),
        tamanho_paspatour: Number(it.tamanho_paspatour || 0),
        paspatour_id: it.paspatour_id || null,
        vidro_tipo: it.vidro_tipo || null,
        vidro_id: it.vidro_id || null,
        fundo_tipo: it.fundo_tipo || null,
        fundo_id: it.fundo_id || null,
        mao_de_obra: Number(it.mao_de_obra || 0),
        molduras: (it.molduras || []).map((m) => ({ moldura_id: m.moldura_id, ordem: m.ordem })),
      }));
      setItens(itemInicialCalculadora ? [...baseItens, itemInicialCalculadora] : baseItens);
    } else {
      setClienteId('');
      setPrazoEntrega('');
      setValidadeOrcamento('');
      setEnderecoEntrega('');
      setFrete('0');
      setDescontoValor('0');
      setDescontoTipo('valor');
      setObservacoes('');
      setItens(itemInicialCalculadora ? [itemInicialCalculadora] : []);
    }
  }, [open, pedidoEdicao, itemInicialCalculadora]);

  useEffect(() => {
    if (!open || pedidoEdicao) return;
    setClienteId((atual) => atual || (clientes[0] ? String(clientes[0].id) : ''));
  }, [open, pedidoEdicao, clientes]);

  const totais = calcularTotaisPreviewPedido(itens, frete, descontoValor, descontoTipo);
  const temItemAbaixo = itens.some((i) => Number(i.preco_unitario) < Number(i.valor_sugerido || 0));

  const criarClienteRapido = async (e) => {
    e.preventDefault();
    if (!novoCliente.nome.trim()) return;
    try {
      const resp = await api.post('/clientes/', {
        nome: novoCliente.nome.trim(),
        telefone: novoCliente.telefone.trim() || null,
      });
      onClienteCriado(resp.data);
      setClienteId(String(resp.data.id));
      setNovoCliente({ nome: '', telefone: '' });
      setModalClienteAberto(false);
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao cadastrar cliente rápido.');
    }
  };

  const salvarPedido = async (e) => {
    e.preventDefault();
    setErro('');
    if (!clienteId) {
      setErro('Selecione um cliente para salvar o pedido.');
      return;
    }
    if (itens.length === 0) {
      setErro('Adicione ao menos um item ao pedido.');
      return;
    }
    setSalvando(true);
    try {
      const payload = {
        cliente_id: parseInt(clienteId, 10),
        data_validade_orcamento: validadeOrcamento || null,
        prazo_entrega: prazoEntrega || null,
        endereco_entrega: enderecoEntrega.trim() || null,
        frete: Number(frete || 0),
        desconto_valor: Number(descontoValor || 0),
        desconto_tipo: descontoTipo,
        observacoes: observacoes.trim() || null,
        itens: itens.map((it) => ({
          tipo_item: it.tipo_item,
          descricao: it.descricao || null,
          quantidade: parseInt(it.quantidade || 1, 10),
          preco_unitario: Number(it.preco_unitario),
          obra_largura: it.obra_largura ?? null,
          obra_altura: it.obra_altura ?? null,
          paspatour: Boolean(it.paspatour),
          tamanho_paspatour: Number(it.tamanho_paspatour || 0),
          paspatour_id: it.paspatour_id || null,
          vidro_tipo: it.vidro_tipo || null,
          vidro_id: it.vidro_id || null,
          fundo_tipo: it.fundo_tipo || null,
          fundo_id: it.fundo_id || null,
          mao_de_obra: Number(it.mao_de_obra || 0),
          molduras: it.molduras || [],
        })),
      };

      const resp = pedidoEdicao
        ? await api.put(`/pedidos/${pedidoEdicao.id}`, payload)
        : await api.post('/pedidos/', payload);
      onSalvo(resp.data);
      onClose();
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao salvar pedido.');
    } finally {
      setSalvando(false);
    }
  };

  return (
    <>
      <Dialog
        open={open}
        onClose={onClose}
        title={pedidoEdicao ? `Editar Orçamento ${pedidoEdicao.numero_pedido}` : 'Novo Orçamento / Pedido'}
        size="lg"
      >
        {erro && <Callout variant="danger">{erro}</Callout>}

        <form onSubmit={salvarPedido} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-4)' }}>
          <div style={{ display: 'flex', gap: 'var(--at-space-2)', alignItems: 'flex-end', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 240 }}>
              <Field id="ped-cliente" label="Cliente" required>
                <select
                  id="ped-cliente"
                  className="at-select"
                  value={clienteId}
                  onChange={(e) => setClienteId(e.target.value)}
                >
                  <option value="">Selecione um cliente...</option>
                  {clientes.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nome} {c.telefone ? `(${c.telefone})` : ''}
                    </option>
                  ))}
                </select>
              </Field>
            </div>
            <Button type="button" variant="secondary" onClick={() => setModalClienteAberto(true)}>
              <UserPlus size={16} aria-hidden="true" /> Novo Cliente
            </Button>
          </div>

          <div className="at-grid-3">
            <Field id="ped-validade" label="Validade do Orçamento">
              <input
                id="ped-validade"
                type="date"
                className="at-input"
                value={validadeOrcamento}
                onChange={(e) => setValidadeOrcamento(e.target.value)}
              />
            </Field>
            <Field id="ped-prazo" label="Prazo de Entrega">
              <input
                id="ped-prazo"
                type="date"
                className="at-input"
                value={prazoEntrega}
                onChange={(e) => setPrazoEntrega(e.target.value)}
              />
            </Field>
            <Field id="ped-endereco" label="Endereço de Entrega">
              <input
                id="ped-endereco"
                className="at-input"
                placeholder="Retirada ou endereço"
                value={enderecoEntrega}
                onChange={(e) => setEnderecoEntrega(e.target.value)}
              />
            </Field>
          </div>

          <div className="at-card">
            <div className="at-card__header">
              <h3>Itens do Pedido ({itens.length})</h3>
              <Button type="button" variant="secondary" size="sm" onClick={() => setModalItemAberto(true)}>
                <Plus size={15} aria-hidden="true" /> Adicionar Item
              </Button>
            </div>

            {temItemAbaixo && (
              <Callout variant="warning">
                Um ou mais itens estão com preço praticado abaixo do valor sugerido pela calculadora. O salvamento continua permitido, mas o pedido ficará marcado internamente.
              </Callout>
            )}

            {itens.length === 0 ? (
              <p className="at-muted">Nenhum item adicionado ainda.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-2)' }}>
                {itens.map((it, idx) => {
                  const abaixo = Number(it.preco_unitario) < Number(it.valor_sugerido || 0);
                  return (
                    <div key={idx} className={`at-baixa-row ${abaixo ? 'at-baixa-row--ruptura' : ''}`}>
                      <div style={{ flex: 1, minWidth: 220 }}>
                        <strong>{it.descricao}</strong>
                        <div className="at-muted at-num" style={{ fontSize: 'var(--at-text-xs)' }}>
                          Qtd: {it.quantidade} · Sugerido: {formatarMoeda(it.valor_sugerido)}
                        </div>
                      </div>

                      <div className="at-actions">
                        <Field id={`preco-it-${idx}`} label="Preço Unit. Praticado (R$)">
                          <input
                            id={`preco-it-${idx}`}
                            type="number"
                            step="0.01"
                            min="0"
                            className="at-input at-num"
                            style={{ width: 120 }}
                            value={it.preco_unitario}
                            onChange={(e) => {
                              const novos = itens.map((itemAtual, i) =>
                                i === idx ? { ...itemAtual, preco_unitario: e.target.value } : itemAtual,
                              );
                              setItens(novos);
                            }}
                          />
                        </Field>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          aria-label={`Remover item ${idx + 1}`}
                          onClick={() => setItens(itens.filter((_, i) => i !== idx))}
                        >
                          <Trash2 size={15} aria-hidden="true" />
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="at-grid-3">
            <Field id="ped-frete" label="Frete (R$)">
              <input
                id="ped-frete"
                type="number"
                step="0.01"
                min="0"
                className="at-input at-num"
                value={frete}
                onChange={(e) => setFrete(e.target.value)}
              />
            </Field>
            <Field id="ped-desc-tipo" label="Tipo de Desconto">
              <select
                id="ped-desc-tipo"
                className="at-select"
                value={descontoTipo}
                onChange={(e) => setDescontoTipo(e.target.value)}
              >
                <option value="valor">Valor Fixo (R$)</option>
                <option value="percentual">Percentual (%)</option>
              </select>
            </Field>
            <Field id="ped-desc-val" label={descontoTipo === 'percentual' ? 'Desconto (%)' : 'Desconto (R$)'}>
              <input
                id="ped-desc-val"
                type="number"
                step="0.01"
                min="0"
                className="at-input at-num"
                value={descontoValor}
                onChange={(e) => setDescontoValor(e.target.value)}
              />
            </Field>
          </div>

          <Field id="ped-obs" label="Observações">
            <textarea
              id="ped-obs"
              className="at-textarea"
              rows={2}
              value={observacoes}
              onChange={(e) => setObservacoes(e.target.value)}
            />
          </Field>

          <div className="at-calc-list">
            <div className="at-calc-list__row">
              <span className="at-muted">Subtotal dos Itens:</span>
              <span className="at-num">{formatarMoeda(totais.subtotalItens)}</span>
            </div>
            <div className="at-calc-list__row at-calc-list__row--total">
              <span>Total Estimado do Pedido:</span>
              <span className="at-num" style={{ color: 'var(--at-color-text-brand)' }}>
                {formatarMoeda(totais.valorTotal)}
              </span>
            </div>
          </div>

          <div className="at-actions" style={{ justifyContent: 'flex-end' }}>
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary" loading={salvando}>
              {pedidoEdicao ? 'Salvar Alterações' : 'Criar Orçamento (Rascunho)'}
            </Button>
          </div>
        </form>
      </Dialog>

      <ModalAdicionarItemPedido
        open={modalItemAberto}
        onClose={() => setModalItemAberto(false)}
        catalogos={catalogos}
        onAdicionarItem={(item) => setItens((atual) => [...atual, item])}
      />

      <Dialog
        open={modalClienteAberto}
        onClose={() => setModalClienteAberto(false)}
        title="Cadastro Rápido de Cliente"
        size="sm"
      >
        <form onSubmit={criarClienteRapido} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-3)' }}>
          <Field id="qc-nome" label="Nome" required>
            <input
              id="qc-nome"
              className="at-input"
              required
              value={novoCliente.nome}
              onChange={(e) => setNovoCliente({ ...novoCliente, nome: e.target.value })}
            />
          </Field>
          <Field id="qc-tel" label="Telefone / WhatsApp">
            <input
              id="qc-tel"
              className="at-input"
              value={novoCliente.telefone}
              onChange={(e) => setNovoCliente({ ...novoCliente, telefone: e.target.value })}
            />
          </Field>
          <div className="at-actions" style={{ justifyContent: 'flex-end' }}>
            <Button type="button" variant="secondary" onClick={() => setModalClienteAberto(false)}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary">
              Cadastrar
            </Button>
          </div>
        </form>
      </Dialog>
    </>
  );
};

export default PedidoForm;
