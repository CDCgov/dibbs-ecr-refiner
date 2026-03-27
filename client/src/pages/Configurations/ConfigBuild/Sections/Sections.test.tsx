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
    narrative: true,
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
    renderWithClient(
      <Sections configurationId={testId} disabled={false} sections={sections} />
    );

    // all table rows (including header)
    const rows = screen.getAllByRole('row');
    expect(rows).toHaveLength(5);

    const getRow = (index: number) => {
      const row = rows[index];
      return {
        checkbox: within(row).getByRole('checkbox'),
        nameCell: within(row).getAllByRole('cell')[1],
        switches: within(row).queryAllByRole('switch'), // [0] = data handling approach, [1] = narrative
      };
    };

    // skip header
    const history = getRow(1);
    const med = getRow(2);
    const imm = getRow(3);
    const narrative = getRow(4);

    // History
    expect(history.checkbox).toBeChecked();
    expect(history.nameCell).toHaveTextContent('History section');
    expect(history.switches).toHaveLength(2);
    expect(history.switches[0]).toBeChecked();
    expect(history.switches[1]).not.toBeChecked();

    // Med
    expect(med.checkbox).not.toBeChecked();
    expect(med.nameCell).toHaveTextContent('Med section');
    expect(med.switches).toHaveLength(0);

    // Immunizations
    expect(imm.checkbox).toBeChecked();
    expect(imm.nameCell).toHaveTextContent('Immunizations section');
    expect(imm.switches).toHaveLength(2);
    expect(imm.switches[0]).not.toBeChecked();
    expect(imm.switches[1]).not.toBeChecked();

    // Custom section
    expect(narrative.checkbox).toBeChecked();
    expect(narrative.nameCell).toHaveTextContent(
      'Mock custom sectionCustommock-custom-sectionEdit|Delete'
    );
    expect(narrative.switches).toHaveLength(2);
    expect(narrative.switches[0]).toBeChecked();
    expect(narrative.switches[1]).toBeChecked();
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
