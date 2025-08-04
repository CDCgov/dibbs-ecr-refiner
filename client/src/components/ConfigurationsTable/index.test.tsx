import { describe, it } from 'vitest';
import { getByText, render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { ConfigurationsTable } from '.';

enum ConfigurationStatus {
  on = 'on',
  off = 'off',
}

const testCfg = {
  columns: {
    name: 'Reportable condition',
    status: 'Status',
  },
  data: [
    {
      name: 'Chlamydia trachomatis infection',
      status: ConfigurationStatus.on,
      id: 'asdf-zxcv-qwer-hjkl',
    },
    {
      name: 'Disease caused by Enterovirus',
      status: ConfigurationStatus.off,
      id: 'asdf-zxcv-qwer-hjkl',
    },
  ],
};

describe('Configurations Table component', () => {
  it('should render a table when supplied with data', () => {
    render(
      <BrowserRouter>
        <ConfigurationsTable columns={testCfg.columns} data={testCfg.data} />
      </BrowserRouter>
    );

    testCfg.data.forEach(({ name, status }) => {
      const row = getByText(screen.getByTestId('table'), name).parentElement;
      expect(row).toHaveTextContent(name);
      expect(row).toHaveTextContent(`Refiner ${status}`);
    });
  });
  it('should render an error message if no data is supplied', () => {
    render(
      <BrowserRouter>
        <ConfigurationsTable columns={testCfg.columns} data={[]} />
      </BrowserRouter>
    );

    expect(screen.getByText('Reportable condition')).toBeInTheDocument();
    expect(screen.getByText('No configurations available')).toBeInTheDocument();
  });
});
