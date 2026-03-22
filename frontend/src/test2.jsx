import React, { useState, useEffect } from 'react';
const Test2 = () => {
  const [visualizacao, setVisualizacao] = useState('kanban');
  const colunasKanban = [{ key: 'a', label: 'A', cor: '#f00' }];
  const pedidos = [];
  
  const renderCardPedido = (p) => <div key={p.id}>test</div>;
  
  const colunas = colunasKanban.map(c => c.key);
  const pedidosPorColuna = colunas.reduce((acc, k) => ({...acc, [k]: []}), {});
  
  return (
    <div>
      <button onClick={() => setVisualizacao('kanban')}>Kanban</button>
      <button onClick={() => setVisualizacao('lista')}>Lista</button>
      {visualizacao === 'kanban' ? (
        <div>
          {colunas.map(c => <div key={c}>{pedidosPorColuna[c]?.length || 0}</div>)}
        </div>
      ) : (
        <div>Lista</div>
      )}
    </div>
  );
};
export default Test2;
