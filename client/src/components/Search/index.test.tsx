import { describe, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { Search } from '.';

const renderComponentView = (text?: string) =>
  render(
    <MemoryRouter>
      <Search placeholder={text} id="test" name="test" />
    </MemoryRouter>
  );

describe('Search component', () => {
  it('should have a default placeholder text', () => {
    renderComponentView();

    expect(screen.getByPlaceholderText('Search')).toBeInTheDocument();
  });
  it('should have a custom placeholder text', () => {
    renderComponentView('My custom placeholder text');

    expect(
      screen.getByPlaceholderText('My custom placeholder text')
    ).toBeInTheDocument();
  });
});
