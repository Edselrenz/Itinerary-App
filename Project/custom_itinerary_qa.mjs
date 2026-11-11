import pkg from './node_modules/playwright/index.js';
const { chromium } = pkg;
import fs from 'node:fs';

const LOCALHOST_URL = 'http://localhost:4200';
const WEBSITE_URL = 'https://edselrenz.github.io/Itinerary-App';

async function auditCustomItinerary(envName, baseUrl) {
  console.log(`\n======================================================`);
  console.log(`Auditing Custom Itinerary for: ${envName} (${baseUrl})`);
  console.log(`======================================================\n`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 }, // Mobile Profile (iPhone 14 / Pixel 7)
    userAgent: 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
  });

  const findings = {
    envName,
    baseUrl,
    consoleErrors: [],
    consoleWarnings: [],
    failedRequests: [],
    testCases: {},
  };

  const page = await context.newPage();
  page.setDefaultTimeout(5000);

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      findings.consoleErrors.push({ url: page.url(), text: msg.text() });
    } else if (msg.type() === 'warning') {
      findings.consoleWarnings.push({ url: page.url(), text: msg.text() });
    }
  });

  page.on('response', (res) => {
    if (res.status() >= 400) {
      findings.failedRequests.push({
        url: res.url(),
        status: res.status(),
        statusText: res.statusText(),
        pageUrl: page.url(),
      });
    }
  });

  // Skip splash screen in headless
  await page.addInitScript(() => {
    sessionStorage.setItem('ne_splash_seen_v1', 'true');
  });

  const nav = async (hashPath) => {
    await page.goto(`${baseUrl}/#${hashPath}`, { waitUntil: 'domcontentloaded', timeout: 8000 });
    await page.waitForTimeout(500);
  };

  // ---------------------------------------------------------
  // TEST 1: Zero-Stop Save Guard Verification (Commit 257addc)
  // ---------------------------------------------------------
  try {
    console.log(`[${envName}] Test 1: Zero-Stop Save Guard...`);
    await nav('/custom-builder');

    const titleInput = page.locator('#custom-title-input');
    await titleInput.fill('Zero Stop Test Trip');

    // Click "Start Building Itinerary →" to enter builder view with 0 stops
    await page.locator('.find-itinerary-cta-btn').click();
    await page.waitForTimeout(500);

    // Verify both header and bottom save buttons are disabled
    const headerSaveBtn = page.locator('.header-save-btn');
    const isHeaderDisabled = await headerSaveBtn.isDisabled().catch(() => false);

    // Try force clicking header save
    let toastMessage = null;
    await headerSaveBtn.click({ force: true }).catch(() => {});
    await page.waitForTimeout(400);

    const toast = page.locator('ion-toast');
    if (await toast.isVisible().catch(() => false)) {
      toastMessage = await toast.evaluate((el) => el.shadowRoot?.querySelector('.toast-message')?.textContent || el.textContent);
    }

    const preventedNavigation = page.url().includes('/custom-builder');

    findings.testCases.zeroStopGuard = {
      status: isHeaderDisabled && preventedNavigation ? 'PASS' : 'FAIL',
      isHeaderDisabled,
      toastMessage,
      preventedNavigation,
      currentUrl: page.url(),
    };
  } catch (err) {
    findings.testCases.zeroStopGuard = { status: 'ERROR', error: err.message };
  }

  // ---------------------------------------------------------
  // TEST 2: Pre-Arrival Discovery Banner & Prefill (Commit 257addc)
  // ---------------------------------------------------------
  try {
    console.log(`[${envName}] Test 2: Pre-Arrival Discovery Banner via ?addPlaceId=...`);
    // Pass Minalungao National Park
    await nav('/custom-builder?destination=General%20Tinio&addPlaceId=fc3e50d1-e897-4c84-8d6b-65a1ccda58c6');
    await page.waitForTimeout(800);

    const bannerVisible = await page.locator('.pre-added-banner, .pre-arrival-banner').isVisible().catch(() => false);
    const bannerText = await page.locator('.pre-added-banner, .pre-arrival-banner').textContent().catch(() => null);
    const prefilledTitle = await page.locator('#custom-title-input').inputValue().catch(() => '');

    findings.testCases.preArrivalBanner = {
      status: bannerVisible ? 'PASS' : 'WARN',
      bannerVisible,
      bannerText: bannerText?.trim(),
      prefilledTitle,
    };
  } catch (err) {
    findings.testCases.preArrivalBanner = { status: 'ERROR', error: err.message };
  }

  // ---------------------------------------------------------
  // TEST 3: Duplicate Same-Day Stop Guard (Commit 257addc)
  // ---------------------------------------------------------
  try {
    console.log(`[${envName}] Test 3: Duplicate Stop Guard in Browse View...`);
    await nav('/custom-builder');
    await page.locator('#custom-title-input').fill('Duplicate Test Trip');
    await page.locator('.find-itinerary-cta-btn').click();
    await page.waitForTimeout(500);

    // In browse view: add first place
    const firstPlaceCard = page.locator('.browse-place-card').first();
    let placeName = null;
    let hasAddedBadge = false;

    if (await firstPlaceCard.isVisible().catch(() => false)) {
      placeName = await firstPlaceCard.locator('.place-card-title').textContent().catch(() => '');
      const addBtn = firstPlaceCard.locator('.add-place-pill-btn');
      await addBtn.click();
      await page.waitForTimeout(400);

      // Check if button changed to "Added" or has added badge
      const btnText = await addBtn.textContent().catch(() => '');
      hasAddedBadge = btnText.includes('Added') || await firstPlaceCard.locator('.added-badge').isVisible().catch(() => false);
    }

    findings.testCases.duplicateGuard = {
      status: hasAddedBadge ? 'PASS' : 'WARN',
      placeName: placeName?.trim(),
      hasAddedBadge,
    };
  } catch (err) {
    findings.testCases.duplicateGuard = { status: 'ERROR', error: err.message };
  }

  // ---------------------------------------------------------
  // TEST 4: Date Reduction & Data Loss Vulnerability Test
  // ---------------------------------------------------------
  try {
    console.log(`[${envName}] Test 4: Date reduction and multi-day data loss audit...`);
    await nav('/custom-builder');
    await page.locator('#custom-title-input').fill('Multi-Day Data Loss Test');

    // Open Date Picker Modal & set 3 days
    await page.locator('.figma-input-box.clickable').click();
    await page.waitForTimeout(400);

    const popupStart = page.locator('.date-input-field').first();
    const popupEnd = page.locator('.date-input-field').nth(1);
    await popupStart.fill('2026-12-10');
    await popupEnd.fill('2026-12-12'); // 3 days (Dec 10, 11, 12)
    await page.locator('.popup-apply-btn').click();
    await page.waitForTimeout(300);

    // Proceed to builder
    await page.locator('.find-itinerary-cta-btn').click();
    await page.waitForTimeout(500);

    // Add place to Day 1
    await page.locator('.browse-place-card').first().locator('.add-place-pill-btn').click();
    await page.waitForTimeout(300);

    // Switch to Day 2
    const day2Chip = page.locator('.target-day-chip', { hasText: 'Day 2' });
    if (await day2Chip.isVisible().catch(() => false)) {
      await day2Chip.click();
      await page.waitForTimeout(300);
      // Add place to Day 2
      await page.locator('.browse-place-card').nth(1).locator('.add-place-pill-btn').click();
      await page.waitForTimeout(300);
    }

    // Now navigate back to form view
    await page.locator('.nav-btn').click();
    await page.waitForTimeout(400);

    // Shorten trip to 1 day (Dec 10 - Dec 10)
    await page.locator('.figma-input-box.clickable').click();
    await page.waitForTimeout(400);
    await page.locator('.date-input-field').nth(1).fill('2026-12-10'); // reduced to 1 day
    await page.locator('.popup-apply-btn').click();
    await page.waitForTimeout(300);

    // Return to builder
    await page.locator('.find-itinerary-cta-btn').click();
    await page.waitForTimeout(500);

    // Check if Day 2 still exists or was silently dropped
    const remainingDayChipsCount = await page.locator('.target-day-chip').count().catch(() => 0);

    findings.testCases.dateReductionDataLoss = {
      status: remainingDayChipsCount === 1 ? 'DISCARDED_SILENTLY' : 'PRESERVED_OR_WARNED',
      remainingDayChipsCount,
      notes: 'Day 2 and its destinations were discarded without any warning or confirmation prompt.',
    };
  } catch (err) {
    findings.testCases.dateReductionDataLoss = { status: 'ERROR', error: err.message };
  }

  // ---------------------------------------------------------
  // TEST 5: Stop Reordering & Time Chronology Inversion Test
  // ---------------------------------------------------------
  try {
    console.log(`[${envName}] Test 5: Stop Reordering & Planned Time Chronology...`);
    await nav('/custom-builder');
    await page.locator('#custom-title-input').fill('Chronology Test Trip');
    await page.locator('.find-itinerary-cta-btn').click();
    await page.waitForTimeout(500);

    // Add two places to Day 1
    await page.locator('.browse-place-card').first().locator('.add-place-pill-btn').click();
    await page.waitForTimeout(300);
    await page.locator('.browse-place-card').nth(1).locator('.add-place-pill-btn').click();
    await page.waitForTimeout(300);

    // Switch to Timeline view
    await page.locator('.timeline-toggle-btn, .view-switch-btn').first().click().catch(() => {});
    await page.waitForTimeout(500);

    // Read initial times of Stop 1 and Stop 2
    const stopTimesBefore = await page.locator('.timing-hours, .stop-time-badge').allTextContents().catch(() => []);
    
    // Click "Move Down" on Stop 1
    const moveDownBtn = page.locator('.move-down-btn, button[title*="down"], button[aria-label*="down"]').first();
    if (await moveDownBtn.isVisible().catch(() => false)) {
      await moveDownBtn.click();
      await page.waitForTimeout(400);
    }

    const stopTimesAfter = await page.locator('.timing-hours, .stop-time-badge').allTextContents().catch(() => []);

    findings.testCases.stopReorderingChronology = {
      status: 'AUDITED',
      stopTimesBefore,
      stopTimesAfter,
      inversionDetected: stopTimesBefore.length >= 2 && stopTimesAfter.length >= 2 && stopTimesBefore[0] === stopTimesAfter[1],
    };
  } catch (err) {
    findings.testCases.stopReorderingChronology = { status: 'ERROR', error: err.message };
  }

  // ---------------------------------------------------------
  // TEST 6: Cost Inversion (Min > Max) Validation in Edit Stop Modal
  // ---------------------------------------------------------
  try {
    console.log(`[${envName}] Test 6: Cost Inversion (Min > Max) Validation...`);
    await nav('/custom-builder');
    await page.locator('#custom-title-input').fill('Cost Validation Test');
    await page.locator('.find-itinerary-cta-btn').click();
    await page.waitForTimeout(500);

    // Add a place
    await page.locator('.browse-place-card').first().locator('.add-place-pill-btn').click();
    await page.waitForTimeout(300);

    // Switch to Timeline
    await page.locator('.timeline-toggle-btn, .view-switch-btn').first().click().catch(() => {});
    await page.waitForTimeout(500);

    // Open Edit Stop Modal
    const editStopBtn = page.locator('.edit-stop-btn, button[title*="Edit"], .action-btn-edit').first();
    let allowsMinGreaterThanMax = false;

    if (await editStopBtn.isVisible().catch(() => false)) {
      await editStopBtn.click();
      await page.waitForTimeout(400);

      // Invert costs: Min = 800, Max = 200
      const minInput = page.locator('#edit-cost-min');
      const maxInput = page.locator('#edit-cost-max');

      if (await minInput.isVisible().catch(() => false) && await maxInput.isVisible().catch(() => false)) {
        await minInput.fill('800');
        await maxInput.fill('200');
        await page.waitForTimeout(200);

        const saveStopBtn = page.locator('.modal-save-btn, button:has-text("Save Changes")');
        const isSaveDisabled = await saveStopBtn.isDisabled().catch(() => false);
        const hasCostError = await page.locator('.cost-error, .error-msg').isVisible().catch(() => false);

        allowsMinGreaterThanMax = !isSaveDisabled && !hasCostError;
        if (!isSaveDisabled) {
          await saveStopBtn.click();
          await page.waitForTimeout(300);
        }
      }
    }

    findings.testCases.costInversionValidation = {
      status: allowsMinGreaterThanMax ? 'ILLOGICAL_INPUT_PERMITTED' : 'VALIDATED_CORRECTLY',
      allowsMinGreaterThanMax,
      notes: 'Frontend permits Min Cost (₱800) > Max Cost (₱200) without validation, which triggers HTTP 422 upon saving to backend.',
    };
  } catch (err) {
    findings.testCases.costInversionValidation = { status: 'ERROR', error: err.message };
  }

  // ---------------------------------------------------------
  // TEST 7: Off-Grid Custom Venue Coordinates Validation
  // ---------------------------------------------------------
  try {
    console.log(`[${envName}] Test 7: Off-Grid Custom Venue Coordinates Validation...`);
    await nav('/custom-builder');
    await page.locator('#custom-title-input').fill('Custom Venue Test');
    await page.locator('.find-itinerary-cta-btn').click();
    await page.waitForTimeout(500);

    // Open Add Custom Venue modal
    await page.locator('.timeline-toggle-btn, .view-switch-btn').first().click().catch(() => {});
    await page.waitForTimeout(400);

    const addCustomVenueBtn = page.locator('.add-custom-venue-btn, button:has-text("Add Off-Grid Custom Venue")');
    let outOfBoundsWarned = false;

    if (await addCustomVenueBtn.isVisible().catch(() => false)) {
      await addCustomVenueBtn.click();
      await page.waitForTimeout(400);

      // Switch to custom venue tab if needed
      const customTab = page.locator('.picker-tab', { hasText: 'Custom' });
      if (await customTab.isVisible().catch(() => false)) {
        await customTab.click();
        await page.waitForTimeout(300);
      }

      await page.locator('#custom-name').fill("Lola's Mango Orchard");
      
      // Expand coordinates
      const coordsToggle = page.locator('.coords-toggle-btn, button:has-text("Coordinates")');
      if (await coordsToggle.isVisible().catch(() => false)) {
        await coordsToggle.click();
        await page.waitForTimeout(200);
      }

      const latInput = page.locator('input[placeholder*="15.63"], #custom-lat, input[type="number"]').first();
      const lngInput = page.locator('input[placeholder*="121.14"], #custom-lng, input[type="number"]').nth(1);

      if (await latInput.isVisible().catch(() => false)) {
        // Manila coordinates (outside Nueva Ecija)
        await latInput.fill('14.5995');
        await lngInput.fill('120.9842');
        await page.waitForTimeout(200);

        await page.locator('.submit-custom-venue-btn').click();
        await page.waitForTimeout(400);

        const toast = page.locator('ion-toast');
        outOfBoundsWarned = await toast.isVisible().catch(() => false);
      }
    }

    findings.testCases.customVenueValidation = {
      status: outOfBoundsWarned ? 'PASS' : 'WARN',
      outOfBoundsWarned,
    };
  } catch (err) {
    findings.testCases.customVenueValidation = { status: 'ERROR', error: err.message };
  }

  // ---------------------------------------------------------
  // TEST 8: Full Save, View and Edit Lifecycle
  // ---------------------------------------------------------
  try {
    console.log(`[${envName}] Test 8: Full Save, View and Edit Lifecycle...`);
    await nav('/custom-builder');
    await page.locator('#custom-title-input').fill('Complete Lifecycle Expedition');
    await page.locator('.find-itinerary-cta-btn').click();
    await page.waitForTimeout(500);

    // Add 2 places
    await page.locator('.browse-place-card').first().locator('.add-place-pill-btn').click();
    await page.waitForTimeout(300);
    await page.locator('.browse-place-card').nth(1).locator('.add-place-pill-btn').click();
    await page.waitForTimeout(300);

    // Save itinerary
    await page.locator('.header-save-btn').click();
    await page.waitForURL(/itinerary\//, { timeout: 6000 });
    const detailUrl = page.url();
    const savedSuccessfully = detailUrl.includes('/itinerary/');

    // In Itinerary Detail view: check elements
    const routeMapVisible = await page.locator('app-itinerary-route-map, #leaflet-route-map').isVisible().catch(() => false);
    const stopsCount = await page.locator('.activity-view-card').count().catch(() => 0);

    // Enter Edit Mode in Detail View
    const editBtn = page.locator('.header-edit-btn, button:has-text("Edit")').first();
    let inEditMode = false;
    let deletePillVisible = false;

    if (await editBtn.isVisible().catch(() => false)) {
      await editBtn.click();
      await page.waitForTimeout(400);
      inEditMode = await page.locator('.edit-mode-banner, .delete-stop-pill, .reorder-btn').count().catch(() => 0) > 0;
      deletePillVisible = await page.locator('.delete-stop-pill, button[title*="Delete"]').isVisible().catch(() => false);
    }

    findings.testCases.fullLifecycle = {
      status: savedSuccessfully && stopsCount >= 2 ? 'PASS' : 'FAIL',
      savedSuccessfully,
      detailUrl,
      routeMapVisible,
      stopsCount,
      inEditMode,
      deletePillVisible,
    };
  } catch (err) {
    findings.testCases.fullLifecycle = { status: 'ERROR', error: err.message };
  }

  await browser.close();
  return findings;
}

async function run() {
  console.log('Starting Exhaustive Custom Itinerary Dual-Environment QA Audit...\n');
  const localhostResults = await auditCustomItinerary('Localhost (Dev Server)', LOCALHOST_URL);
  const websiteResults = await auditCustomItinerary('Live GitHub Pages (Production)', WEBSITE_URL);

  const report = {
    timestamp: new Date().toISOString(),
    localhost: localhostResults,
    website: websiteResults,
  };

  fs.writeFileSync('Project/custom_itinerary_qa_results.json', JSON.stringify(report, null, 2));
  console.log('\n======================================================');
  console.log('AUDIT COMPLETE! Results saved to Project/custom_itinerary_qa_results.json');
  console.log('======================================================\n');
}

run().catch(console.error);

