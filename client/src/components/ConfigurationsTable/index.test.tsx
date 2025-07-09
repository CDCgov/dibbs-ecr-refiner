import { describe, it } from 'vitest';
import { getByText, render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { ConfigurationsTable } from '.';

const testData = {
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
      <ConfigurationsTable columns={testData.columns} data={testData.data} />
    </BrowserRouter>
  );

describe('Configurations Table component', () => {
  it('should render a table when supplied with data', async () => {
    renderComponentView();

    testData.data.forEach(({ name, status }) => {
      let row = getByText(screen.getByTestId('table'), name).parentElement;
      expect(row).toHaveTextContent(name);
      expect(row).toHaveTextContent(`Refiner ${status}`);
    });
  });
});
