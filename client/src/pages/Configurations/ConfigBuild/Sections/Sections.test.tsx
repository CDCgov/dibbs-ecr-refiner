import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { TestQueryClientProvider } from '../../../../test-utils';
import { Sections } from '.';
import { DbConfigurationSectionProcessing } from '../../../../api/schemas/dbConfigurationSectionProcessing';
import userEvent from '@testing-library/user-event';

const sections: DbConfigurationSectionProcessing[] = [
  {
    name: 'History section',
    action: 'refine',
    include: true,
    code: 'hist',
    narrative: false,
    versions: ['1.1', '3.1'],
    section_type: 'standard',
  },
  {
    name: 'Med section',
    action: 'refine',
    include: false,
    code: 'med',
    narrative: false,
    versions: ['1.1', '3.1', '3.1.1'],
    section_type: 'standard',
  },
  {
    name: 'Immunizations section',
    action: 'retain',
    include: true,
    code: 'imm',
    narrative: false,
    versions: ['3.1', '3.1.1'],
    section_type: 'standard',
  },
  {
    name: 'Mock custom section',
    action: 'refine',
    include: true,
    code: 'mock-custom-section',
    narrative: false,
    versions: [],
    section_type: 'custom',
  },
];

const testId = 'test-id';

function renderWithClient(ui: React.ReactElement) {
  return render(<TestQueryClientProvider>{ui}</TestQueryClientProvider>);
}

describe('Configuration sections', () => {
  it('should display sections based on stored section data', () => {
    const testId = 'test-id';

    renderWithClient(
      <Sections configurationId={testId} disabled={false} sections={sections} />
    );

    const rows = screen.getAllByRole('row');

    expect(rows).toHaveLength(sections.length + 1); // including header

    // get the table rows
    const firstRow = rows[1];
    const firstRowCells = within(firstRow).getAllByRole('cell');

    const secondRow = rows[2];
    const secondRowCells = within(secondRow).getAllByRole('cell');

    const thirdRow = rows[3];
    const thirdRowCells = within(thirdRow).getAllByRole('cell');

    // check the contents of each row
    expect(within(firstRow).getByRole('checkbox')).toBeChecked();
    expect(firstRowCells[1]).toHaveTextContent('History section');
    expect(within(firstRow).getByRole('switch')).toBeChecked();

    expect(within(secondRow).getByRole('checkbox')).not.toBeChecked();
    expect(secondRowCells[1]).toHaveTextContent('Med section');
    expect(within(secondRow).queryByRole('switch')).not.toBeInTheDocument();

    expect(within(thirdRow).getByRole('checkbox')).toBeChecked();
    expect(thirdRowCells[1]).toHaveTextContent('Immunizations section');
    expect(within(thirdRow).getByRole('switch')).not.toBeChecked();
  });

  it('should allow custom section additions', async () => {
    const user = userEvent.setup();

    renderWithClient(
      <Sections configurationId={testId} disabled={false} sections={sections} />
    );

    expect(screen.getByText('Add custom section')).toBeInTheDocument();
    await user.click(screen.getByText('Add custom section'));

    expect(
      screen.getByText('Add a custom section', { selector: 'h2' })
    ).toBeInTheDocument();
    await user.type(
      screen.getByLabelText('Display name (for this section)', { exact: true }),
      'sample name'
    );
    await user.type(
      screen.getByLabelText('LOINC code', { exact: true }),
      'sample code'
    );
    expect(
      screen.getByRole('button', { name: 'Add section' })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Close this window' })
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
  });

  it('should allow custom section edits', () => {
    renderWithClient(
      <Sections configurationId={testId} disabled={false} sections={sections} />
    );

    const cell = screen.getByText('Mock custom section');
    const row = cell.closest('tr');

    expect(row).not.toBeNull();

    if (!row) {
      throw new Error('Could not find table row for "Mock custom section"');
    }

    expect(
      within(row).getByRole('button', { name: /edit/i })
    ).toBeInTheDocument();
  });

  it('should allow custom section deletions', () => {
    renderWithClient(
      <Sections configurationId={testId} disabled={false} sections={sections} />
    );

    const cell = screen.getByText('Mock custom section');
    const row = cell.closest('tr');

    expect(row).not.toBeNull();

    if (!row) {
      throw new Error('Could not find table row for "Mock custom section"');
    }

    expect(
      within(row).getByRole('button', { name: /delete/i })
    ).toBeInTheDocument();
  });
});
