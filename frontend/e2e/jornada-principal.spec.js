import { expect, test } from '@playwright/test';
import { fazerLoginAdmin, monitorarErrosCriticos } from './helpers/auth';

test.describe('Atividros E2E — Jornada Operacional Resiliente', () => {
  test('rejeita senha inválida e autentica admin abrindo Dashboard', async ({ page }) => {
    const monitor = monitorarErrosCriticos(page);

    await page.goto('/login');
    await page.getByLabel(/usuário/i).fill('admin');
    await page.getByLabel(/senha/i).fill('senha-incorreta');
    await page.getByRole('button', { name: /entrar/i }).click();

    await expect(page.getByRole('alert')).toContainText(/usuário ou senha inválidos/i);

    await fazerLoginAdmin(page);
    await expect(page.getByText(/pedidos ativos/i)).toBeVisible();
    monitor.assertSemErros();
  });

  test('exibe todas as 4 tabelas de preço incluindo a aba Molduras', async ({ page }) => {
    const monitor = monitorarErrosCriticos(page);
    await fazerLoginAdmin(page);

    await page.getByRole('link', { name: /tabelas de preço/i }).click();
    await expect(page).toHaveURL(/\/precos/);

    await expect(page.getByRole('tab', { name: /vidros e espelhos/i })).toBeVisible();
    await page.getByRole('tab', { name: /fundos/i }).click();
    await expect(page.getByRole('cell', { name: /MDF 3mm/i }).first()).toBeVisible();

    await page.getByRole('tab', { name: /paspatour/i }).click();
    await expect(page.getByRole('cell', { name: /Branco Clássico/i }).first()).toBeVisible();

    await page.getByRole('tab', { name: /molduras/i }).click();
    await expect(page.getByRole('cell', { name: /MLD-PRETA-2CM/i })).toBeVisible();
    monitor.assertSemErros();
  });

  test('executa fluxo Calculadora -> Pedido (abaixo do sugerido) -> Lista -> Pagamento -> Baixa Assistida -> PDF', async ({ page }) => {
    const monitor = monitorarErrosCriticos(page);
    await fazerLoginAdmin(page);

    await page.getByRole('navigation').getByRole('link', { name: /calculadora/i }).click();
    await expect(page).toHaveURL(/\/calculadora/);

    // Garante que não existem mais seletores duplicados de chapa física no formulário
    await expect(page.getByLabel(/chapa física no estoque/i)).toHaveCount(0);
    await expect(page.getByLabel(/chapa de fundo no estoque/i)).toHaveCount(0);

    // Aguarda carregamento do catálogo de vidros e seleciona uma moldura para validar cálculo + baixa reais
    await expect(page.getByLabel(/vidro \/ espelho/i)).not.toHaveValue('');
    await page.getByRole('button', { name: /adicionar moldura/i }).click();
    const selectMoldura = page.getByLabel(/moldura camada 1/i);
    await expect(selectMoldura).toContainText(/MLD-PRETA-2CM/i);
    await selectMoldura.selectOption({ index: 1 });

    await page.getByLabel(/largura obra/i).fill('45');
    await page.getByLabel(/altura obra/i).fill('35');
    await page.getByRole('button', { name: /calcular orçamento/i }).click();

    await expect(page.getByText(/unitário sugerido:/i)).toBeVisible();
    await page.getByRole('button', { name: /adicionar ao pedido/i }).click();

    await expect(page).toHaveURL(/\/pedidos/);
    const dialogNovo = page.getByRole('dialog');
    await expect(dialogNovo).toBeVisible();
    await expect(dialogNovo.getByLabel(/cliente/i)).not.toHaveValue('');

    const inputPreco = dialogNovo.getByLabel(/preço unit\. praticado/i);
    await inputPreco.fill('50');
    await expect(dialogNovo.getByText(/abaixo do valor sugerido/i)).toBeVisible();

    const respCriarPromise = page.waitForResponse(
      (resp) => resp.url().includes('/pedidos/') && resp.request().method() === 'POST',
    );
    await dialogNovo.getByRole('button', { name: /criar orçamento/i }).click();
    const respCriar = await respCriarPromise;
    expect(respCriar.status()).toBe(201);
    const pedidoCriado = await respCriar.json();

    // Alterna para visão Lista e filtra Orçamentos (Rascunho)
    await page.getByRole('button', { name: /^lista$/i }).click();
    await page.getByRole('button', { name: /orçamentos \(rascunho\)/i }).click();

    const linhaPedido = page.getByRole('row', { name: new RegExp(pedidoCriado.numero_pedido) });
    await expect(linhaPedido).toBeVisible();
    await linhaPedido.getByRole('button', { name: /detalhes/i }).click();

    // Registra pagamento parcial para confirmar o orçamento automaticamente
    const modalDetalhe = page.getByRole('dialog', { name: new RegExp(`Pedido ${pedidoCriado.numero_pedido}`) });
    await expect(modalDetalhe).toBeVisible();
    await modalDetalhe.getByRole('button', { name: /^pagamentos$/i }).click();

    const modalPagamento = page.getByRole('dialog', { name: new RegExp(`Pagamentos — ${pedidoCriado.numero_pedido}`) });
    await modalPagamento.getByLabel(/valor \(R\$\)/i).fill('20');
    await modalPagamento.getByRole('button', { name: /registrar pagamento/i }).click();
    await expect(modalPagamento.getByRole('button', { name: /estornar/i })).toBeVisible();
    await modalPagamento.getByRole('button', { name: /fechar/i }).click();

    // Verifica que o status geral virou Confirmado e dispara Baixa Assistida
    await expect(modalDetalhe.getByText(/Confirmado/i).first()).toBeVisible();
    await modalDetalhe.getByRole('button', { name: /baixar e produzir/i }).click();

    const modalBaixa = page.getByRole('dialog', { name: new RegExp(`Baixa Assistida — ${pedidoCriado.numero_pedido}`) });
    await modalBaixa.getByRole('button', { name: /confirmar baixa e iniciar produção/i }).click();

    await expect(modalDetalhe.getByText(/Em Produção/i).first()).toBeVisible();

    // Verifica geração do PDF sem erro (status 200 application/pdf)
    const respPdfPromise = page.waitForResponse(
      (resp) => resp.url().includes(`/pedidos/${pedidoCriado.id}/pdf`) && resp.request().method() === 'GET',
    );
    await modalDetalhe.getByRole('button', { name: /baixar pdf/i }).click();
    const respPdf = await respPdfPromise;
    expect(respPdf.status()).toBe(200);
    expect(respPdf.headers()['content-type']).toContain('application/pdf');

    monitor.assertSemErros();
  });

  test('abre pedido antigo no histórico do cliente e salta para Pedidos', async ({ page }) => {
    const monitor = monitorarErrosCriticos(page);
    await fazerLoginAdmin(page);

    await page.getByRole('link', { name: /clientes/i }).click();
    await expect(page).toHaveURL(/\/clientes/);

    await page.getByRole('button', { name: /ver histórico de marina/i }).click();
    const modalHist = page.getByRole('dialog');
    await expect(modalHist).toBeVisible();

    const btnPedidoAntigo = modalHist.getByRole('button', { name: /#\d+/ }).first();
    await expect(btnPedidoAntigo).toBeVisible();
    await btnPedidoAntigo.click();

    await expect(modalHist.getByRole('heading', { name: /itens do pedido/i })).toBeVisible();
    await expect(modalHist.getByRole('heading', { name: /pagamentos/i })).toBeVisible();

    await modalHist.getByRole('button', { name: /voltar ao histórico/i }).click();
    await expect(modalHist.getByRole('button', { name: /#\d+/ }).first()).toBeVisible();

    await modalHist.getByRole('button', { name: /#\d+/ }).first().click();
    await modalHist.getByRole('button', { name: /abrir em pedidos/i }).click();

    await expect(page).toHaveURL(/\/pedidos/);
    await expect(page.getByRole('dialog')).toBeVisible();
    monitor.assertSemErros();
  });

  test('navega pelas 4 abas do Estoque validando dados reais', async ({ page }) => {
    const monitor = monitorarErrosCriticos(page);
    await fazerLoginAdmin(page);

    await page.getByRole('navigation').getByRole('link', { name: /estoque/i }).click();
    await expect(page).toHaveURL(/\/estoque/);

    await expect(page.getByRole('cell', { name: /MLD-PRETA-2CM/i })).toBeVisible();
    await page.getByRole('tab', { name: /vidros/i }).click();
    await expect(page.getByRole('cell', { name: /incolor/i }).first()).toBeVisible();

    await page.getByRole('tab', { name: /fundos/i }).click();
    await expect(page.getByRole('cell', { name: /MDF 3mm/i }).first()).toBeVisible();

    await page.getByRole('tab', { name: /suplementos/i }).click();
    await expect(page.getByRole('cell', { name: /Grampo Flexível/i })).toBeVisible();
    monitor.assertSemErros();
  });
});
