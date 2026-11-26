import React from 'react';
import EmptyState from './EmptyState';

/**
 * Tabela responsiva com wrapper horizontal seguro e estado vazio configurável.
 *
 * @param {{
 *   columns: Array<{ key: string, header: string, numeric?: boolean, render?: (row: any) => React.ReactNode }>,
 *   data: Array<any>,
 *   keyField?: string,
 *   emptyTitle?: string,
 *   emptyDescription?: string,
 *   emptyAction?: React.ReactNode
 * }} props Propriedades do DataTable.
 * @returns {JSX.Element} Tabela ou estado vazio.
 */
const DataTable = ({
  columns,
  data,
  keyField = 'id',
  emptyTitle = 'Nenhum registro encontrado',
  emptyDescription = '',
  emptyAction = null,
}) => {
  if (!data || data.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} action={emptyAction} />;
  }

  return (
    <div className="at-table-wrap">
      <table className="at-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key} scope="col">
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row[keyField]}>
              {columns.map((col) => (
                <td key={col.key} className={col.numeric ? 'at-num' : undefined}>
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DataTable;
