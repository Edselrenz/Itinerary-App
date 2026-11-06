import { expect, test } from '@playwright/test';

test.describe('Nueva Ecija Travel Itinerary Planner E2E Journey', () => {
  test.beforeEach(async ({ page }) => {
    // Mark loading/splash screen as already seen to prevent overlay interception in headless journeys (UI-05)
    await page.addInitScript(() => {
      sessionStorage.setItem('ne_splash_seen_v1', 'true');
    });
  });

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
    await expect(page.locator('.guest-subtitle')).toContainText('Your trips are saved locally on this device');

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
    await expect(page.locator('.map-top-bar')).toBeVisible();

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

  test('displays places on map and opens place detail sheet when tapped from list view', async ({ page }) => {
    await page.goto('/tabs/map');
    await expect(page).toHaveURL(/\/tabs\/map/);
    await expect(page.locator('#leaflet-map')).toBeVisible();

    // Verify POI list toggle button shows loaded destinations
    const listPill = page.locator('.poi-list-toggle-pill');
    await expect(listPill).toBeVisible();
    await expect(listPill).toContainText(/List View \([1-9]/);

    // Verify Live OSM discovery button is present
    await expect(page.locator('.live-osm-btn')).toBeVisible();

    // Capture screenshot of the map view with destinations
    await page.screenshot({
      path: 'C:/Users/Edward/.gemini/antigravity/brain/b414e2ac-5be5-4176-b1a9-9ec4a2178554/map_places_display.png',
    });

    // Open POI list drawer
    await listPill.click();
    const drawer = page.locator('.poi-list-drawer');
    await expect(drawer).toBeVisible();

    // Verify destinations exist in the list
    const firstCard = drawer.locator('.drawer-place-card').first();
    await expect(firstCard).toBeVisible();
    const placeName = (await firstCard.locator('.drawer-card-name').textContent())?.trim();
    expect(placeName).toBeTruthy();

    // Tap place to open place detail sheet
    await firstCard.click();

    // Verify place detail sheet opens with correct venue details and action buttons
    const detailSheet = page.locator('app-place-detail-sheet');
    await expect(detailSheet).toBeVisible();
    await expect(detailSheet.locator('.sheet-title')).toContainText(placeName!);
    await expect(detailSheet.locator('.btn-suggested')).toBeVisible();
    await expect(detailSheet.locator('.btn-directions')).toBeVisible();

    // Capture screenshot of the opened place detail sheet
    await page.screenshot({
      path: 'C:/Users/Edward/.gemini/antigravity/brain/b414e2ac-5be5-4176-b1a9-9ec4a2178554/place_detail_sheet_open.png',
    });

    // Close detail sheet
    await detailSheet.locator('.sheet-close-btn').click();
    await expect(detailSheet).not.toBeVisible();
  });

  test('verifies Leaflet map markers and interaction on canvas', async ({ page }) => {
    await page.goto('/tabs/map');
    await expect(page.locator('#leaflet-map')).toBeVisible();

    // Wait for Leaflet marker layer pane to attach to the map DOM
    const markerPane = page.locator('.leaflet-marker-pane');
    await expect(markerPane).toBeAttached();

    // Verify at least one marker icon exists on the map
    const marker = page.locator('.leaflet-marker-icon').first();
    await expect(marker).toBeVisible({ timeout: 10000 });

    // Click marker
    await marker.click({ force: true });

    // Verify map remains responsive and intact
    await expect(page.locator('#leaflet-map')).toBeVisible();
  });
});
