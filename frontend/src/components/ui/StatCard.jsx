import React from 'react';
import Card from './Card';

/**
 * Cartão de indicador numérico (KPI) com moldura circular azul-gelo da identidade Atividros.
 *
 * @param {{
 *   icon: React.ReactNode,
 *   label: string,
 *   value: string | number,
 *   tone?: 'brand' | 'info' | 'warning' | 'danger'
 * }} props Propriedades do StatCard.
 * @returns {JSX.Element} Cartão de KPI.
 */
const StatCard = ({ icon, label, value, tone = 'brand' }) => (
  <Card className="at-stat">
    <div className={`at-stat__icon at-stat__icon--${tone}`} aria-hidden="true">
      <div className="at-stat__icon-circle">{icon}</div>
    </div>
    <div>
      <p className="at-stat__label">{label}</p>
      <p className="at-stat__value at-num">{value}</p>
    </div>
  </Card>
);

export default StatCard;
