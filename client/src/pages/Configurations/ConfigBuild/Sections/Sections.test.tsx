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

const sectionsWithDisabled: DbConfigurationSectionProcessing[] = [
  ...sections,
  {
    name: 'Disabled section',
    action: 'retain',
    include: true,
    code: '83910-0',
    narrative: true,
    versions: ['3.1'],
    section_type: 'standard',
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

    const rows = screen.getAllByRole('row');
    expect(rows).toHaveLength(5);

    const getRow = (index: number) => {
      const row = rows[index];
      return {
        checkbox: within(row).getByRole('checkbox'),
        nameCell: within(row).getAllByRole('cell')[1],
        codedDataSwitch: within(row).queryByRole('switch'),
        narrativeSelect: within(row).queryByRole('combobox'),
      };
    };

    const history = getRow(1);
    const med = getRow(2);
    const imm = getRow(3);
    const custom = getRow(4);

    expect(history.checkbox).toBeChecked();
    expect(history.nameCell).toHaveTextContent('History section');
    expect(history.codedDataSwitch).toBeInTheDocument();
    expect(history.codedDataSwitch).toBeChecked();
    expect(history.narrativeSelect).toBeInTheDocument();
    expect(history.narrativeSelect).toHaveValue('remove');

    expect(med.checkbox).not.toBeChecked();
    expect(med.nameCell).toHaveTextContent('Med section');
    expect(med.codedDataSwitch).not.toBeInTheDocument();
    expect(med.narrativeSelect).not.toBeInTheDocument();

    expect(imm.checkbox).toBeChecked();
    expect(imm.nameCell).toHaveTextContent('Immunizations section');
    expect(imm.codedDataSwitch).toBeInTheDocument();
    expect(imm.codedDataSwitch).not.toBeChecked();
    expect(imm.narrativeSelect).toBeInTheDocument();
    expect(imm.narrativeSelect).toHaveValue('remove');

    expect(custom.checkbox).toBeChecked();
    expect(custom.nameCell).toHaveTextContent(
      'Mock custom sectionCustommock-custom-sectionEdit|Delete'
    );
    expect(custom.codedDataSwitch).toBeInTheDocument();
    expect(custom.codedDataSwitch).toBeChecked();
    expect(custom.narrativeSelect).toBeInTheDocument();
    expect(custom.narrativeSelect).toHaveValue('retain');
  });

  it('should render narrative dropdown with correct options', () => {
    renderWithClient(
      <Sections configurationId={testId} disabled={false} sections={sections} />
    );

    const selects = screen.getAllByRole('combobox');
    expect(selects.length).toBeGreaterThanOrEqual(1);

    const firstSelect = selects[0];
    const options = within(firstSelect).getAllByRole('option');
    expect(options).toHaveLength(2);
    expect(options[0]).toHaveTextContent('Keep original');
    expect(options[0]).toHaveValue('retain');
    expect(options[1]).toHaveTextContent('Remove');
    expect(options[1]).toHaveValue('remove');
  });

  it('should blank out narrative controls for excluded rows', () => {
    renderWithClient(
      <Sections configurationId={testId} disabled={false} sections={sections} />
    );

    const rows = screen.getAllByRole('row');
    const medRow = rows[2];

    expect(within(medRow).queryByRole('switch')).not.toBeInTheDocument();
    expect(within(medRow).queryByRole('combobox')).not.toBeInTheDocument();
  });

  it('should disable narrative dropdown for disabled section LOINC codes', () => {
    renderWithClient(
      <Sections
        configurationId={testId}
        disabled={false}
        sections={sectionsWithDisabled}
      />
    );

    const disabledSectionName = screen.getByText('Disabled section');
    const row = disabledSectionName.closest('tr');
    expect(row).not.toBeNull();
    const select = row && within(row).queryByRole('combobox');
    expect(select).toBeInTheDocument();
    expect(select).toBeDisabled();
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
