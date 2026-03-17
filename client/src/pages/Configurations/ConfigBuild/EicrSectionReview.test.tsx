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
        name: 'Immuizations section',
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

    const rows = screen.getAllByRole('row');

    expect(rows).toHaveLength(5);

    const firstRow = rows[1];
    const firstRowCells = within(firstRow).getAllByRole('cell');

    const secondRow = rows[2];
    const secondRowCells = within(secondRow).getAllByRole('cell');

    const thirdRow = rows[3];
    const thirdRowCells = within(thirdRow).getAllByRole('cell');

    const fourthRow = rows[4];
    const fourthRowCells = within(fourthRow).getAllByRole('cell');

    expect(within(firstRow).getByRole('checkbox')).toBeChecked();
    expect(firstRowCells[1]).toHaveTextContent('History section');
    const firstRowSwitches = within(firstRow).getAllByRole('switch');
    expect(firstRowSwitches).toHaveLength(2);
    expect(firstRowSwitches[0]).toBeChecked();
    expect(firstRowSwitches[1]).not.toBeChecked();

    expect(within(secondRow).getByRole('checkbox')).not.toBeChecked();
    expect(secondRowCells[1]).toHaveTextContent('Med section');
    expect(within(secondRow).queryByRole('switch')).not.toBeInTheDocument();

    expect(within(thirdRow).getByRole('checkbox')).toBeChecked();
    expect(thirdRowCells[1]).toHaveTextContent('Immuizations section');
    const thirdRowSwitches = within(thirdRow).getAllByRole('switch');
    expect(thirdRowSwitches).toHaveLength(2);
    expect(thirdRowSwitches[0]).not.toBeChecked();
    expect(thirdRowSwitches[1]).not.toBeChecked();

    expect(within(fourthRow).getByRole('checkbox')).toBeChecked();
    expect(fourthRowCells[1]).toHaveTextContent('Narrative section');
    const fourthRowSwitches = within(fourthRow).getAllByRole('switch');
    expect(fourthRowSwitches).toHaveLength(2);
    expect(fourthRowSwitches[0]).not.toBeChecked();
    expect(fourthRowSwitches[1]).toBeChecked();
  });
});
