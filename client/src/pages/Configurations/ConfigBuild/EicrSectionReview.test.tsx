// @vitest-environment jsdom
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import EicrSectionReview from './EicrSectionReview';

describe('EicrSectionReview', () => {
  it('renders the heading and placeholder', () => {
    render(<EicrSectionReview />);
    // Check heading
    expect(
      screen.getByRole('heading', {
        name: /Choose what you'd like to do with the sections in your eICR/,
      })
    ).toBeInTheDocument();
    // Check options are there
    expect(screen.getByText(/include & refine section:/i)).toBeInTheDocument();
    expect(screen.getByText(/include entire section:/i)).toBeInTheDocument();
    expect(screen.getByText(/remove section:/i)).toBeInTheDocument();
  });

  it('has accessible section landmark', () => {
    render(<EicrSectionReview />);
    const section = screen.getByLabelText(
      /Choose what you'd like to do with the sections in your eICR/i
    );
    expect(section).toBeInTheDocument();
  });
});
