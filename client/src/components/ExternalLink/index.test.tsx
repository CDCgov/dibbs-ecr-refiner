import { render } from '@testing-library/react';
import { ExternalLink } from '.';

describe('ExternalLink', () => {
  it('should display the icon by default', () => {
    const { container } = render(
      <ExternalLink href="http://test.com">Test link</ExternalLink>
    );
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('should not display the icon when intentionally excluded', () => {
    const { container } = render(
      <ExternalLink href="http://test.com" includeIcon={false}>
        Test link
      </ExternalLink>
    );
    expect(container.querySelector('svg')).not.toBeInTheDocument();
  });
});
