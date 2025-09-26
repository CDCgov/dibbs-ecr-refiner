import { getByText, render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { ConfigurationsTable } from '.';
import userEvent from '@testing-library/user-event';

const mockNavigate = vi.fn();

vi.mock('react-router', async () => {
  const actual =
    await vi.importActual<typeof import('react-router')>('react-router');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const testCfg = {
  data: [
    {
      name: 'Chlamydia trachomatis infection',
      is_active: true,
      id: 'chlamydia-config-id',
    },
    {
      name: 'Disease caused by Enterovirus',
      is_active: false,
      id: 'asdf-zxcv-qwer-hjkl',
    },
  ],
};

describe('Configurations Table component', () => {
  afterEach(() => {
    mockNavigate.mockClear();
  });

  it('should render a table when supplied with data', () => {
    render(
      <BrowserRouter>
        <ConfigurationsTable data={testCfg.data} />
      </BrowserRouter>
    );

    testCfg.data.forEach(({ name, is_active }) => {
      const row = getByText(screen.getByTestId('table'), name).parentElement;
      expect(row).toHaveTextContent(name);
      expect(row).toHaveTextContent(`${is_active ? 'Active' : 'Refiner off'}`);
    });
  });
  it('should render an error message if no data is supplied', () => {
    render(
      <BrowserRouter>
        <ConfigurationsTable data={[]} />
      </BrowserRouter>
    );

    expect(screen.getByText(/reportable condition/i)).toBeInTheDocument();
    expect(screen.getByText('No configurations available')).toBeInTheDocument();
  });

  it('should navigate to the config builder page when a table row is clicked', async () => {
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <ConfigurationsTable data={testCfg.data} />
      </BrowserRouter>
    );

    // This ensures the aria-label is correct
    const row = screen.getByRole('row', {
      name: 'View configuration for Chlamydia trachomatis infection',
    });

    await user.click(row);

    expect(mockNavigate).toHaveBeenCalledWith(
      '/configurations/chlamydia-config-id/build'
    );
  });

  it('should navigate to the config builder page when Enter or Space is pressed on a table row', async () => {
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <ConfigurationsTable data={testCfg.data} />
      </BrowserRouter>
    );

    const row = screen.getByRole('row', {
      name: 'View configuration for Chlamydia trachomatis infection',
    });

    row.focus();
    expect(row).toHaveFocus();

    // Pressing enter
    await user.keyboard('{Enter}');

    expect(mockNavigate).toHaveBeenCalledWith(
      '/configurations/chlamydia-config-id/build'
    );

    mockNavigate.mockClear();

    // Pressing space
    await user.keyboard(' ');

    expect(mockNavigate).toHaveBeenCalledWith(
      '/configurations/chlamydia-config-id/build'
    );
  });
});
