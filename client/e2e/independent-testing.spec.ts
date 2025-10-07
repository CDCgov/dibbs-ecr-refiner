import { test, expect, Page } from '@playwright/test';
import { login, logout } from './utils';
import path from 'path';
import fs from 'fs';

test.describe.serial('should be able to access independent testing', () => {
  let page: Page;

  // Login once before all tests
  test.beforeAll(async ({ browser }) => {
    const context = await browser.newContext();
    page = await context.newPage();
    await login(page);
  });

  // Logout once after all tests
  test.afterAll(async () => {
    await logout(page);
    await page.close();
  });

  test('should be able to see the click on testing tab', async () => {
    /// ==========================================================================
    /// Test that testing tab can be accessed
    /// ==========================================================================
    await page.getByRole('link', { name: 'Testing' }).click();
    await expect(
      page.getByText('Want to refine your own eCR file?')
    ).toBeVisible();
  });

  test('should be able to upload a file, refine, and download results', async () => {
    /// ==========================================================================
    /// Test independent test flow: upload, refine, download
    /// ==========================================================================
    await page.getByRole('link', { name: 'Testing' }).click();

    // Locate the file input by its id
    const fileInput = page.locator('input#zip-upload');

    // Resolve the file path relative to the project root
    const filePath = path.resolve(
      process.cwd(),
      'e2e/assets/mon-mothma-one-condition.zip'
    );

    // Upload the file directly
    await fileInput.setInputFiles(filePath);

    // Optionally, assert the file name shows up in the UI
    await expect(page.getByText('mon-mothma-one-condition.zip')).toBeVisible();

    // Click the "Upload .zip file" button
    const uploadButton = page.locator('button[data-testid="button"]', {
      hasText: 'Upload .zip file',
    });
    await uploadButton.click();

    // Assert the reportable conditions text is visible
    // Use regex to ignore line breaks and spacing issues
    await expect(
      page.getByText(
        /We found the following reportable condition\(s\) in the RR:/
      )
    ).toBeVisible();
    await expect(
      page.getByText(
        /Disease caused by severe acute respiratory syndrome coronavirus 2 \(disorder\)/
      )
    ).toBeVisible();

    // Click "Refine eCR" button
    const refineButton = page.locator('button[data-testid="button"]', {
      hasText: 'Refine eCR',
    });
    await refineButton.click();

    await expect(page.getByText('eCR refinement results')).toBeVisible();
    await expect(page.getByText('eICR file size reduced by')).toBeVisible();
    await expect(page.getByText('Original eICR')).toBeVisible();
    await expect(page.getByText('Refined eICR')).toBeVisible();

    // --- Click "Download results" and verify file download ---
    const [download] = await Promise.all([
      page.waitForEvent('download'), // wait for download to start
      page.locator('button', { hasText: 'Download results' }).click(),
    ]);

    // Save the downloaded file to a temporary path
    const downloadPath = path.resolve(
      process.cwd(),
      'e2e/downloads/results.zip'
    );
    await download.saveAs(downloadPath);

    // Assert that the file exists
    expect(fs.existsSync(downloadPath)).toBeTruthy();
  });

  test('should be able to refine with the test file', async () => {
    /// ==========================================================================
    /// Test independent flow with test file
    /// ==========================================================================
    await page.getByRole('link', { name: 'Testing' }).click();

    // Click the "Use test file" button
    const useTestFileButton = page.getByRole('button', {
      name: 'Use test file',
    });
    await expect(useTestFileButton).toBeVisible();
    await useTestFileButton.click();

    // Verify the expected reportable conditions are visible
    await expect(
      page.getByText(
        'We found the following reportable condition(s) in the RR:',
        { exact: false }
      )
    ).toBeVisible();

    await expect(
      page.getByText(
        'Disease caused by severe acute respiratory syndrome coronavirus 2 (disorder)',
        { exact: false }
      )
    ).toBeVisible();

    await expect(
      page.getByText(
        'Influenza caused by Influenza A virus subtype H5N1 (disorder)',
        { exact: false }
      )
    ).toBeVisible();

    // Click the "Refine eCR" button
    const refineButton = page.getByRole('button', { name: 'Refine eCR' });
    await expect(refineButton).toBeVisible();
    await refineButton.click();

    await expect(page.getByText('eCR refinement results')).toBeVisible();
    await expect(page.getByText('eICR file size reduced by')).toBeVisible();
    await expect(page.getByText('Original eICR')).toBeVisible();
    await expect(page.getByText('Refined eICR')).toBeVisible();
  });
});
