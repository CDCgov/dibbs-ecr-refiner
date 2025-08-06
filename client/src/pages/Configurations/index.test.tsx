import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { Configurations } from '.';
import { TestQueryClientProvider } from '../../test-utils';
import userEvent from '@testing-library/user-event';
import { ToastContainer } from 'react-toastify';

// Mock configurations request
vi.mock('../../api/configurations/configurations', async () => {
  const actual = await vi.importActual(
    '../../api/configurations/configurations'
  );
  return {
    ...actual,
    useGetConfigurations: vi.fn(() => ({
      data: { data: [{ id: '1', display_name: 'test' }] },
      isLoading: false,
      error: null,
    })),
  };
});

const renderPageView = () =>
  render(
    <TestQueryClientProvider>
      <ToastContainer />
      <BrowserRouter>
        <Configurations />
      </BrowserRouter>
    </TestQueryClientProvider>
  );

describe('Configurations', () => {
  it('should contain a table with certain columns', async () => {
    renderPageView();

    expect(await screen.findByRole('table')).toBeInTheDocument();
  });
  it('should contain a call-to-action button', async () => {
    renderPageView();
    expect(
      screen.getByText('Set up new condition', {
        selector: 'button.usa-button[type=button]',
      })
    ).toBeInTheDocument();
  });
  it('should have a search component with correct placeholder', async () => {
    renderPageView();
    expect(
      await screen.findByPlaceholderText('Search configurations')
    ).toBeInTheDocument();
  });

  it('should render an error and success toast when the "Set up new configuration" button is clicked', async () => {
    const user = userEvent.setup();
    renderPageView();
    await user.click(screen.getByText('Set up new condition'));
    expect(
      await screen.findAllByText('New configuration created')
    ).toHaveLength(2);
  });
});
