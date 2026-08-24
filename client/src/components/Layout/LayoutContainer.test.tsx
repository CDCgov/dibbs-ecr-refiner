import { render, screen } from '@testing-library/react';
import { LayoutContainer, LAYOUT_MAX_WIDTH } from './LayoutContainer';
import { describe, it, expect } from 'vitest';

describe('LayoutContainer', () => {
  it('renders children correctly', () => {
    render(
      <LayoutContainer>
        <div data-testid="child">Child Content</div>
      </LayoutContainer>
    );
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('applies default maxWidth and padding', () => {
    render(
      <LayoutContainer>
        <div data-testid="child">Child Content</div>
      </LayoutContainer>
    );
    const container = screen.getByTestId('child').parentElement;
    expect(container?.className).toContain(LAYOUT_MAX_WIDTH);
    expect(container?.className).toContain('px-8');
    expect(container?.className).toContain('lg:px-20');
  });

  it('applies custom maxWidth and padding', () => {
    render(
      <LayoutContainer maxWidth="max-w-7xl" padding="p-4">
        <div data-testid="child">Child Content</div>
      </LayoutContainer>
    );
    const container = screen.getByTestId('child').parentElement;
    expect(container?.className).toContain('max-w-7xl');
    expect(container?.className).toContain('p-4');
    expect(container?.className).not.toContain('px-8');
  });

  it('applies background class', () => {
    render(
      <LayoutContainer background="bg-red-500">
        <div data-testid="child">Child Content</div>
      </LayoutContainer>
    );
    const container = screen.getByTestId('child').parentElement;
    expect(container?.className).toContain('bg-red-500');
  });

  it('handles breakout mode for full-width backgrounds', () => {
    render(
      <LayoutContainer background="bg-blue-500" breakout>
        <div data-testid="child">Child Content</div>
      </LayoutContainer>
    );
    const innerContainer = screen.getByTestId('child').parentElement;
    const outerContainer = innerContainer?.parentElement;

    expect(outerContainer?.className).toContain('banner-breakout');
    expect(outerContainer?.className).toContain('bg-blue-500');
    expect(innerContainer?.className).toContain('mx-auto');
  });

  it('handles breakout mode correctly', () => {
    render(
      <LayoutContainer background="bg-green-500" breakout>
        <div data-testid="child">Child Content</div>
      </LayoutContainer>
    );
    const innerContainer = screen.getByTestId('child').parentElement;
    const outerContainer = innerContainer?.parentElement;

    expect(outerContainer?.className).toContain('banner-breakout');
    expect(outerContainer?.className).toContain('bg-green-500');
    expect(innerContainer?.className).toContain('mx-auto');
  });

  it('applies custom className', () => {
    render(
      <LayoutContainer className="custom-class">
        <div data-testid="child">Child Content</div>
      </LayoutContainer>
    );
    const container = screen.getByTestId('child').parentElement;
    expect(container?.className).toContain('custom-class');
  });
});
