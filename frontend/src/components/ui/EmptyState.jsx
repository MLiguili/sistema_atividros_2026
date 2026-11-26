import React from 'react';
import { Inbox } from 'lucide-react';

/**
 * Estado vazio ou informativo reutilizável com título, descrição e ação resolutiva opcional.
 *
 * @param {{
 *   icon?: React.ReactNode,
 *   title: string,
 *   description?: string,
 *   action?: React.ReactNode
 * }} props Propriedades do EmptyState.
 * @returns {JSX.Element} Bloco de estado vazio.
 */
const EmptyState = ({ icon, title, description = '', action = null }) => (
  <div className="at-state">
    {icon || <Inbox size={36} aria-hidden="true" />}
    <div>
      <p style={{ fontWeight: 600 }}>{title}</p>
      {description && <p className="at-muted">{description}</p>}
    </div>
    {action}
  </div>
);

export default EmptyState;
