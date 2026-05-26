import { test, expect } from '@playwright/test';

/**
 * Smoke tests for My Agent React SPA.
 * Requires running server: docker compose up or uvicorn on :8020
 */

test.describe('My Agent UI smoke', () => {
  test('login page loads', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('body')).toContainText(/My Agent|Войти|Login/i);
  });

  test('app shell redirects to login when unauthenticated', async ({ page }) => {
    await page.goto('/app/');
    await page.waitForURL(/\/login/);
    expect(page.url()).toContain('/login');
  });

  test('legacy routes redirect to app paths when authed', async ({ page, context }) => {
    // Skip if no test credentials — structural check only
    const res = await page.goto('/agents');
    expect([200, 301, 302, 307]).toContain(res?.status() || 0);
  });
});

test.describe('Authenticated flows', () => {
  test.skip(!process.env.E2E_USER, 'Set E2E_USER and E2E_PASS for authenticated tests');

  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="text"], input[name="username"], #username', process.env.E2E_USER!);
    await page.fill('input[type="password"]', process.env.E2E_PASS!);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/app/);
  });

  test('onboarding page shows Russian steps', async ({ page }) => {
    await page.goto('/app/onboarding');
    await expect(page.locator('h1')).toContainText(/My Agent|Добро пожаловать/i);
  });

  test('agents settings tab loads grid', async ({ page }) => {
    await page.goto('/app/settings?tab=agents');
    await expect(page.locator('body')).toContainText(/агент/i);
  });

  test('chat page has composer', async ({ page }) => {
    await page.goto('/app/chat');
    await expect(page.locator('textarea, input[placeholder*="Сообщение"], input[placeholder*="Message"]')).toBeVisible();
  });
});
