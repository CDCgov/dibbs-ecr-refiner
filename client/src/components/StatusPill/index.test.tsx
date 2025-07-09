import { describe, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router';
import { StatusPill } from '.';

const renderComponentView = (status: string) =>
  render(
    <BrowserRouter>
      <StatusPill status={status} />
    </BrowserRouter>
  );

describe('Status pill component', () => {
  it('should render with status on', async () => {
    renderComponentView('on');

    expect(screen.getByTestId('status-pill')).toBeInTheDocument();
    expect(screen.getByTestId('status-pill')).toHaveAttribute(
      'data-configuration-status',
      'on'
    );
  });
  it('should render with status off', async () => {
    renderComponentView('off');

    expect(screen.getByTestId('status-pill')).toBeInTheDocument();
    expect(screen.getByTestId('status-pill')).toHaveAttribute(
      'data-configuration-status',
      'off'
    );
  });
});
