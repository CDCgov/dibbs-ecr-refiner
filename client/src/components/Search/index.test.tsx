import { describe, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { Search } from '.';

const renderComponentView = (text?: string) =>
  render(
    <BrowserRouter>
      <Search placeholder={text} id='test' name='test' />
    </BrowserRouter>
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
