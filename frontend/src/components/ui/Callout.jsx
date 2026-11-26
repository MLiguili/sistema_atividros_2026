import React from 'react';
import { AlertTriangle, CheckCircle2, Info, OctagonAlert } from 'lucide-react';

const ICONES = {
  warning: AlertTriangle,
  danger: OctagonAlert,
  info: Info,
  success: CheckCircle2,
};

/**
 * Banner contextual para avisos não-bloqueantes (warning/info) ou erros bloqueantes (danger).
 *
 * @param {{
 *   variant?: 'warning' | 'danger' | 'info' | 'success',
 *   role?: string,
 *   className?: string,
 *   children: React.ReactNode
 * }} props Propriedades do Callout.
 * @returns {JSX.Element} Callout estilizado.
 */
const Callout = ({ variant = 'info', role, className = '', children }) => {
  const Icon = ICONES[variant] || Info;
  const ariaRole = role || (variant === 'danger' ? 'alert' : 'status');

  return (
    <div role={ariaRole} className={`at-callout at-callout--${variant} ${className}`.trim()}>
      <Icon size={18} aria-hidden="true" style={{ flexShrink: 0, marginTop: '2px' }} />
      <div>{children}</div>
    </div>
  );
};

export default Callout;
