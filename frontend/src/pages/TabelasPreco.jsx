import React, { useCallback, useEffect, useState } from 'react';
import { Edit2, Plus, Trash2 } from 'lucide-react';
import api from '../api/config';
import { useToast } from '../context/ContextoToast';
import Tabs from '../components/ui/Tabs';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import DataTable from '../components/ui/DataTable';
import Dialog from '../components/ui/Dialog';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import Field from '../components/ui/Field';
import Callout from '../components/ui/Callout';
import { formatarAreaM2, formatarMoeda } from '../utils/formatadores';

const ABAS = [
  { id: 'vidro', label: 'Vidros e Espelhos' },
  { id: 'fundo', label: 'Fundos' },
  { id: 'paspatour', label: 'Paspatour' },
];

/**
 * Página dedicada ao gerenciamento das 3 tabelas de preço por m² (Vidro, Fundo e Paspatour).
 *
 * @returns {JSX.Element} Página TabelasPreco.
 */
const TabelasPreco = () => {
  const { notificar } = useToast();
  const [aba, setAba] = useState('vidro');
  const [itens, setItens] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [modalAberto, setModalAberto] = useState(false);
  const [editando, setEditando] = useState(null);
  const [excluirAlvo, setExcluirAlvo] = useState(null);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  const [form, setForm] = useState({
    tipo: '',
    descricao: '',
    preco_por_m2: '',
    area_minima_m2: '0.2500',
  });

  const endpointBase =
    aba === 'vidro'
      ? '/calculadora/tabela-vidro'
      : aba === 'fundo'
        ? '/calculadora/tabela-fundo'
        : '/calculadora/tabela-paspatour';

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const resp = await api.get(endpointBase);
      setItens(resp.data || []);
    } catch (err) {
      notificar(err.response?.data?.detail || 'Erro ao carregar tabela de preços.', 'danger');
    } finally {
      setCarregando(false);
    }
  }, [endpointBase, notificar]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const abrirCriar = () => {
    setEditando(null);
    setErro('');
    setForm({ tipo: '', descricao: '', preco_por_m2: '', area_minima_m2: '0.2500' });
    setModalAberto(true);
  };

  const abrirEditar = (item) => {
    setEditando(item);
    setErro('');
    setForm({
      tipo: item.tipo || '',
      descricao: item.descricao || '',
      preco_por_m2: String(item.preco_por_m2 ?? ''),
      area_minima_m2: String(item.area_minima_m2 ?? '0.2500'),
    });
    setModalAberto(true);
  };

  const handleSalvar = async (evento) => {
    evento.preventDefault();
    setErro('');
    setSalvando(true);

    try {
      if (aba === 'vidro') {
        const payload = {
          ...(editando ? {} : { tipo: form.tipo.trim() }),
          preco_por_m2: parseFloat(form.preco_por_m2),
          area_minima_m2: parseFloat(form.area_minima_m2 || '0.25'),
          descricao: form.descricao,
        };
        if (editando) {
          await api.put(`${endpointBase}/${editando.id}`, payload);
        } else {
          await api.post(endpointBase, payload);
        }
      } else if (aba === 'fundo') {
        const payload = {
          tipo: form.tipo.trim(),
          preco_por_m2: parseFloat(form.preco_por_m2),
          descricao: form.descricao,
        };
        if (editando) {
          await api.put(`${endpointBase}/${editando.id}`, payload);
        } else {
          await api.post(endpointBase, payload);
        }
      } else {
        const payload = {
          descricao: form.descricao.trim(),
          preco_por_m2: parseFloat(form.preco_por_m2),
        };
        if (editando) {
          await api.put(`${endpointBase}/${editando.id}`, payload);
        } else {
          await api.post(endpointBase, payload);
        }
      }

      notificar('Tabela de preço atualizada com sucesso.');
      setModalAberto(false);
      carregar();
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao salvar faixa de preço.');
    } finally {
      setSalvando(false);
    }
  };

  const handleExcluir = async () => {
    if (!excluirAlvo) return;
    setSalvando(true);
    try {
      await api.delete(`${endpointBase}/${excluirAlvo.id}`);
      notificar('Faixa de preço removida.');
      setExcluirAlvo(null);
      carregar();
    } catch (err) {
      notificar(err.response?.data?.detail || 'Erro ao excluir faixa de preço.', 'danger');
      setExcluirAlvo(null);
    } finally {
      setSalvando(false);
    }
  };

  const colunas = [
    ...(aba !== 'paspatour' ? [{ key: 'tipo', header: 'Tipo' }] : []),
    { key: 'descricao', header: 'Descrição', render: (r) => r.descricao || '—' },
    {
      key: 'preco_por_m2',
      header: 'Preço (R$/m²)',
      numeric: true,
      render: (r) => `${formatarMoeda(r.preco_por_m2)}/m²`,
    },
    ...(aba === 'vidro'
      ? [
          {
            key: 'area_minima_m2',
            header: 'Área Mínima',
            numeric: true,
            render: (r) => formatarAreaM2(r.area_minima_m2),
          },
        ]
      : []),
    {
      key: 'acoes',
      header: 'Ações',
      render: (r) => (
        <div style={{ display: 'flex', gap: 'var(--at-space-1)' }}>
          <Button variant="icon" onClick={() => abrirEditar(r)} aria-label="Editar faixa de preço">
            <Edit2 size={16} aria-hidden="true" />
          </Button>
          <Button variant="icon" onClick={() => setExcluirAlvo(r)} aria-label="Excluir faixa de preço">
            <Trash2 size={16} aria-hidden="true" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <header className="at-page-header">
        <div>
          <h1>Tabelas de Preço</h1>
          <p className="at-page-header__subtitle">
            Valores de referência por m² usados pela Calculadora Unificada de quadros e vidros avulsos.
          </p>
        </div>
        <div className="at-page-header__actions">
          <Button variant="primary" onClick={abrirCriar}>
            <Plus size={18} aria-hidden="true" />
            <span>Nova Faixa</span>
          </Button>
        </div>
      </header>

      <Tabs tabs={ABAS} activeId={aba} onChange={setAba} ariaLabel="Categorias de tabelas de preço" />

      {carregando ? (
        <div className="at-state" role="status">
          Carregando tabela...
        </div>
      ) : (
        <Card>
          <DataTable
            columns={colunas}
            data={itens}
            emptyTitle="Nenhuma faixa cadastrada"
            emptyDescription="Adicione os valores por m² para habilitar cálculos nesta categoria."
            emptyAction={
              <Button variant="primary" onClick={abrirCriar}>
                Cadastrar Preço
              </Button>
            }
          />
        </Card>
      )}

      <Dialog
        open={modalAberto}
        onClose={() => setModalAberto(false)}
        title={editando ? 'Editar Faixa de Preço' : 'Nova Faixa de Preço'}
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalAberto(false)} disabled={salvando}>
              Cancelar
            </Button>
            <Button type="submit" form="form-tabela-preco" variant="primary" loading={salvando}>
              Salvar
            </Button>
          </>
        }
      >
        <form id="form-tabela-preco" onSubmit={handleSalvar}>
          {erro && <Callout variant="danger">{erro}</Callout>}

          {aba === 'vidro' && (
            <Field id="tp-tipo-vidro" label="Tipo de Vidro" required>
              <select
                id="tp-tipo-vidro"
                className="at-input"
                value={form.tipo}
                onChange={(e) => setForm({ ...form, tipo: e.target.value })}
                disabled={Boolean(editando)}
                required
              >
                <option value="">Selecione...</option>
                <option value="incolor">incolor</option>
                <option value="antireflexo">antireflexo</option>
                <option value="espelho">espelho</option>
                <option value="outro">outro</option>
              </select>
            </Field>
          )}

          {aba === 'fundo' && (
            <Field id="tp-tipo-fundo" label="Tipo de Fundo" required hint="Ex.: MDF, Eucatex, Foam Board">
              <input
                id="tp-tipo-fundo"
                className="at-input"
                value={form.tipo}
                onChange={(e) => setForm({ ...form, tipo: e.target.value })}
                required
              />
            </Field>
          )}

          <Field id="tp-descricao" label="Descrição" required={aba === 'paspatour'}>
            <input
              id="tp-descricao"
              className="at-input"
              value={form.descricao}
              onChange={(e) => setForm({ ...form, descricao: e.target.value })}
              required={aba === 'paspatour'}
            />
          </Field>

          <div className={aba === 'vidro' ? 'at-grid-2' : undefined}>
            <Field id="tp-preco-m2" label="Preço por m² (R$)" required>
              <input
                id="tp-preco-m2"
                type="number"
                step="0.01"
                min="0"
                className="at-input at-num"
                value={form.preco_por_m2}
                onChange={(e) => setForm({ ...form, preco_por_m2: e.target.value })}
                required
              />
            </Field>

            {aba === 'vidro' && (
              <Field id="tp-area-min" label="Área Mínima (m²)" required hint="Ex.: 0,2500 m²">
                <input
                  id="tp-area-min"
                  type="number"
                  step="0.0001"
                  min="0"
                  className="at-input at-num"
                  value={form.area_minima_m2}
                  onChange={(e) => setForm({ ...form, area_minima_m2: e.target.value })}
                  required
                />
              </Field>
            )}
          </div>
        </form>
      </Dialog>

      <ConfirmDialog
        open={Boolean(excluirAlvo)}
        onClose={() => setExcluirAlvo(null)}
        onConfirm={handleExcluir}
        title="Confirmar exclusão"
        confirmLabel="Excluir faixa"
        loading={salvando}
      >
        <p>Deseja remover esta faixa de preço? Essa ação não altera pedidos já gravados.</p>
      </ConfirmDialog>
    </div>
  );
};

export default TabelasPreco;
