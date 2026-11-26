import React, { useCallback, useEffect, useState } from 'react';
import { Columns3, List, Plus } from 'lucide-react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import api from '../api/config';
import { useToast } from '../context/ContextoToast';
import Button from '../components/ui/Button';
import Callout from '../components/ui/Callout';
import KanbanBoard from '../components/pedidos/KanbanBoard';
import PedidoLista from '../components/pedidos/PedidoLista';
import PedidoForm from '../components/pedidos/PedidoForm';
import PedidoDetalhe from '../components/pedidos/PedidoDetalhe';
import ModalBaixaEstoque from '../components/pedidos/ModalBaixaEstoque';
import ModalPagamento from '../components/pedidos/ModalPagamento';

/**
 * Orquestrador da página de Pedidos e Orçamentos (Kanban de 6 colunas, Lista e modais).
 *
 * @returns {JSX.Element} Página de Pedidos.
 */
const Pedidos = () => {
  const { notificar } = useToast();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [visao, setVisao] = useState('kanban');
  const [filtroGeral, setFiltroGeral] = useState('');
  const [pedidos, setPedidos] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [catalogos, setCatalogos] = useState({ molduras: [], vidros: [], fundos: [], tabelaVidro: [], tabelaFundo: [], tabelaPaspatour: [] });
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState('');

  const [formAberto, setFormAberto] = useState(false);
  const [pedidoEdicao, setPedidoEdicao] = useState(null);
  const [itemCalculadoraPendente, setItemCalculadoraPendente] = useState(null);
  const [pedidoDetalhe, setPedidoDetalhe] = useState(null);
  const [pedidoBaixa, setPedidoBaixa] = useState(null);
  const [pedidoPagamento, setPedidoPagamento] = useState(null);

  const carregarDados = useCallback(async () => {
    setCarregando(true);
    setErro('');
    try {
      const q = searchParams.get('q') || '';
      const [p, c, m, v, f, tv, tf, tp] = await Promise.all([
        api.get('/pedidos/', { params: q ? { q } : {} }),
        api.get('/clientes/'),
        api.get('/estoque/molduras'),
        api.get('/estoque/vidros'),
        api.get('/estoque/fundos'),
        api.get('/calculadora/tabela-vidro'),
        api.get('/calculadora/tabela-fundo'),
        api.get('/calculadora/tabela-paspatour'),
      ]);
      setPedidos(p.data || []);
      setClientes(c.data || []);
      setCatalogos({
        molduras: m.data || [],
        vidros: v.data || [],
        fundos: f.data || [],
        tabelaVidro: tv.data || [],
        tabelaFundo: tf.data || [],
        tabelaPaspatour: tp.data || [],
      });
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao carregar pedidos e catálogos.');
    } finally {
      setCarregando(false);
    }
  }, [searchParams]);

  useEffect(() => { carregarDados(); }, [carregarDados]);

  useEffect(() => {
    if (location.state?.itemCalculadora) {
      setItemCalculadoraPendente(location.state.itemCalculadora);
      setPedidoEdicao(null);
      setFormAberto(true);
      navigate('/pedidos', { replace: true, state: {} });
    } else if (location.state?.abrirPedidoId && !carregando) {
      const idAlvo = location.state.abrirPedidoId;
      const encontrado = pedidos.find((p) => p.id === idAlvo);
      if (encontrado) setPedidoDetalhe(encontrado);
      else api.get(`/pedidos/${idAlvo}`).then((r) => setPedidoDetalhe(r.data)).catch(() => {});
      navigate('/pedidos', { replace: true, state: {} });
    }
  }, [location.state, navigate, pedidos, carregando]);

  const sincronizarPedido = (atualizado) => {
    setPedidos((lista) => (lista.some((p) => p.id === atualizado.id) ? lista.map((p) => (p.id === atualizado.id ? atualizado : p)) : [atualizado, ...lista]));
    if (pedidoDetalhe?.id === atualizado.id) setPedidoDetalhe(atualizado);
    if (pedidoPagamento?.id === atualizado.id) setPedidoPagamento(atualizado);
  };

  const mudarStatus = async (pedido, eixo, novoStatus) => {
    try {
      const resp = await api.patch(`/pedidos/${pedido.id}/status`, { eixo, novo_status: novoStatus });
      sincronizarPedido(resp.data);
      notificar(`Pedido ${pedido.numero_pedido} atualizado com sucesso.`);
    } catch (err) {
      notificar(err.response?.data?.detail || 'Não foi possível atualizar o status.', 'danger');
    }
  };

  const baixarPdf = async (pedido) => {
    try {
      const resp = await api.get(`/pedidos/${pedido.id}/pdf`, { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }));
      const a = Object.assign(document.createElement('a'), { href: url, download: `${pedido.numero_pedido}.pdf` });
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      notificar('Erro ao gerar o PDF do pedido.', 'danger');
    }
  };

  const excluirPedido = async (pedido) => {
    try {
      await api.delete(`/pedidos/${pedido.id}`);
      setPedidos((lista) => lista.filter((p) => p.id !== pedido.id));
      setPedidoDetalhe(null);
      notificar(`Pedido ${pedido.numero_pedido} excluído.`);
    } catch (err) {
      notificar(err.response?.data?.detail || 'Erro ao excluir pedido.', 'danger');
    }
  };

  return (
    <div>
      <header className="at-page-header">
        <div>
          <h1>Pedidos e Produção</h1>
          <p className="at-page-header__subtitle">Orçamentos, Kanban da oficina em 6 etapas e pagamentos.</p>
        </div>
        <div className="at-actions">
          <div className="at-segmented" role="group" aria-label="Modo de visualização">
            <button type="button" className="at-segmented__btn" aria-pressed={visao === 'kanban'} onClick={() => setVisao('kanban')}>
              <Columns3 size={15} aria-hidden="true" /> Kanban
            </button>
            <button type="button" className="at-segmented__btn" aria-pressed={visao === 'lista'} onClick={() => setVisao('lista')}>
              <List size={15} aria-hidden="true" /> Lista
            </button>
          </div>
          <Button variant="primary" onClick={() => { setPedidoEdicao(null); setItemCalculadoraPendente(null); setFormAberto(true); }}>
            <Plus size={16} aria-hidden="true" /> Novo Orçamento
          </Button>
        </div>
      </header>

      {erro && <Callout variant="danger">{erro}</Callout>}
      {carregando ? (
        <p className="at-muted">Carregando pedidos...</p>
      ) : visao === 'kanban' ? (
        <KanbanBoard pedidos={pedidos} onAbrirDetalhe={setPedidoDetalhe} onAbrirBaixa={setPedidoBaixa} onAvancarProducao={(p, st) => mudarStatus(p, 'producao', st)} onMarcarEntregue={(p) => mudarStatus(p, 'geral', 'entregue')} />
      ) : (
        <PedidoLista pedidos={pedidos} filtroGeral={filtroGeral} onChangeFiltroGeral={setFiltroGeral} onAbrirDetalhe={setPedidoDetalhe} onEditarRascunho={(p) => { setPedidoEdicao(p); setItemCalculadoraPendente(null); setFormAberto(true); }} onBaixarPdf={baixarPdf} />
      )}

      <PedidoForm open={formAberto} onClose={() => { setFormAberto(false); setItemCalculadoraPendente(null); }} pedidoEdicao={pedidoEdicao} itemInicialCalculadora={itemCalculadoraPendente} clientes={clientes} onClienteCriado={(c) => setClientes((atual) => [c, ...atual])} catalogos={catalogos} onSalvo={(p) => { sincronizarPedido(p); notificar(`Pedido ${p.numero_pedido} salvo!`); }} />
      <PedidoDetalhe open={Boolean(pedidoDetalhe)} onClose={() => setPedidoDetalhe(null)} pedido={pedidoDetalhe} onEditarRascunho={(p) => { setPedidoDetalhe(null); setPedidoEdicao(p); setFormAberto(true); }} onAbrirBaixa={setPedidoBaixa} onAbrirPagamento={setPedidoPagamento} onMudarStatus={mudarStatus} onBaixarPdf={baixarPdf} onExcluirPedido={excluirPedido} />
      <ModalBaixaEstoque open={Boolean(pedidoBaixa)} onClose={() => setPedidoBaixa(null)} pedido={pedidoBaixa} onConfirmado={(resp) => { sincronizarPedido(resp.pedido); notificar(resp.alertas_ruptura?.length ? `Produção iniciada com ${resp.alertas_ruptura.length} alerta(s) de ruptura.` : `Produção de ${resp.pedido.numero_pedido} iniciada!`, resp.alertas_ruptura?.length ? 'warning' : 'success'); }} />
      <ModalPagamento open={Boolean(pedidoPagamento)} onClose={() => setPedidoPagamento(null)} pedido={pedidoPagamento} onAtualizado={(p) => { sincronizarPedido(p); notificar(`Financeiro de ${p.numero_pedido} atualizado.`); }} />
    </div>
  );
};

export default Pedidos;
