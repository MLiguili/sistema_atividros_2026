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
import CalculadoraCustoBarra from '../components/estoque/CalculadoraCustoBarra';
import { formatarAreaM2, formatarMedidaCm, formatarMetragem, formatarMoeda } from '../utils/formatadores';

const ABAS = [
  { id: 'vidro', label: 'Vidros e Espelhos' },
  { id: 'fundo', label: 'Fundos' },
  { id: 'paspatour', label: 'Paspatour' },
  { id: 'moldura', label: 'Molduras' },
];

const FORM_INICIAL = {
  tipo: '',
  descricao: '',
  preco_por_m2: '',
  area_minima_m2: '0.2500',
  codigo: '',
  cor: '',
  marca: '',
  largura_barra: '3.00',
  tamanho_barra: '2.75',
  preco_custo: '',
  preco_venda: '',
};

/**
 * Página dedicada ao gerenciamento das tabelas de preço por m² (Vidro, Fundo e Paspatour)
 * e preços por metro linear das Molduras cadastradas.
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
  const [form, setForm] = useState(FORM_INICIAL);

  const endpointPorAba = {
    vidro: '/calculadora/tabela-vidro',
    fundo: '/calculadora/tabela-fundo',
    paspatour: '/calculadora/tabela-paspatour',
    moldura: '/estoque/molduras',
  };
  const endpointBase = endpointPorAba[aba];

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
    setForm(FORM_INICIAL);
    setModalAberto(true);
  };

  const abrirEditar = (item) => {
    setEditando(item);
    setErro('');
    setForm({
      ...FORM_INICIAL,
      tipo: item.tipo || '',
      descricao: item.descricao || '',
      preco_por_m2: String(item.preco_por_m2 ?? ''),
      area_minima_m2: String(item.area_minima_m2 ?? '0.2500'),
      codigo: item.codigo || '',
      cor: item.cor || '',
      marca: item.marca || '',
      largura_barra: String(item.largura_barra ?? '3.00'),
      tamanho_barra: String(item.tamanho_barra ?? '2.75'),
      preco_custo: String(item.preco_custo ?? ''),
      preco_venda: String(item.preco_venda ?? ''),
    });
    setModalAberto(true);
  };

  const handleSalvar = async (evento) => {
    evento.preventDefault();
    setErro('');
    setSalvando(true);

    try {
      let payload;
      if (aba === 'vidro') {
        payload = {
          ...(editando ? {} : { tipo: form.tipo.trim() }),
          preco_por_m2: parseFloat(form.preco_por_m2),
          area_minima_m2: parseFloat(form.area_minima_m2 || '0.25'),
          descricao: form.descricao,
        };
      } else if (aba === 'fundo') {
        payload = {
          tipo: form.tipo.trim(),
          preco_por_m2: parseFloat(form.preco_por_m2),
          descricao: form.descricao,
        };
      } else if (aba === 'moldura') {
        payload = {
          codigo: form.codigo.trim(),
          cor: form.cor.trim(),
          marca: form.marca.trim() || null,
          largura_barra: parseFloat(form.largura_barra),
          tamanho_barra: parseFloat(form.tamanho_barra),
          preco_custo: parseFloat(form.preco_custo),
          preco_venda: parseFloat(form.preco_venda),
          ...(editando ? {} : { quantidade: 0, estoque_minimo: 5 }),
        };
      } else {
        payload = {
          descricao: form.descricao.trim(),
          preco_por_m2: parseFloat(form.preco_por_m2),
        };
      }

      if (editando) {
        await api.put(`${endpointBase}/${editando.id}`, payload);
      } else {
        await api.post(endpointBase, payload);
      }

      notificar(aba === 'moldura' ? 'Moldura atualizada com sucesso.' : 'Tabela de preço atualizada com sucesso.');
      setModalAberto(false);
      carregar();
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao salvar registro.');
    } finally {
      setSalvando(false);
    }
  };

  const handleExcluir = async () => {
    if (!excluirAlvo) return;
    setSalvando(true);
    try {
      await api.delete(`${endpointBase}/${excluirAlvo.id}`);
      notificar(aba === 'moldura' ? 'Moldura removida.' : 'Faixa de preço removida.');
      setExcluirAlvo(null);
      carregar();
    } catch (err) {
      notificar(err.response?.data?.detail || 'Erro ao excluir registro.', 'danger');
      setExcluirAlvo(null);
    } finally {
      setSalvando(false);
    }
  };

  const colunaAcoes = {
    key: 'acoes',
    header: 'Ações',
    render: (r) => (
      <div style={{ display: 'flex', gap: 'var(--at-space-1)' }}>
        <Button variant="icon" onClick={() => abrirEditar(r)} aria-label="Editar registro">
          <Edit2 size={16} aria-hidden="true" />
        </Button>
        <Button variant="icon" onClick={() => setExcluirAlvo(r)} aria-label="Excluir registro">
          <Trash2 size={16} aria-hidden="true" />
        </Button>
      </div>
    ),
  };

  const colunas =
    aba === 'moldura'
      ? [
          { key: 'codigo', header: 'Código' },
          {
            key: 'cor',
            header: 'Cor / Marca',
            render: (r) => (
              <div>
                <div>{r.cor}</div>
                {r.marca && <div className="at-muted">{r.marca}</div>}
              </div>
            ),
          },
          {
            key: 'barra',
            header: 'Barra (Larg. × Comp.)',
            numeric: true,
            render: (r) => `${formatarMedidaCm(r.largura_barra)} × ${formatarMetragem(r.tamanho_barra)}`,
          },
          {
            key: 'preco_custo',
            header: 'Custo (R$/m)',
            numeric: true,
            render: (r) => `${formatarMoeda(r.preco_custo)}/m`,
          },
          {
            key: 'preco_venda',
            header: 'Venda (R$/m)',
            numeric: true,
            render: (r) => <strong>{`${formatarMoeda(r.preco_venda)}/m`}</strong>,
          },
          colunaAcoes,
        ]
      : [
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
          colunaAcoes,
        ];

  return (
    <div>
      <header className="at-page-header">
        <div>
          <h1>Tabelas de Preço</h1>
          <p className="at-page-header__subtitle">
            Valores por m² (vidros, fundos, paspatour) e por metro linear (molduras) usados na Calculadora Unificada.
          </p>
        </div>
        <div className="at-page-header__actions">
          <Button variant="primary" onClick={abrirCriar}>
            <Plus size={18} aria-hidden="true" />
            <span>{aba === 'moldura' ? 'Nova Moldura' : 'Nova Faixa'}</span>
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
            emptyTitle={aba === 'moldura' ? 'Nenhuma moldura cadastrada' : 'Nenhuma faixa cadastrada'}
            emptyDescription={
              aba === 'moldura'
                ? 'Cadastre molduras para habilitar seleção e cálculo linear na Calculadora.'
                : 'Adicione os valores por m² para habilitar cálculos nesta categoria.'
            }
            emptyAction={
              <Button variant="primary" onClick={abrirCriar}>
                {aba === 'moldura' ? 'Cadastrar Moldura' : 'Cadastrar Preço'}
              </Button>
            }
          />
        </Card>
      )}

      <Dialog
        open={modalAberto}
        onClose={() => setModalAberto(false)}
        title={
          aba === 'moldura'
            ? editando
              ? `Editar Moldura ${editando.codigo}`
              : 'Nova Moldura'
            : editando
              ? 'Editar Faixa de Preço'
              : 'Nova Faixa de Preço'
        }
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
        <form id="form-tabela-preco" onSubmit={handleSalvar} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--at-space-3)' }}>
          {erro && <Callout variant="danger">{erro}</Callout>}

          {aba === 'moldura' ? (
            <>
              <div className="at-grid-2">
                <Field id="tp-mld-codigo" label="Código" required>
                  <input
                    id="tp-mld-codigo"
                    className="at-input"
                    value={form.codigo}
                    onChange={(e) => setForm({ ...form, codigo: e.target.value })}
                    required
                  />
                </Field>
                <Field id="tp-mld-cor" label="Cor / Acabamento" required>
                  <input
                    id="tp-mld-cor"
                    className="at-input"
                    value={form.cor}
                    onChange={(e) => setForm({ ...form, cor: e.target.value })}
                    required
                  />
                </Field>
              </div>

              <Field id="tp-mld-marca" label="Marca / Fornecedor">
                <input
                  id="tp-mld-marca"
                  className="at-input"
                  value={form.marca}
                  onChange={(e) => setForm({ ...form, marca: e.target.value })}
                />
              </Field>

              <div className="at-grid-2">
                <Field id="tp-mld-largura" label="Largura do Perfil (cm)" required>
                  <input
                    id="tp-mld-largura"
                    type="number"
                    step="0.01"
                    min="0.1"
                    className="at-input at-num"
                    value={form.largura_barra}
                    onChange={(e) => setForm({ ...form, largura_barra: e.target.value })}
                    required
                  />
                </Field>
                <Field id="tp-mld-tamanho" label="Comprimento da Barra (m)" required>
                  <input
                    id="tp-mld-tamanho"
                    type="number"
                    step="0.01"
                    min="0.1"
                    className="at-input at-num"
                    value={form.tamanho_barra}
                    onChange={(e) => setForm({ ...form, tamanho_barra: e.target.value })}
                    required
                  />
                </Field>
              </div>

              <div className="at-grid-2">
                <Field id="tp-mld-custo" label="Custo por Metro (R$/m)" required>
                  <input
                    id="tp-mld-custo"
                    type="number"
                    step="0.01"
                    min="0"
                    className="at-input at-num"
                    value={form.preco_custo}
                    onChange={(e) => setForm({ ...form, preco_custo: e.target.value })}
                    required
                  />
                </Field>
                <Field id="tp-mld-venda" label="Preço de Venda (R$/m)" required>
                  <input
                    id="tp-mld-venda"
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
                onAplicarCustoMetro={(custoMetro) => setForm((f) => ({ ...f, preco_custo: custoMetro }))}
              />
            </>
          ) : (
            <>
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
            </>
          )}
        </form>
      </Dialog>

      <ConfirmDialog
        open={Boolean(excluirAlvo)}
        onClose={() => setExcluirAlvo(null)}
        onConfirm={handleExcluir}
        title="Confirmar exclusão"
        confirmLabel={aba === 'moldura' ? 'Excluir moldura' : 'Excluir faixa'}
        loading={salvando}
      >
        <p>
          {aba === 'moldura'
            ? 'Deseja remover esta moldura? Caso esteja vinculada a pedidos existentes, a exclusão será bloqueada.'
            : 'Deseja remover esta faixa de preço? Essa ação não altera pedidos já gravados.'}
        </p>
      </ConfirmDialog>
    </div>
  );
};

export default TabelasPreco;
