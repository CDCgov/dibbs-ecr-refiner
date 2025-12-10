import { test, expect } from './fixtures/fixtures';
import { createNewConfiguration } from './utils';

test.describe
  .serial('Activation for new draft configurations works as expected', () => {
  test.describe.configure({ retries: 1 });

  test('activations flow shows the correct options with different versions', async ({
    page,
    makeAxeBuilder,
  }) => {
    await expect(makeAxeBuilder).toHaveNoAxeViolations();
    await createNewConfiguration('Hepatitis A Virus infection', page);

    // activate the newly created config
    await expect(page.getByText('Build configuration')).toBeVisible();
    await page.getByRole('link', { name: 'Activate' }).click();

    await expect(
      page.getByRole('heading', { name: 'Turn on configuration' })
    ).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    const turnOnButton = page.getByRole('button', {
      name: 'Turn on configuration',
    });

    await expect(turnOnButton).toBeVisible();
    await turnOnButton.click();

    const turnOnModalConfirmationButton = page.getByRole('button', {
      name: 'Turn on configuration',
    });

    await expect(turnOnModalConfirmationButton).toBeVisible();
    await turnOnModalConfirmationButton.click();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await expect(page.getByText('Status: Version 1 active')).toBeVisible();

    // check turn off flow works correctly
    const turnOffCurrentVersionButton = page.getByRole('button', {
      name: 'Turn off current version',
    });

    await turnOffCurrentVersionButton.click();
    const turnOffModalConfirmation = page.getByRole('button', {
      name: 'Yes, turn off',
    });
    await expect(turnOffModalConfirmation).toBeVisible();

    await turnOffModalConfirmation.click();
    await expect(page.getByText('Status: Inactive')).toBeVisible();

    await turnOnButton.click();
    await turnOnModalConfirmationButton.click();

    // draft a new version and verify the UI changes correctly
    await page.getByRole('link', { name: 'Build' }).click();
    const newDraftButton = page.getByRole('button', {
      name: 'Draft a new version',
    });
    await expect(newDraftButton).toBeVisible();
    await expect(makeAxeBuilder).toHaveNoAxeViolations();

    await newDraftButton.click();

    await page
      .getByRole('button', {
        name: 'Yes, draft a new version',
      })
      .click();

    await expect(
      page.getByRole('heading', { name: 'New draft created' })
    ).toBeVisible();

    await page.getByRole('link', { name: 'Activate' }).click();

    const switchButton = page.getByRole('button', {
      name: 'Switch to Version 2',
    });
    const turnOffButton = page.getByRole('button', {
      name: 'Turn off configuration',
    });
    await expect(switchButton).toBeVisible();
    await expect(turnOffButton).toBeVisible();

    await switchButton.click();
    await page
      .getByRole('button', {
        name: 'Yes, switch to Version 2',
      })
      .click();

    await expect(page.getByText('Status: Version 2 active')).toBeVisible();

    await page
      .getByRole('button', {
        name: 'Turn off current version',
      })
      .click();
    await page
      .getByRole('button', {
        name: 'Yes, turn off',
      })
      .click();

    await expect(page.getByText('Status: Inactive')).toBeVisible();

    await expect(turnOnButton).toBeVisible();
  });
});
