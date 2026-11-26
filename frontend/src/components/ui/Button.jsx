import React from 'react';

/**
 * Botão padronizado do Design System Atividros.
 *
 * @param {{
 *   variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'icon',
 *   size?: 'md' | 'sm',
 *   loading?: boolean,
 *   className?: string,
 *   type?: 'button' | 'submit' | 'reset',
 *   children: React.ReactNode
 * } & React.ButtonHTMLAttributes<HTMLButtonElement>} props Propriedades do botão.
 * @returns {JSX.Element} Elemento button estilizado.
 */
const Button = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  className = '',
  type = 'button',
  disabled,
  children,
  ...rest
}) => {
  const classes = [
    'at-btn',
    `at-btn--${variant}`,
    size === 'sm' ? 'at-btn--sm' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || loading}
      aria-busy={loading ? 'true' : undefined}
      {...rest}
    >
      {children}
    </button>
  );
};

export default Button;
