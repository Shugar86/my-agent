import { test, expect } from '@playwright/test';

/**
 * Investor funnel smoke tests — landing, public demo, login rebrand.
 * Requires running server on :8020 with seeded templates for live demo run.
 */

test.describe('Investor funnel', () => {
  test('landing is outcome-focused, not dev docs', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText(/90 секунд/i);
    await expect(page.locator('body')).toContainText(/50\+/);
    await expect(page.locator('body')).not.toContainText(/376 тестов/i);
    await expect(page.locator('body')).not.toContainText(/Dual Provider/i);
    await expect(page.getByRole('link', { name: /Попробовать live/i })).toHaveAttribute('href', '/demo');
  });

  test('pricing section exists on landing', async ({ page }) => {
    await page.goto('/#pricing');
    await expect(page.locator('#pricing')).toBeVisible();
    await expect(page.locator('body')).toContainText(/Starter/i);
    await expect(page.locator('body')).toContainText(/Enterprise/i);
  });

  test('public demo page loads', async ({ page }) => {
    await page.goto('/demo');
    await expect(page.locator('h1')).toContainText(/Competitor Intelligence/i);
    await expect(page.getByRole('button', { name: /Запустить за 90 сек/i })).toBeVisible();
  });

  test('login has no dev credentials by default', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('body')).not.toContainText(/admin \/ admin/i);
    await expect(page.getByRole('link', { name: /Попробовать без регистрации/i })).toHaveAttribute('href', '/demo');
  });

  test('landing hero has product screenshot', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.hero-visual img')).toHaveAttribute('src', /product-dashboard/);
  });

  test('login uses external CSS', async ({ page }) => {
    await page.goto('/login');
    const styles = await page.locator('link[rel="stylesheet"]').all();
    const hrefs = await Promise.all(styles.map((l) => l.getAttribute('href')));
    expect(hrefs.some((h) => h?.includes('login.css'))).toBeTruthy();
    await expect(page.locator('style')).toHaveCount(0);
  });

  test('demo timeline uses RU heading', async ({ page }) => {
    await page.goto('/demo');
    await expect(page.locator('.demo-timeline h2')).toContainText(/Выполнение workflow/i);
  });

  test('login shows dev credentials with ?dev=1', async ({ page }) => {
    await page.goto('/login?dev=1');
    await expect(page.locator('#dev-footer')).toBeVisible();
    await expect(page.locator('#dev-footer')).toContainText(/admin \/ admin/i);
  });

  test('landing has problems and live-demo sections', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#problems')).toBeVisible();
    await expect(page.locator('#problems')).toContainText(/4 часа/i);
    await expect(page.locator('#live-demo')).toBeVisible();
    await expect(page.locator('#live-demo iframe')).toHaveAttribute('src', '/demo');
  });

  test('landing marketplace preview section exists', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#marketplace-preview')).toBeVisible();
  });
});

test.describe('Public demo run', () => {
  test.skip(!process.env.E2E_DEMO_RUN, 'Set E2E_DEMO_RUN=1 to test live mock demo completion');

  test('mock run completes with artifact link on /demo', async ({ page }) => {
    test.setTimeout(120_000);
    await page.goto('/demo');
    await page.getByRole('button', { name: /Запустить за 90 сек/i }).click();
    await expect(page.locator('#timeline')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole('link', { name: /Скачать brief/i })).toBeVisible({ timeout: 90_000 });
    await expect(page.locator('#stickyCta')).toHaveClass(/visible/);
  });
});

test.describe('Showcase demo-MVP', () => {
  test('showcase page renders hero and 7 cards', async ({ page }) => {
    await page.goto('/showcase');
    await expect(page.locator('h1')).toContainText(/AI-операторы/i);
    await expect(page.locator('.showcase-card')).toHaveCount(7);
    await expect(page.locator('.showcase-stat-value[data-stat="live"]')).toHaveText('7');
  });

  test('persona accordion expands with YAML content', async ({ page }) => {
    await page.goto('/showcase');
    const accordion = page.locator('.showcase-card').first().locator('.persona-accordion');
    await accordion.locator('summary').click();
    await expect(accordion.locator('.persona-role')).toBeVisible();
    await expect(accordion.locator('.persona-snippet')).toBeVisible();
  });

  test('CTA form submits and shows Telegram deep-link', async ({ page }) => {
    await page.goto('/showcase#cta');
    await page.waitForSelector('#leadVertical option[value="ararat"]');
    await page.fill('#leadTelegram', '@investor_test');
    await page.selectOption('#leadVertical', 'ararat');
    await page.fill('#leadEmail', 'test@example.com');
    await page.getByRole('button', { name: /Получить AI-оператора/i }).click();
    await expect(page.locator('#leadThankyou')).toBeVisible({ timeout: 10_000 });
    await expect(page.locator('#leadTelegramLink')).toHaveAttribute('href', /preset_ararat/);
  });
});

test.describe('Showcase playground run', () => {
  test.skip(!process.env.E2E_DEMO_RUN, 'Set E2E_DEMO_RUN=1 to test live mock demo completion');

  test('playground preset completes with DOCX link', async ({ page }) => {
    test.setTimeout(120_000);
    await page.goto('/showcase#playground');
    await page.getByRole('button', { name: /Запустить demo/i }).click();
    await expect(page.locator('#playgroundTimeline')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole('link', { name: /Скачать brief/i })).toBeVisible({ timeout: 90_000 });
  });
});

async function loginAsAdmin(page: import('@playwright/test').Page) {
  await page.goto('/login?dev=1');
  const userInput = page.locator('#username, input[type="text"]').first();
  await userInput.fill('admin');
  const passInput = page.locator('#password, input[type="password"]').first();
  await passInput.fill('admin');
  await page.getByRole('button', { name: /войти|login|sign in/i }).click();
  await page.waitForURL(/\/app/, { timeout: 15_000 });
}

test.describe('Authenticated SPA UX', () => {
  test('app showcase has playground demo button', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/app/showcase');
    await expect(page.getByRole('button', { name: /Запустить demo/i })).toBeVisible({ timeout: 10_000 });
    await expect(page.locator('#playground')).toBeVisible();
  });

  test('settings billing shows coming soon badge', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/app/settings?tab=billing');
    await expect(page.locator('body')).toContainText(/Скоро|Stripe/i);
  });
});

async function loginAsAdmin(page: import('@playwright/test').Page) {
  await page.goto('/login?dev=1');
  const userInput = page.locator('#username, input[type="text"]').first();
  await userInput.fill('admin');
  const passInput = page.locator('#password, input[type="password"]').first();
  await passInput.fill('admin');
  await page.getByRole('button', { name: /войти|login|sign in/i }).click();
  await page.waitForURL(/\/app/, { timeout: 15_000 });
}

test.describe('Authenticated SPA UX', () => {
  test('app showcase has playground demo button', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/app/showcase');
    await expect(page.getByRole('button', { name: /Запустить demo/i })).toBeVisible({ timeout: 10_000 });
    await expect(page.locator('#playground')).toBeVisible();
  });

  test('settings billing shows coming soon badge', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/app/settings?tab=billing');
    await expect(page.locator('body')).toContainText(/Скоро|Stripe/i);
  });
});
