import { expect, test } from '@playwright/test';

test.describe('Nueva Ecija Travel Itinerary Planner E2E Journey', () => {
  test('redirects root url to welcome page with brand elements', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/welcome/);

    // Hero branding and adventure copy
    await expect(page.locator('.brand-title')).toContainText('Trip mo, trip ko');
    await expect(page.locator('.hero-headline')).toContainText('Your next adventure');

    // Action buttons
    await expect(page.locator('.actions-group ion-button', { hasText: 'Log in' })).toBeVisible();
    await expect(page.locator('.actions-group ion-button', { hasText: 'Sign up' })).toBeVisible();
    await expect(page.locator('.guest-pill-btn')).toContainText('Continue as Guest');
  });

  test('completes guest authentication journey from welcome to home', async ({ page }) => {
    await page.goto('/welcome');

    // Click Continue as Guest on Welcome screen
    await page.locator('.guest-pill-btn').click();
    await expect(page).toHaveURL(/\/guest/);

    // Verify Guest explanation view
    await expect(page.locator('.guest-title')).toContainText('Explore as a guest');
    await expect(page.locator('.guest-subtitle')).toContainText("Your data won't be saved");

    // Click Continue as Guest button to enter main tabs
    await page.locator('.guest-content-section ion-button', { hasText: 'Continue as Guest' }).click();
    await expect(page).toHaveURL(/\/tabs\/home/);

    // Verify Home tab view
    await expect(page.locator('.header-title')).toContainText('Where are you');
    await expect(page.locator('.search-input')).toBeVisible();
  });

  test('navigates seamlessly between Home and Map tabs', async ({ page }) => {
    await page.goto('/tabs/home');

    // Verify Tab bar is present with navigation buttons
    const tabBar = page.locator('ion-tab-bar');
    await expect(tabBar).toBeVisible();

    // Navigate to Map tab
    await page.locator('ion-tab-button[tab="map"]').click();
    await expect(page).toHaveURL(/\/tabs\/map/);

    // Verify Map canvas and filter bar are loaded
    await expect(page.locator('#leaflet-map')).toBeVisible();
    await expect(page.locator('.map-filter-bar')).toBeVisible();

    // Navigate back to Home tab
    await page.locator('ion-tab-button[tab="home"]').click();
    await expect(page).toHaveURL(/\/tabs\/home/);
    await expect(page.locator('.header-title')).toContainText('Where are you');
  });

  test('navigates to Custom Itinerary Builder and verifies travel questionnaire', async ({ page }) => {
    await page.goto('/tabs/home');

    // Click Custom Itinerary action card
    const customCard = page.locator('.action-card.custom-card');
    await expect(customCard).toBeVisible();
    await customCard.click();

    // Verify Custom Builder view
    await expect(page).toHaveURL(/\/custom-builder/);
    await expect(page.locator('.main-heading')).toContainText('Tell us your travel details');

    // Verify questionnaire form inputs exist
    await expect(page.locator('.builder-toolbar .builder-title')).toContainText('Custom Itinerary');
  });

  test('allows direct deep-linking to core application routes', async ({ page }) => {
    // Direct link to Map
    await page.goto('/tabs/map');
    await expect(page).toHaveURL(/\/tabs\/map/);
    await expect(page.locator('#leaflet-map')).toBeVisible();

    // Direct link to Custom Builder
    await page.goto('/custom-builder');
    await expect(page).toHaveURL(/\/custom-builder/);
    await expect(page.locator('.main-heading')).toContainText('Tell us your travel details');
  });
});
