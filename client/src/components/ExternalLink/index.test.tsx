import { render, screen, within } from '@testing-library/react';
import { ExternalLink } from '.';

describe('ExternalLink', () => {
  it('should display the icon by default', () => {
    render(<ExternalLink href="http://test.com">Test link</ExternalLink>);
    const link = screen.getByRole('link', { name: /test link/i });
    expect(within(link).getByRole('img', { hidden: true })).toBeInTheDocument();
  });

  it('should not display the icon when intentionally excluded', () => {
    render(
      <ExternalLink href="http://test.com" includeIcon={false}>
        Test link
      </ExternalLink>
    );
    const link = screen.getByRole('link', { name: /test link/i });
    expect(
      within(link).queryByRole('img', { hidden: true })
    ).not.toBeInTheDocument();
  });
});
