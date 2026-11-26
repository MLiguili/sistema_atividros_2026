import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Edit2, Layers, Plus, Search, SlidersHorizontal, Trash2 } from 'lucide-react';
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
import ModalEntradaChapas from '../components/estoque/ModalEntradaChapas';
import ModalAjusteM2 from '../components/estoque/ModalAjusteM2';
import CalculadoraCustoBarra from '../components/estoque/CalculadoraCustoBarra';
import { formatarAreaM2, formatarMoeda } from '../utils/formatadores';

const ABAS = [
  { id: 'molduras', label: 'Molduras' },
  { id: 'vidros', label: 'Vidros' },
  { id: 'fundos', label: 'Fundos' },
  { id: 'suplementos', label: 'Suplementos' },
];

const FORM_PADRAO = {
  molduras: {
    codigo: '',
    cor: '',
    marca: '',
    tamanho_barra: '2.70',
    largura_barra: '3.00',
    preco_custo: '',
    preco_venda: '',
    quantidade: '0',
    estoque_minimo: '5',
  },
  vidros: {
    tipo: 'incolor',
    espessura: '3.00',
    cor: '',
    area_disponivel_m2: '0.0000',
    estoque_minimo_m2: '2.0000',
  },
  fundos: {
    tipo: 'MDF',
    espessura: '3.00',
    cor: '',
    area_disponivel_m2: '0.0000',
    estoque_minimo_m2: '2.0000',
  },
  suplementos: {
    nome: '',
    quantidade: '0',
    unidade: 'un',
  },
};

/**
 * Página de Gestão de Estoque cobrindo Molduras (barras + R$/m), Vidros/Fundos (m² + chapas) e Suplementos.
 *
 * @returns {JSX.Element} Página Estoque.
 */
const Estoque = () => {
  const { notificar } = useToast();
  const [abaAtiva, setAbaAtiva] = useState('molduras');
  const [itens, setItens] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [termoBusca, setTermoBusca] = useState('');
  const [soCriticos, setSoCriticos] = useState(false);

  const [modalFormAberto, setModalFormAberto] = useState(false);
  const [editando, setEditando] = useState(null);
  const [form, setForm] = useState(FORM_PADRAO.molduras);
  const [erroForm, setErroForm] = useState('');
  const [salvando, setSalvando] = useState(false);

  const [itemExcluir, setItemExcluir] = useState(null);
  const [itemChapas, setItemChapas] = useState(null);
  const [itemAjusteM2, setItemAjusteM2] = useState(null);

  const carregarDados = useCallback(async () => {
    setCarregando(true);
    try {
      const params = {};
      if (abaAtiva !== 'suplementos') {
        if (termoBusca.trim()) params.q = termoBusca.trim();
        if (soCriticos) params.critico = true;
      }
      const resp = await api.get(`/estoque/${abaAtiva}`, { params });
      let dados = resp.data || [];
      if (abaAtiva === 'suplementos' && termoBusca.trim()) {
        const qLower = termoBusca.trim().toLowerCase();
        dados = dados.filter((s) => s.nome.toLowerCase().includes(qLower));
      }
      setItens(dados);
    } catch (err) {
      notificar(err.response?.data?.detail || `Erro ao carregar ${abaAtiva}.`, 'danger');
    } finally {
      setCarregando(false);
    }
  }, [abaAtiva, termoBusca, soCriticos, notificar]);

  useEffect(() => {
    const timer = setTimeout(() => {
      carregarDados();
    }, 180);
    return () => clearTimeout(timer);
  }, [carregarDados]);

  const trocarAba = (novaAba) => {
    setAbaAtiva(novaAba);
    setTermoBusca('');
    setSoCriticos(false);
  };

  const abrirCriar = () => {
    setEditando(null);
    setForm({ ...FORM_PADRAO[abaAtiva] });
    setErroForm('');
    setModalFormAberto(true);
  };

  const abrirEditar = (item) => {
    setEditando(item);
    setErroForm('');
    const base = { ...FORM_PADRAO[abaAtiva] };
    Object.keys(base).forEach((k) => {
      base[k] = item[k] !== null && item[k] !== undefined ? String(item[k]) : '';
    });
    setForm(base);
    setModalFormAberto(true);
  };

  const handleSalvar = async (evento) => {
    evento.preventDefault();
    setErroForm('');
    setSalvando(true);

    try {
      let payload;
      if (abaAtiva === 'molduras') {
        payload = {
          codigo: form.codigo.trim(),
          cor: form.cor.trim(),
          marca: form.marca.trim() || null,
          tamanho_barra: parseFloat(form.tamanho_barra),
          largura_barra: parseFloat(form.largura_barra),
          preco_custo: parseFloat(form.preco_custo),
          preco_venda: parseFloat(form.preco_venda),
          quantidade: parseInt(form.quantidade, 10),
          estoque_minimo: parseInt(form.estoque_minimo, 10),
        };
      } else if (abaAtiva === 'vidros' || abaAtiva === 'fundos') {
        payload = {
          tipo: form.tipo.trim(),
          espessura: parseFloat(form.espessura),
          cor: form.cor.trim() || null,
          area_disponivel_m2: parseFloat(form.area_disponivel_m2 || '0'),
          estoque_minimo_m2: parseFloat(form.estoque_minimo_m2 || '2'),
        };
      } else {
        payload = {
          nome: form.nome.trim(),
          quantidade: parseInt(form.quantidade, 10),
          unidade: form.unidade.trim() || null,
        };
      }

      if (editando) {
        await api.put(`/estoque/${abaAtiva}/${editando.id}`, payload);
        notificar('Item atualizado com sucesso.');
      } else {
        await api.post(`/estoque/${abaAtiva}`, payload);
        notificar('Item cadastrado com sucesso.');
      }
      setModalFormAberto(false);
      carregarDados();
    } catch (err) {
      setErroForm(err.response?.data?.detail || 'Erro ao salvar item de estoque.');
    } finally {
      setSalvando(false);
    }
  };

  const confirmarExclusao = async () => {
    if (!itemExcluir) return;
    setSalvando(true);
    try {
      await api.delete(`/estoque/${abaAtiva}/${itemExcluir.id}`);
      notificar('Item removido do estoque.');
      setItemExcluir(null);
      carregarDados();
    } catch (err) {
      notificar(err.response?.data?.detail || 'Não foi possível excluir este item.', 'danger');
      setItemExcluir(null);
    } finally {
      setSalvando(false);
    }
  };

  const renderAcoes = (row) => (
    <div style={{ display: 'flex', gap: 'var(--at-space-1)', alignItems: 'center' }}>
      {(abaAtiva === 'vidros' || abaAtiva === 'fundos') && (
        <>
          <Button size="sm" variant="secondary" onClick={() => setItemChapas(row)}>
            <Layers size={14} aria-hidden="true" />
            <span>+ Chapas</span>
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setItemAjusteM2(row)}>
            <SlidersHorizontal size={14} aria-hidden="true" />
            <span>Ajustar m²</span>
          </Button>
        </>
      )}
      <Button variant="icon" onClick={() => abrirEditar(row)} aria-label="Editar item">
        <Edit2 size={16} aria-hidden="true" />
      </Button>
      <Button variant="icon" onClick={() => setItemExcluir(row)} aria-label="Excluir item">
        <Trash2 size={16} aria-hidden="true" />
      </Button>
    </div>
  );

  const colunasPorAba = {
    molduras: [
      { key: 'codigo', header: 'Código', render: (r) => <strong className="at-mono">{r.codigo}</strong> },
      { key: 'cor', header: 'Cor' },
      { key: 'barra', header: 'Barra / Largura', numeric: true, render: (r) => `${r.tamanho_barra}m · ${r.largura_barra}cm` },
      { key: 'preco_custo', header: 'Custo (R$/m)', numeric: true, render: (r) => `${formatarMoeda(r.preco_custo)}/m` },
      { key: 'preco_venda', header: 'Venda (R$/m)', numeric: true, render: (r) => `${formatarMoeda(r.preco_venda)}/m` },
      {
        key: 'quantidade',
        header: 'Saldo (Barras)',
        numeric: true,
        render: (r) => (
          <strong className={r.quantidade <= r.estoque_minimo ? 'at-status at-status--financeiro-sem_pagamento' : ''}>
            {r.quantidade} (mín. {r.estoque_minimo})
          </strong>
        ),
      },
      { key: 'acoes', header: 'Ações', render: renderAcoes },
    ],
    vidros: [
      { key: 'tipo', header: 'Tipo' },
      { key: 'espessura', header: 'Espessura', numeric: true, render: (r) => `${r.espessura} mm` },
      { key: 'cor', header: 'Cor', render: (r) => r.cor || '—' },
      {
        key: 'area_disponivel_m2',
        header: 'Saldo (m²)',
        numeric: true,
        render: (r) => (
          <strong
            className={
              Number(r.area_disponivel_m2) <= Number(r.estoque_minimo_m2)
                ? 'at-status at-status--financeiro-sem_pagamento'
                : ''
            }
          >
            {formatarAreaM2(r.area_disponivel_m2)}
          </strong>
        ),
      },
      { key: 'estoque_minimo_m2', header: 'Mínimo (m²)', numeric: true, render: (r) => formatarAreaM2(r.estoque_minimo_m2) },
      { key: 'acoes', header: 'Ações', render: renderAcoes },
    ],
    fundos: [
      { key: 'tipo', header: 'Tipo' },
      { key: 'espessura', header: 'Espessura', numeric: true, render: (r) => `${r.espessura} mm` },
      { key: 'cor', header: 'Cor', render: (r) => r.cor || '—' },
      {
        key: 'area_disponivel_m2',
        header: 'Saldo (m²)',
        numeric: true,
        render: (r) => (
          <strong
            className={
              Number(r.area_disponivel_m2) <= Number(r.estoque_minimo_m2)
                ? 'at-status at-status--financeiro-sem_pagamento'
                : ''
            }
          >
            {formatarAreaM2(r.area_disponivel_m2)}
          </strong>
        ),
      },
      { key: 'estoque_minimo_m2', header: 'Mínimo (m²)', numeric: true, render: (r) => formatarAreaM2(r.estoque_minimo_m2) },
      { key: 'acoes', header: 'Ações', render: renderAcoes },
    ],
    suplementos: [
      { key: 'nome', header: 'Suplemento' },
      { key: 'quantidade', header: 'Quantidade', numeric: true },
      { key: 'unidade', header: 'Unidade', render: (r) => r.unidade || 'un' },
      { key: 'acoes', header: 'Ações', render: renderAcoes },
    ],
  };

  const margemMoldura = (() => {
    const venda = Number(form.preco_venda);
    const custo = Number(form.preco_custo);
    if (!Number.isFinite(venda) || !Number.isFinite(custo) || venda <= 0) return null;
    const diff = venda - custo;
    const pct = (diff / venda) * 100;
    return { diff, pct };
  })();

  return (
    <div>
      <header className="at-page-header">
        <div>
          <h1>Gestão de Estoque</h1>
          <p className="at-page-header__subtitle">
            Molduras por barra (R$/m), vidros e fundos por metragem quadrada (m²) e suplementos manuais.
          </p>
        </div>
        <div className="at-page-header__actions">
          <Link to="/precos" className="at-btn at-btn--secondary">
            Tabelas de Preço
          </Link>
          <Button variant="primary" onClick={abrirCriar}>
            <Plus size={18} aria-hidden="true" />
            <span>Novo Item</span>
          </Button>
        </div>
      </header>

      <Tabs tabs={ABAS} activeId={abaAtiva} onChange={trocarAba} ariaLabel="Categorias do estoque" />

      <Card style={{ marginBottom: 'var(--at-space-4)' }}>
        <div className="at-toolbar" style={{ marginBottom: 0 }}>
          <div className="at-search-box">
            <Search size={18} className="at-search-box__icon" aria-hidden="true" />
            <label htmlFor="busca-estoque" className="at-sr-only">
              Buscar no estoque
            </label>
            <input
              id="busca-estoque"
              type="search"
              className="at-input at-search-box__input"
              placeholder={`Buscar em ${abaAtiva}...`}
              value={termoBusca}
              onChange={(e) => setTermoBusca(e.target.value)}
            />
          </div>

          {abaAtiva !== 'suplementos' && (
            <button
              type="button"
              className="at-chip"
              aria-pressed={soCriticos}
              onClick={() => setSoCriticos((v) => !v)}
            >
              Somente críticos
            </button>
          )}
        </div>
      </Card>

      {carregando ? (
        <div className="at-state" role="status">
          Carregando estoque...
        </div>
      ) : (
        <DataTable
          columns={colunasPorAba[abaAtiva]}
          data={itens}
          emptyTitle="Nenhum item encontrado"
          emptyDescription={
            soCriticos || termoBusca
              ? 'Nenhum item corresponde aos filtros selecionados.'
              : 'Cadastre o primeiro material nesta categoria.'
          }
          emptyAction={
            <Button variant="primary" onClick={abrirCriar}>
              Cadastrar Item
            </Button>
          }
        />
      )}

      <Dialog
        open={modalFormAberto}
        onClose={() => setModalFormAberto(false)}
        title={`${editando ? 'Editar' : 'Novo'} item em ${abaAtiva}`}
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalFormAberto(false)} disabled={salvando}>
              Cancelar
            </Button>
            <Button type="submit" form="form-estoque" variant="primary" loading={salvando}>
              Salvar
            </Button>
          </>
        }
      >
        <form id="form-estoque" onSubmit={handleSalvar}>
          {erroForm && <Callout variant="danger">{erroForm}</Callout>}

          {abaAtiva === 'molduras' && (
            <>
              <div className="at-grid-2">
                <Field id="est-cod" label="Código" required>
                  <input
                    id="est-cod"
                    className="at-input"
                    value={form.codigo}
                    onChange={(e) => setForm({ ...form, codigo: e.target.value })}
                    required
                  />
                </Field>
                <Field id="est-cor" label="Cor" required>
                  <input
                    id="est-cor"
                    className="at-input"
                    value={form.cor}
                    onChange={(e) => setForm({ ...form, cor: e.target.value })}
                    required
                  />
                </Field>
              </div>
              <div className="at-grid-3">
                <Field id="est-tam" label="Tamanho Barra (m)" required>
                  <input
                    id="est-tam"
                    type="number"
                    step="0.01"
                    min="0.01"
                    className="at-input at-num"
                    value={form.tamanho_barra}
                    onChange={(e) => setForm({ ...form, tamanho_barra: e.target.value })}
                    required
                  />
                </Field>
                <Field id="est-larg" label="Largura Barra (cm)" required>
                  <input
                    id="est-larg"
                    type="number"
                    step="0.01"
                    min="0.01"
                    className="at-input at-num"
                    value={form.largura_barra}
                    onChange={(e) => setForm({ ...form, largura_barra: e.target.value })}
                    required
                  />
                </Field>
                <Field id="est-marca" label="Marca">
                  <input
                    id="est-marca"
                    className="at-input"
                    value={form.marca}
                    onChange={(e) => setForm({ ...form, marca: e.target.value })}
                  />
                </Field>
              </div>
              <div className="at-grid-2">
                <Field id="est-custo" label="Preço de Custo (R$/m)" required>
                  <input
                    id="est-custo"
                    type="number"
                    step="0.01"
                    min="0"
                    className="at-input at-num"
                    value={form.preco_custo}
                    onChange={(e) => setForm({ ...form, preco_custo: e.target.value })}
                    required
                  />
                </Field>
                <Field id="est-venda" label="Preço de Venda (R$/m)" required>
                  <input
                    id="est-venda"
                    type="number"
                    step="0.01"
                    min="0"
                    className="at-input at-num"
                    value={form.preco_venda}
                    onChange={(e) => setForm({ ...form, preco_venda: e.target.value })}
                    required
                  />
                </Field>
              </div>
              <CalculadoraCustoBarra
                tamanhoBarra={form.tamanho_barra}
                onAplicarCustoMetro={(valor) => setForm((f) => ({ ...f, preco_custo: valor }))}
              />
              {margemMoldura && (
                <p className="at-field__hint at-num" style={{ marginTop: 'var(--at-space-2)' }}>
                  Margem unitária estimada: {formatarMoeda(margemMoldura.diff)}/m ({margemMoldura.pct.toFixed(1)}%)
                </p>
              )}
              <div className="at-grid-2" style={{ marginTop: 'var(--at-space-3)' }}>
                <Field id="est-qtd" label="Quantidade (Barras)" required>
                  <input
                    id="est-qtd"
                    type="number"
                    step="1"
                    className="at-input at-num"
                    value={form.quantidade}
                    onChange={(e) => setForm({ ...form, quantidade: e.target.value })}
                    required
                  />
                </Field>
                <Field id="est-min" label="Estoque Mínimo (Barras)" required>
                  <input
                    id="est-min"
                    type="number"
                    step="1"
                    min="0"
                    className="at-input at-num"
                    value={form.estoque_minimo}
                    onChange={(e) => setForm({ ...form, estoque_minimo: e.target.value })}
                    required
                  />
                </Field>
              </div>
            </>
          )}

          {(abaAtiva === 'vidros' || abaAtiva === 'fundos') && (
            <>
              <div className="at-grid-2">
                <Field id="ch-tipo" label="Tipo" required>
                  {abaAtiva === 'vidros' ? (
                    <select
                      id="ch-tipo"
                      className="at-input"
                      value={form.tipo}
                      onChange={(e) => setForm({ ...form, tipo: e.target.value })}
                      required
                    >
                      <option value="incolor">incolor</option>
                      <option value="antireflexo">antireflexo</option>
                      <option value="espelho">espelho</option>
                      <option value="outro">outro</option>
                    </select>
                  ) : (
                    <input
                      id="ch-tipo"
                      className="at-input"
                      value={form.tipo}
                      onChange={(e) => setForm({ ...form, tipo: e.target.value })}
                      required
                    />
                  )}
                </Field>
                <Field id="ch-esp" label="Espessura (mm)" required>
                  <input
                    id="ch-esp"
                    type="number"
                    step="0.01"
                    min="0.01"
                    className="at-input at-num"
                    value={form.espessura}
                    onChange={(e) => setForm({ ...form, espessura: e.target.value })}
                    required
                  />
                </Field>
              </div>
              <Field id="ch-cor" label="Cor (opcional)">
                <input
                  id="ch-cor"
                  className="at-input"
                  value={form.cor}
                  onChange={(e) => setForm({ ...form, cor: e.target.value })}
                />
              </Field>
              <div className="at-grid-2">
                <Field id="ch-area" label="Saldo Inicial / Atual (m²)" required>
                  <input
                    id="ch-area"
                    type="number"
                    step="0.0001"
                    className="at-input at-num"
                    value={form.area_disponivel_m2}
                    onChange={(e) => setForm({ ...form, area_disponivel_m2: e.target.value })}
                    required
                  />
                </Field>
                <Field id="ch-min" label="Estoque Mínimo (m²)" required>
                  <input
                    id="ch-min"
                    type="number"
                    step="0.0001"
                    min="0"
                    className="at-input at-num"
                    value={form.estoque_minimo_m2}
                    onChange={(e) => setForm({ ...form, estoque_minimo_m2: e.target.value })}
                    required
                  />
                </Field>
              </div>
            </>
          )}

          {abaAtiva === 'suplementos' && (
            <>
              <Field id="sup-nome" label="Nome do Suplemento" required>
                <input
                  id="sup-nome"
                  className="at-input"
                  value={form.nome}
                  onChange={(e) => setForm({ ...form, nome: e.target.value })}
                  required
                />
              </Field>
              <div className="at-grid-2">
                <Field id="sup-qtd" label="Quantidade" required>
                  <input
                    id="sup-qtd"
                    type="number"
                    min="0"
                    step="1"
                    className="at-input at-num"
                    value={form.quantidade}
                    onChange={(e) => setForm({ ...form, quantidade: e.target.value })}
                    required
                  />
                </Field>
                <Field id="sup-un" label="Unidade">
                  <input
                    id="sup-un"
                    className="at-input"
                    value={form.unidade}
                    onChange={(e) => setForm({ ...form, unidade: e.target.value })}
                    placeholder="un, ml, kg..."
                  />
                </Field>
              </div>
            </>
          )}
        </form>
      </Dialog>

      <ModalEntradaChapas
        categoria={abaAtiva === 'fundos' ? 'fundos' : 'vidros'}
        item={itemChapas}
        onClose={() => setItemChapas(null)}
        onSuccess={(msg) => {
          notificar(msg);
          setItemChapas(null);
          carregarDados();
        }}
      />

      <ModalAjusteM2
        categoria={abaAtiva === 'fundos' ? 'fundos' : 'vidros'}
        item={itemAjusteM2}
        onClose={() => setItemAjusteM2(null)}
        onSuccess={(msg) => {
          notificar(msg);
          setItemAjusteM2(null);
          carregarDados();
        }}
      />

      <ConfirmDialog
        open={Boolean(itemExcluir)}
        onClose={() => setItemExcluir(null)}
        onConfirm={confirmarExclusao}
        title="Confirmar exclusão de item"
        confirmLabel="Excluir item"
        loading={salvando}
      >
        <p>Deseja remover este material do estoque? Itens já vinculados a pedidos são protegidos.</p>
      </ConfirmDialog>
    </div>
  );
};

export default Estoque;
