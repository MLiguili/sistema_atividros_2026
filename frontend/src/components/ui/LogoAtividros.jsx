import React from 'react';

/**
 * Logotipo oficial Atividros com a composição de molduras entrelaçadas e assinatura em Dancing Script.
 *
 * @param {{
 *   compact?: boolean,
 *   centered?: boolean,
 *   subtitle?: string,
 *   asHeading?: boolean
 * }} props Propriedades de exibição do logotipo.
 * @returns {JSX.Element} Marca oficial Atividros.
 */
const LogoAtividros = ({
  compact = false,
  centered = false,
  subtitle = 'Molduras & Vidros',
  asHeading = false,
}) => {
  const classes = [
    'at-logo',
    compact ? 'at-logo--compact' : '',
    centered ? 'at-logo--centered' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classes}>
      <svg
        viewBox="0 0 130 92"
        className="at-logo__mark"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <rect x="6" y="18" width="32" height="52" strokeWidth="4.5" className="at-logo__frame-bronze" />
        <rect x="8.5" y="20.5" width="27" height="47" strokeWidth="1.2" className="at-logo__frame-champ-in" />
        <rect x="44" y="6" width="30" height="32" strokeWidth="4.2" className="at-logo__frame-champagne" />
        <rect x="46.2" y="8.2" width="25.6" height="27.6" strokeWidth="1" className="at-logo__frame-champ-in" />
        <rect x="43" y="45" width="32" height="34" strokeWidth="4.2" className="at-logo__frame-champagne" />
        <rect x="82" y="19" width="32" height="48" strokeWidth="4.8" className="at-logo__frame-gold" />
        <rect x="84.5" y="21.5" width="27" height="43" strokeWidth="1.1" className="at-logo__frame-gold-in" />
        <rect x="23" y="18" width="36" height="39" strokeWidth="4.5" className="at-logo__frame-lilac" />
        <rect x="64" y="30" width="31" height="54" strokeWidth="4.5" className="at-logo__frame-sky" />
      </svg>

      <div className="at-logo__wordmark-wrap">
        {asHeading ? (
          <h1 className="at-logo__wordmark">Atividros</h1>
        ) : (
          <span className="at-logo__wordmark">Atividros</span>
        )}
        {subtitle && <span className="at-logo__sub">{subtitle}</span>}
      </div>
    </div>
  );
};

export default LogoAtividros;
