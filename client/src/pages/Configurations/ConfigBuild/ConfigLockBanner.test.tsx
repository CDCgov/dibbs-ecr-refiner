import { render, screen } from '@testing-library/react';
import { ConfigLockBanner } from './ConfigLockBanner';

describe('ConfigLockBanner', () => {
  it('shows banner with name/email', () => {
    render(<ConfigLockBanner lockedByName="foo" lockedByEmail="bar" />);
    expect(screen.getByText(/View only/)).toBeInTheDocument();
    expect(screen.getByText('foo')).toBeInTheDocument();
    expect(screen.getByText('bar')).toBeInTheDocument();
  });

  it('null if name/email missing', () => {
    const { container } = render(<ConfigLockBanner lockedByName={null} lockedByEmail="bar" />);
    expect(container).toBeEmptyDOMElement();
    render(<ConfigLockBanner lockedByName="foo" lockedByEmail={null} />);
    expect(screen.queryByText(/View only/)).toBeNull();
  });
});
