import { describe, it } from 'vitest';
import { getByText, render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { ConfigurationsTable } from '.';

const tableData = {
  columns: ['Reportable condition', 'Status'],
  data: [
    {
      name: 'Chlamydia trachomatis infection',
      status: 'on',
      id: 'asdf-zxcv-qwer-hjkl',
    },
    {
      name: 'Disease caused by Enterovirus',
      status: 'off',
      id: 'asdf-zxcv-qwer-hjkl',
    },
  ],
};

const renderComponentView = () =>
  render(
    <BrowserRouter>
      <ConfigurationsTable columns={tableData.columns} data={tableData.data} />
    </BrowserRouter>
  );

describe('Configurations Table component', () => {
  it('should render a table when supplied with data', async () => {
    renderComponentView();

    const table = screen.getByTestId('table');
    const firstRow = getByText(table, tableData.data[0].name).parentElement;
    const secondRow = getByText(table, tableData.data[1].name).parentElement;

    expect(table).toBeInTheDocument();
    expect(firstRow).toHaveTextContent(tableData.data[0].name);
    expect(firstRow).toHaveTextContent(`Refiner ${tableData.data[0].status}`);
    expect(secondRow).toHaveTextContent(tableData.data[1].name);
    expect(secondRow).toHaveTextContent(`Refiner ${tableData.data[1].status}`);
  });
});
