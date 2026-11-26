import React from 'react';

/**
 * Wrapper acessível de campo de formulário com rótulo associado, dica e erro inline.
 *
 * @param {{
 *   id: string,
 *   label: string,
 *   required?: boolean,
 *   hint?: string,
 *   error?: string,
 *   className?: string,
 *   children: React.ReactNode
 * }} props Propriedades do campo.
 * @returns {JSX.Element} Bloco de campo acessível.
 */
const Field = ({ id, label, required = false, hint = '', error = '', className = '', children }) => {
  const errorId = error ? `${id}-erro` : undefined;
  const hintId = hint ? `${id}-hint` : undefined;

  return (
    <div className={`at-field ${className}`.trim()}>
      <label htmlFor={id} className="at-field__label">
        {label} {required && <span aria-hidden="true">*</span>}
      </label>
      {children}
      {hint && !error && (
        <span id={hintId} className="at-field__hint">
          {hint}
        </span>
      )}
      {error && (
        <span id={errorId} role="alert" className="at-field__error">
          {error}
        </span>
      )}
    </div>
  );
};

export default Field;
