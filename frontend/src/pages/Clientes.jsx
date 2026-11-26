import React, { useCallback, useEffect, useState } from 'react';
import { Edit2, History, Mail, MapPin, Phone, Plus, Search, Trash2, Users } from 'lucide-react';
import api from '../api/config';
import { useToast } from '../context/ContextoToast';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Field from '../components/ui/Field';
import Dialog from '../components/ui/Dialog';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import Callout from '../components/ui/Callout';
import EmptyState from '../components/ui/EmptyState';
import ModalHistoricoCliente from '../components/clientes/ModalHistoricoCliente';

const ESTADO_INICIAL_CLIENTE = {
  nome: '',
  sobrenome: '',
  telefone: '',
  email: '',
  endereco: '',
  cep: '',
};

/**
 * Página de gestão de clientes com busca no servidor (?q=), CRUD acessível e histórico filtrado.
 *
 * @returns {JSX.Element} Página Clientes.
 */
const Clientes = () => {
  const { notificar } = useToast();
  const [clientes, setClientes] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [termoBusca, setTermoBusca] = useState('');
  const [modalAberto, setModalAberto] = useState(false);
  const [form, setForm] = useState(ESTADO_INICIAL_CLIENTE);
  const [editandoId, setEditandoId] = useState(null);
  const [erroForm, setErroForm] = useState('');
  const [salvando, setSalvando] = useState(false);
  const [clienteExcluir, setClienteExcluir] = useState(null);
  const [excluindo, setExcluindo] = useState(false);
  const [clienteHistorico, setClienteHistorico] = useState(null);

  const carregarClientes = useCallback(async (busca = '') => {
    setCarregando(true);
    try {
      const params = busca.trim() ? { q: busca.trim() } : {};
      const resp = await api.get('/clientes/', { params });
      setClientes(resp.data || []);
    } catch (err) {
      notificar(err.response?.data?.detail || 'Erro ao carregar clientes.', 'danger');
    } finally {
      setCarregando(false);
    }
  }, [notificar]);

  useEffect(() => {
    const timer = setTimeout(() => {
      carregarClientes(termoBusca);
    }, 200);
    return () => clearTimeout(timer);
  }, [termoBusca, carregarClientes]);

  const abrirCriar = () => {
    setEditandoId(null);
    setForm(ESTADO_INICIAL_CLIENTE);
    setErroForm('');
    setModalAberto(true);
  };

  const abrirEditar = (cliente) => {
    setEditandoId(cliente.id);
    setForm({
      nome: cliente.nome || '',
      sobrenome: cliente.sobrenome || '',
      telefone: cliente.telefone || '',
      email: cliente.email || '',
      endereco: cliente.endereco || '',
      cep: cliente.cep || '',
    });
    setErroForm('');
    setModalAberto(true);
  };

  const handleSalvar = async (evento) => {
    evento.preventDefault();
    setErroForm('');
    if (!form.nome.trim() || !form.sobrenome.trim() || !form.telefone.trim()) {
      setErroForm('Nome, sobrenome e telefone são obrigatórios.');
      return;
    }

    setSalvando(true);
    try {
      if (editandoId) {
        await api.put(`/clientes/${editandoId}`, form);
        notificar('Cliente atualizado com sucesso.');
      } else {
        await api.post('/clientes/', form);
        notificar('Cliente cadastrado com sucesso.');
      }
      setModalAberto(false);
      carregarClientes(termoBusca);
    } catch (err) {
      setErroForm(err.response?.data?.detail || 'Erro ao salvar cliente.');
    } finally {
      setSalvando(false);
    }
  };

  const confirmarExclusao = async () => {
    if (!clienteExcluir) return;
    setExcluindo(true);
    try {
      await api.delete(`/clientes/${clienteExcluir.id}`);
      notificar('Cliente excluído com sucesso.');
      setClienteExcluir(null);
      carregarClientes(termoBusca);
    } catch (err) {
      notificar(err.response?.data?.detail || 'Não foi possível excluir o cliente.', 'danger');
      setClienteExcluir(null);
    } finally {
      setExcluindo(false);
    }
  };

  return (
    <div>
      <header className="at-page-header">
        <div>
          <h1>Gestão de Clientes</h1>
          <p className="at-page-header__subtitle">Cadastro central e histórico completo de orçamentos e pedidos.</p>
        </div>
        <div className="at-page-header__actions">
          <Button variant="primary" onClick={abrirCriar}>
            <Plus size={18} aria-hidden="true" />
            <span>Adicionar Cliente</span>
          </Button>
        </div>
      </header>

      <Card style={{ marginBottom: 'var(--at-space-4)' }}>
        <div className="at-search-box">
          <Search size={18} className="at-search-box__icon" aria-hidden="true" />
          <label htmlFor="busca-clientes" className="at-sr-only">
            Buscar clientes
          </label>
          <input
            id="busca-clientes"
            type="search"
            className="at-input at-search-box__input"
            placeholder="Nome, sobrenome, telefone ou e-mail"
            value={termoBusca}
            onChange={(e) => setTermoBusca(e.target.value)}
          />
        </div>
      </Card>

      {carregando ? (
        <div className="at-state" role="status">
          Carregando clientes...
        </div>
      ) : clientes.length === 0 ? (
        <Card>
          <EmptyState
            icon={<Users size={36} aria-hidden="true" />}
            title={termoBusca ? 'Nenhum cliente encontrado para esta busca' : 'Nenhum cliente cadastrado'}
            description={termoBusca ? 'Tente outro nome, telefone ou e-mail.' : 'Cadastre o primeiro cliente da Atividros.'}
            action={
              termoBusca ? (
                <Button variant="secondary" onClick={() => setTermoBusca('')}>
                  Limpar busca
                </Button>
              ) : (
                <Button variant="primary" onClick={abrirCriar}>
                  Novo Cliente
                </Button>
              )
            }
          />
        </Card>
      ) : (
        <div className="at-grid-auto">
          {clientes.map((c) => (
            <Card key={c.id}>
              <div className="at-card__header">
                <div>
                  <h3>
                    {c.nome} {c.sobrenome}
                  </h3>
                  <span className="at-muted at-num">#{c.id}</span>
                </div>
                <div style={{ display: 'flex', gap: 'var(--at-space-1)' }}>
                  <Button
                    variant="icon"
                    onClick={() => setClienteHistorico(c)}
                    aria-label={`Ver histórico de ${c.nome} ${c.sobrenome}`}
                  >
                    <History size={16} aria-hidden="true" />
                  </Button>
                  <Button
                    variant="icon"
                    onClick={() => abrirEditar(c)}
                    aria-label={`Editar ${c.nome} ${c.sobrenome}`}
                  >
                    <Edit2 size={16} aria-hidden="true" />
                  </Button>
                  <Button
                    variant="icon"
                    onClick={() => setClienteExcluir(c)}
                    aria-label={`Excluir ${c.nome} ${c.sobrenome}`}
                  >
                    <Trash2 size={16} aria-hidden="true" />
                  </Button>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-2)' }}>
                <p style={{ display: 'flex', alignItems: 'center', gap: 'var(--at-space-2)' }} className="at-num">
                  <Phone size={15} aria-hidden="true" /> {c.telefone}
                </p>
                {c.email && (
                  <p style={{ display: 'flex', alignItems: 'center', gap: 'var(--at-space-2)' }}>
                    <Mail size={15} aria-hidden="true" /> {c.email}
                  </p>
                )}
                {c.endereco && (
                  <p style={{ display: 'flex', alignItems: 'center', gap: 'var(--at-space-2)' }} className="at-muted">
                    <MapPin size={15} aria-hidden="true" /> {c.endereco} {c.cep ? `(${c.cep})` : ''}
                  </p>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      <Dialog
        open={modalAberto}
        onClose={() => setModalAberto(false)}
        title={editandoId ? 'Editar Cliente' : 'Novo Cliente'}
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalAberto(false)} disabled={salvando}>
              Cancelar
            </Button>
            <Button type="submit" form="form-cliente" variant="primary" loading={salvando}>
              Salvar Cliente
            </Button>
          </>
        }
      >
        <form id="form-cliente" onSubmit={handleSalvar}>
          {erroForm && <Callout variant="danger">{erroForm}</Callout>}
          <div className="at-grid-2">
            <Field id="cli-nome" label="Nome" required>
              <input
                id="cli-nome"
                className="at-input"
                value={form.nome}
                onChange={(e) => setForm({ ...form, nome: e.target.value })}
                required
              />
            </Field>
            <Field id="cli-sobrenome" label="Sobrenome" required>
              <input
                id="cli-sobrenome"
                className="at-input"
                value={form.sobrenome}
                onChange={(e) => setForm({ ...form, sobrenome: e.target.value })}
                required
              />
            </Field>
          </div>
          <div className="at-grid-2">
            <Field id="cli-telefone" label="Telefone" required>
              <input
                id="cli-telefone"
                className="at-input"
                value={form.telefone}
                onChange={(e) => setForm({ ...form, telefone: e.target.value })}
                required
              />
            </Field>
            <Field id="cli-email" label="E-mail">
              <input
                id="cli-email"
                type="email"
                className="at-input"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </Field>
          </div>
          <Field id="cli-endereco" label="Endereço">
            <input
              id="cli-endereco"
              className="at-input"
              value={form.endereco}
              onChange={(e) => setForm({ ...form, endereco: e.target.value })}
            />
          </Field>
          <Field id="cli-cep" label="CEP">
            <input
              id="cli-cep"
              className="at-input"
              value={form.cep}
              onChange={(e) => setForm({ ...form, cep: e.target.value })}
            />
          </Field>
        </form>
      </Dialog>

      <ConfirmDialog
        open={Boolean(clienteExcluir)}
        onClose={() => setClienteExcluir(null)}
        onConfirm={confirmarExclusao}
        title="Confirmar exclusão de cliente"
        confirmLabel="Excluir cliente"
        loading={excluindo}
      >
        <p>
          Deseja excluir o cliente{' '}
          <strong>
            {clienteExcluir?.nome} {clienteExcluir?.sobrenome}
          </strong>
          ? Clientes com pedidos vinculados são protegidos contra exclusão.
        </p>
      </ConfirmDialog>

      <ModalHistoricoCliente cliente={clienteHistorico} onClose={() => setClienteHistorico(null)} />
    </div>
  );
};

export default Clientes;
