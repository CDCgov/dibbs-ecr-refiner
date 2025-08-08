import { describe, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { StatusPill } from '.';

const renderComponentView = (status: 'on' | 'off') =>
  render(
    <BrowserRouter>
      <StatusPill status={status} />
    </BrowserRouter>
  );

describe('Status pill component', () => {
  it('should render with status on', () => {
    renderComponentView('on');

    expect(screen.getByText('Refiner on')).toBeInTheDocument();
  });
  it('should render with status off', () => {
    renderComponentView('off');

    expect(screen.getByText('Refiner off')).toBeInTheDocument();
  });
});
