import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { Configurations } from '.';

const renderPageView = () =>
  render(
    <BrowserRouter>
      <Configurations />
    </BrowserRouter>
  );

describe('Configurations', () => {
  it('should contain a table with certain columns', () => {
    renderPageView();

    expect(screen.getByTestId('table')).toBeInTheDocument();
  });
  it('should contain a call-to-action button', () => {
    renderPageView();
    expect(
      screen.getByText('Set up new condition', {
        selector: 'button.usa-button[type=button]',
      })
    ).toBeInTheDocument();
  });
  it('should have a search component with correct placeholder', () => {
    renderPageView();
    expect(
      screen.getByPlaceholderText('Search configurations')
    ).toBeInTheDocument();
  });
});
