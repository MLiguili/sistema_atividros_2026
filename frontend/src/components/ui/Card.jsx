import React from 'react';

/**
 * Contêiner de superfície sólida com borda nítida para agrupamento de conteúdo.
 *
 * @param {{
 *   subtle?: boolean,
 *   className?: string,
 *   children: React.ReactNode
 * } & React.HTMLAttributes<HTMLDivElement>} props Propriedades do card.
 * @returns {JSX.Element} Card estilizado.
 */
const Card = ({ subtle = false, className = '', children, ...rest }) => {
  const classes = ['at-card', subtle ? 'at-card--subtle' : '', className].filter(Boolean).join(' ');
  return (
    <div className={classes} {...rest}>
      {children}
    </div>
  );
};

export default Card;
