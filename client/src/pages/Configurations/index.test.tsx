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
  it.skip('should contain a table with certain columns', async () => {
    assert.fail('NOT IMPLEMENTED');
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
      screen.getByPlaceholderText('Search configurations')
    ).toBeInTheDocument();
  });
});
