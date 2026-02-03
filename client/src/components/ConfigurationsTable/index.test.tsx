import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { ConfigurationsTable } from '.';
import userEvent from '@testing-library/user-event';
import { GetConfigurationsResponseStatus } from '../../api/schemas';

const mockNavigate = vi.fn();

vi.mock('react-router', async () => {
  const actual =
    await vi.importActual<typeof import('react-router')>('react-router');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const tableData = {
  data: [
    {
      id: 'chlamydia-config-id',
      name: 'Chlamydia trachomatis infection',
      status: GetConfigurationsResponseStatus.active,
    },
    {
      id: 'asdf-zxcv-qwer-hjkl',
      name: 'Disease caused by Enterovirus',
      status: GetConfigurationsResponseStatus.inactive,
    },
    {
      id: '1234-5678-9101-1121',
      name: 'Acanthamoeba',
      status: GetConfigurationsResponseStatus.draft,
    },
  ],
};

describe('Configurations Table component', () => {
  afterEach(() => {
    mockNavigate.mockClear();
  });

  it('should render a table when supplied with data', () => {
    render(
      <MemoryRouter>
        <ConfigurationsTable data={tableData.data} />
      </MemoryRouter>
    );

    expect(
      screen.getByRole('row', {
        name: /active configuration for chlamydia trachomatis infection/i,
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('row', {
        name: /inactive configuration for disease caused by enterovirus/i,
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('row', {
        name: /inactive configuration for acanthamoeba/i,
      })
    ).toBeInTheDocument();
  });

  it('should render an error message if no data is supplied', () => {
    render(
      <MemoryRouter>
        <ConfigurationsTable data={[]} />
      </MemoryRouter>
    );

    expect(screen.getByText(/reportable condition/i)).toBeInTheDocument();
    expect(screen.getByText('No configurations available')).toBeInTheDocument();
  });

  it('should navigate to the config builder page when a table row is clicked', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ConfigurationsTable data={tableData.data} />
      </MemoryRouter>
    );

    // This ensures the aria-label is correct
    const rowButton = within(
      screen.getByRole('row', {
        name: 'View active configuration for Chlamydia trachomatis infection',
      })
    ).getAllByRole('button', {
      name: 'Configure the configuration for Chlamydia trachomatis infection',
    })[0];

    await user.click(rowButton);

    expect(mockNavigate).toHaveBeenCalledWith(
      '/configurations/chlamydia-config-id/build'
    );
  });

  it('should navigate to the config builder page when Enter or Space is pressed on a table row', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ConfigurationsTable data={tableData.data} />
      </MemoryRouter>
    );

    const rowButton = within(
      screen.getByRole('row', {
        name: 'View active configuration for Chlamydia trachomatis infection',
      })
    ).getAllByRole('button', {
      name: 'Configure the configuration for Chlamydia trachomatis infection',
    })[0];

    rowButton.focus();
    expect(rowButton).toHaveFocus();

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
