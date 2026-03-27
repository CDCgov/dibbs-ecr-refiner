import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { TestQueryClientProvider } from '../../../test-utils';
import { EicrSectionReview } from './EicrSectionReview';
import { DbConfigurationSectionProcessing } from '../../../api/schemas/dbConfigurationSectionProcessing';

function renderWithClient(ui: React.ReactElement) {
  return render(<TestQueryClientProvider>{ui}</TestQueryClientProvider>);
}

describe('EicrSectionReview', () => {
  it('should display sections based on stored section data', () => {
    const testId = 'test-id';
    const sections: DbConfigurationSectionProcessing[] = [
      {
        name: 'History section',
        action: 'refine',
        include: true,
        code: 'hist',
        narrative: false,
        versions: ['1.1', '3.1'],
      },
      {
        name: 'Med section',
        action: 'refine',
        include: false,
        code: 'med',
        narrative: false,
        versions: ['1.1', '3.1', '3.1.1'],
      },
      {
        name: 'Immunizations section',
        action: 'retain',
        include: true,
        code: 'imm',
        narrative: false,
        versions: ['3.1', '3.1.1'],
      },
      {
        name: 'Narrative section',
        action: 'retain',
        include: true,
        code: 'nar',
        narrative: true,
        versions: ['3.1'],
      },
    ];
    renderWithClient(
      <EicrSectionReview
        configurationId={testId}
        disabled={false}
        sectionProcessing={sections}
      />
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

    // Narrative
    expect(narrative.checkbox).toBeChecked();
    expect(narrative.nameCell).toHaveTextContent('Narrative section');
    expect(narrative.switches).toHaveLength(2);
    expect(narrative.switches[0]).not.toBeChecked();
    expect(narrative.switches[1]).toBeChecked();
  });
});
