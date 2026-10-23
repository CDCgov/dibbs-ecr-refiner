import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { ConfigurationsTable } from '.';
import userEvent from '@testing-library/user-event';
import { ConfigurationStatus } from '../../api/schemas';

const tableData = {
  data: [
    {
      id: 'chlamydia-config-id',
      display_name: 'Chlamydia trachomatis infection',
      status: ConfigurationStatus.active,
    },
    {
      id: 'asdf-zxcv-qwer-hjkl',
      display_name: 'Disease caused by Enterovirus',
      status: ConfigurationStatus.inactive,
    },
    {
      id: '1234-5678-9101-1121',
      display_name: 'Acanthamoeba',
      status: ConfigurationStatus.draft,
    },
  ],
};

describe('Configurations Table component', () => {
  it('should render a link to the config builder page for each row', () => {
    render(
      <MemoryRouter>
        <ConfigurationsTable data={tableData.data} />
      </MemoryRouter>
    );

    expect(
      screen.getByRole('link', {
        name: /configure chlamydia trachomatis infection/i,
      })
    ).toHaveAttribute(
      'href',
      '/configurations/chlamydia-config-id/customize-sections'
    );

    expect(
      screen.getByRole('link', {
        name: /configure disease caused by enterovirus/i,
      })
    ).toHaveAttribute(
      'href',
      '/configurations/asdf-zxcv-qwer-hjkl/customize-sections'
    );

    expect(
      screen.getByRole('link', { name: /configure acanthamoeba/i })
    ).toHaveAttribute(
      'href',
      '/configurations/1234-5678-9101-1121/customize-sections'
    );
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

  it('should focus the row link and activate it with keyboard', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ConfigurationsTable data={tableData.data} />
      </MemoryRouter>
    );

    const link = screen.getByRole('link', {
      name: /configure chlamydia trachomatis infection/i,
    });

    link.focus();
    expect(link).toHaveFocus();

    await user.keyboard('{Enter}');
    expect(link).toHaveAttribute(
      'href',
      '/configurations/chlamydia-config-id/customize-sections'
    );
  });
});
