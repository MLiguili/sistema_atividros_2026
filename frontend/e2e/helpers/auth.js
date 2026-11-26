import { expect } from '@playwright/test';

/**
 * Realiza login completo no sistema pela interface semântica de /login usando credenciais admin.
 *
 * @param {import('@playwright/test').Page} page Página ativa do Playwright.
 * @param {{ usuario?: string, senha?: string }} [credenciais] Credenciais opcionais.
 * @returns {Promise<void>}
 */
export async function fazerLoginAdmin(page, credenciais = {}) {
  const usuario = credenciais.usuario || process.env.E2E_USER || 'admin';
  const senha = credenciais.senha || process.env.E2E_PASS || 'admin123';

  await page.goto('/login');
  await page.getByLabel(/usuário/i).fill(usuario);
  await page.getByLabel(/senha/i).fill(senha);
  await page.getByRole('button', { name: /entrar/i }).click();

  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole('heading', { name: /painel geral|dashboard|visão geral/i })).toBeVisible();
}

/**
 * Registra listeners de erros não tratados de runtime e respostas HTTP >= 500 durante o teste E2E.
 *
 * @param {import('@playwright/test').Page} page Página ativa do Playwright.
 * @returns {{ assertSemErros: () => void }} Verificador para chamar ao final do cenário.
 */
export function monitorarErrosCriticos(page) {
  const falhas = [];
  page.on('pageerror', (err) => falhas.push(`pageerror: ${err.message}`));
  page.on('response', (resp) => {
    if (resp.status() >= 500) {
      falhas.push(`HTTP ${resp.status()} em ${resp.url()}`);
    }
  });

  return {
    assertSemErros: () => {
      expect(falhas, `Erros detectados durante navegação E2E:\n${falhas.join('\n')}`).toEqual([]);
    },
  };
}
