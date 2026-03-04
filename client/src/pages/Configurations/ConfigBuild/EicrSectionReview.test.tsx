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
    // const user = userEvent.setup();
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
        name: 'Immuizations section',
        action: 'retain',
        include: true,
        code: 'imm',
        narrative: false,
        versions: ['3.1', '3.1.1'],
      },
    ];
    renderWithClient(
      <EicrSectionReview
        configurationId={testId}
        disabled={false}
        sectionProcessing={sections}
      />
    );

    const rows = screen.getAllByRole('row');

    expect(rows).toHaveLength(4); // including header

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
    expect(thirdRowCells[1]).toHaveTextContent('Immuizations section');
    expect(within(thirdRow).getByRole('switch')).not.toBeChecked();
  });
});
