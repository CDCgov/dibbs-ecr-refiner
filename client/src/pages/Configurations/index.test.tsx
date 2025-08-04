import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { Configurations } from '.';
import { TestQueryClientProvider } from '../../test-utils';

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
});
