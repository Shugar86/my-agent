import { test, expect } from '@playwright/test';

/**
 * Investor funnel smoke tests — React landing, public demo, showcase.
 * Requires running server on :8020 with seeded templates for live demo run.
 */

test.describe('Investor funnel', () => {
  test('landing is outcome-focused, not dev docs', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText(/90 секунд/i);
    await expect(page.locator('body')).toContainText(/50\+/);
    await expect(page.locator('body')).not.toContainText(/376 тестов/i);
    await expect(page.locator('body')).not.toContainText(/Dual Provider/i);
    await expect(page.getByRole('link', { name: /Попробовать live/i }).first()).toHaveAttribute('href', '/demo');
  });

  test('pricing section exists on landing', async ({ page }) => {
    await page.goto('/#pricing');
    await expect(page.locator('#pricing')).toBeVisible();
    await expect(page.locator('body')).toContainText(/Starter/i);
    await expect(page.locator('body')).toContainText(/Enterprise/i);
  });

  test('public demo page loads', async ({ page }) => {
    await page.goto('/demo');
    await expect(page.locator('h1')).toContainText(/Live demo|Competitor Intelligence/i);
    await expect(page.getByRole('button', { name: /Запустить demo/i })).toBeVisible();
  });

  test('login has no dev credentials by default', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('body')).not.toContainText(/admin \/ admin/i);
    await expect(page.getByRole('link', { name: /Попробовать без регистрации/i })).toHaveAttribute('href', '/demo');
  });

  test('landing hero has product screenshot', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.landing-device-frame img')).toHaveAttribute('src', /product-dashboard/);
  });

  test('login uses external CSS', async ({ page }) => {
    await page.goto('/login');
    const styles = await page.locator('link[rel="stylesheet"]').all();
    const hrefs = await Promise.all(styles.map((l) => l.getAttribute('href')));
    expect(hrefs.some((h) => h?.includes('login.css'))).toBeTruthy();
    await expect(page.locator('style')).toHaveCount(0);
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
    await expect(page.getByRole('button', { name: /Запустить demo/i })).toBeVisible();
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
    await page.getByRole('button', { name: /Запустить demo/i }).click();
    await expect(page.locator('.demo-stepper, .playground-demo')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole('link', { name: /DOCX|brief|скачать/i })).toBeVisible({ timeout: 90_000 });
  });
});

test.describe('Showcase demo-MVP', () => {
  test('showcase page renders hero and case cards', async ({ page }) => {
    await page.goto('/showcase');
    await expect(page.locator('h1')).toContainText(/Кейсы|production/i);
    await expect(page.locator('.landing-card')).toHaveCount(7, { timeout: 10_000 });
  });

  test('persona toggle expands on first card', async ({ page }) => {
    await page.goto('/showcase');
    const firstCard = page.locator('.landing-card').first();
    await firstCard.getByRole('button').click();
    await expect(firstCard).toContainText(/./);
  });

  test('showcase lead CTA links to onboarding', async ({ page }) => {
    await page.goto('/showcase#cta');
    await expect(page.getByRole('link', { name: /Получить AI-оператора/i })).toHaveAttribute('href', /login\?next=/);
  });
});

test.describe('Showcase playground run', () => {
  test.skip(!process.env.E2E_DEMO_RUN, 'Set E2E_DEMO_RUN=1 to test live mock demo completion');

  test('playground preset completes with DOCX link', async ({ page }) => {
    test.setTimeout(120_000);
    await page.goto('/showcase#playground');
    await page.getByRole('button', { name: /Запустить demo/i }).click();
    await expect(page.locator('.demo-stepper')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole('link', { name: /DOCX|brief|скачать/i })).toBeVisible({ timeout: 90_000 });
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

  test('app demo route in sidebar flow', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/app/demo');
    await expect(page.getByRole('button', { name: /Запустить demo/i })).toBeVisible();
  });

  test('settings billing shows coming soon badge', async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto('/app/settings?tab=billing');
    await expect(page.locator('body')).toContainText(/Скоро|Stripe/i);
  });
});
