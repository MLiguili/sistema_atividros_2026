import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/config';
import { useToast } from '../context/ContextoToast';
import Callout from '../components/ui/Callout';
import FormComposicaoQuadro from '../components/calculadora/FormComposicaoQuadro';
import PainelResultadoCalculo from '../components/calculadora/PainelResultadoCalculo';

const ESTADO_INICIAL = {
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
 * Página da Calculadora Unificada (Quadro Sob Medida e Vidro Avulso) com envio direto para Pedido.
 *
 * @returns {JSX.Element} Página Calculadora.
 */
const Calculadora = () => {
  const { notificar } = useToast();
  const navigate = useNavigate();

  const [modo, setModo] = useState('quadro_sob_medida');
  const [dados, setDados] = useState(ESTADO_INICIAL);
  const [catalogos, setCatalogos] = useState({
    molduras: [],
    vidros: [],
    fundos: [],
    tabelaVidro: [],
    tabelaFundo: [],
    tabelaPaspatour: [],
  });
  const [resultado, setResultado] = useState(null);
  const [erro, setErro] = useState('');
  const [calculando, setCalculando] = useState(false);

  useEffect(() => {
    const carregarCatalogos = async () => {
      try {
        const [m, v, f, tv, tf, tp] = await Promise.all([
          api.get('/estoque/molduras'),
          api.get('/estoque/vidros'),
          api.get('/estoque/fundos'),
          api.get('/calculadora/tabela-vidro'),
          api.get('/calculadora/tabela-fundo'),
          api.get('/calculadora/tabela-paspatour'),
        ]);
        const tabelaVidro = tv.data || [];
        const tabelaPaspatour = tp.data || [];
        setCatalogos({
          molduras: m.data || [],
          vidros: v.data || [],
          fundos: f.data || [],
          tabelaVidro,
          tabelaFundo: tf.data || [],
          tabelaPaspatour,
        });
        setDados((atual) => ({
          ...atual,
          vidro_tipo: atual.vidro_tipo || tabelaVidro[0]?.tipo || '',
          paspatour_id: atual.paspatour_id || (tabelaPaspatour[0] ? String(tabelaPaspatour[0].id) : ''),
        }));
      } catch (err) {
        notificar(err.response?.data?.detail || 'Erro ao carregar catálogos da calculadora.', 'danger');
      }
    };
    carregarCatalogos();
  }, [notificar]);

  const calcular = async () => {
    setErro('');
    if (!dados.obra_largura || !dados.obra_altura || Number(dados.obra_largura) <= 0 || Number(dados.obra_altura) <= 0) {
      setErro('Informe largura e altura válidas maiores que zero.');
      return;
    }

    setCalculando(true);
    try {
      let resp;
      if (modo === 'vidro_avulso') {
        resp = await api.post('/calculadora/vidro-avulso', {
          largura: parseFloat(dados.obra_largura),
          altura: parseFloat(dados.obra_altura),
          quantidade: parseInt(dados.quantidade || '1', 10),
          vidro_tipo: dados.vidro_tipo || 'incolor',
          vidro_id: dados.vidro_id ? parseInt(dados.vidro_id, 10) : null,
          mao_de_obra: parseFloat(dados.mao_de_obra || '0'),
        });
      } else {
        resp = await api.post('/calculadora/quadro', {
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
      }
      setResultado(resp.data);
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao calcular orçamento.');
    } finally {
      setCalculando(false);
    }
  };

  const handleAdicionarAoPedido = () => {
    if (!resultado) return;
    const itemCalculadora = {
      tipo_item: modo,
      descricao: resultado.descricao_sugerida,
      quantidade: parseInt(dados.quantidade || '1', 10),
      valor_sugerido: Number(resultado.valor_sugerido_unitario),
      preco_unitario: Number(resultado.valor_sugerido_unitario),
      obra_largura: parseFloat(dados.obra_largura),
      obra_altura: parseFloat(dados.obra_altura),
      paspatour: modo === 'quadro_sob_medida' ? Boolean(dados.paspatour) : false,
      tamanho_paspatour:
        modo === 'quadro_sob_medida' && dados.paspatour ? parseFloat(dados.tamanho_paspatour || '0') : 0,
      paspatour_id:
        modo === 'quadro_sob_medida' && dados.paspatour && dados.paspatour_id
          ? parseInt(dados.paspatour_id, 10)
          : null,
      vidro_tipo: dados.vidro_tipo || null,
      vidro_id: dados.vidro_id ? parseInt(dados.vidro_id, 10) : null,
      fundo_tipo: modo === 'quadro_sob_medida' ? dados.fundo_tipo || null : null,
      fundo_id: modo === 'quadro_sob_medida' && dados.fundo_id ? parseInt(dados.fundo_id, 10) : null,
      mao_de_obra: parseFloat(dados.mao_de_obra || '0'),
      molduras:
        modo === 'quadro_sob_medida'
          ? dados.molduras
              .filter((m) => m.moldura_id)
              .map((m, idx) => ({ moldura_id: parseInt(m.moldura_id, 10), ordem: idx }))
          : [],
    };
    navigate('/pedidos', { state: { itemCalculadora } });
  };

  return (
    <div>
      <header className="at-page-header">
        <div>
          <h1>Calculadora Unificada</h1>
          <p className="at-page-header__subtitle">
            Propagação de dimensões, perda em 45°, área mínima, mão de obra e envio direto para pedido.
          </p>
        </div>
      </header>

      {erro && <Callout variant="danger">{erro}</Callout>}

      <div className="at-calc-grid">
        <FormComposicaoQuadro
          modo={modo}
          onChangeModo={(novoModo) => {
            setModo(novoModo);
            setResultado(null);
            setErro('');
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
          onAdicionarAoPedido={handleAdicionarAoPedido}
        />
      </div>
    </div>
  );
};

export default Calculadora;
