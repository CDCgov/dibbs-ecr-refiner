// @vitest-environment jsdom
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import EicrSectionReview from './EicrSectionReview';

describe('EicrSectionReview', () => {
  it('renders the heading and placeholder', () => {
    const mockSectionProcessing = [
      { name: 'Section 1', code: '001', action: 'refine' },
      { name: 'Section 2', code: '002', action: 'include' },
      { name: 'Section 3', code: '003', action: 'remove' },
    ];
    render(<EicrSectionReview sectionProcessing={mockSectionProcessing} />);
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
    const mockSectionProcessing = [
      { name: 'Section 1', code: '001', action: 'refine' },
      { name: 'Section 2', code: '002', action: 'include' },
      { name: 'Section 3', code: '003', action: 'remove' },
    ];
    render(<EicrSectionReview sectionProcessing={mockSectionProcessing} />);
    const section = screen.getByLabelText(
      /Choose what you'd like to do with the sections in your eICR/i
    );
    expect(section).toBeInTheDocument();
  });
});
