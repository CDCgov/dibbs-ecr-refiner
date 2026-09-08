import { describe, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Drawer } from './Drawer';
import userEvent from '@testing-library/user-event';
import { TestProviders } from '../../../../test-utils';

function renderDrawer(props?: Partial<React.ComponentProps<typeof Drawer>>) {
  const defaultProps = {
    title: 'Test Drawer',
    searchPlaceholder: 'Search here...',
    isOpen: true,
    onClose: vi.fn(),
    onSearch: vi.fn(),
    children: <div>Drawer Content</div>,
  };

  return render(
    <TestProviders>
      <Drawer {...defaultProps} {...props} />
    </TestProviders>
  );
}

describe('Drawer Component', () => {
  it('should render correctly', () => {
    const { container } = renderDrawer();

    expect(container).toBeInTheDocument();
    expect(screen.getByText('Test Drawer')).toBeInTheDocument();
    expect(screen.getByText('Drawer Content')).toBeInTheDocument();
  });

  it('should close the drawer when the close button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderDrawer({ onClose });

    await user.click(screen.getByRole('button', { name: 'Close drawer' }));
    expect(onClose).toHaveBeenCalled();
  });

  it('should filter content based on search input', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn();
    renderDrawer({ onSearch });

    const searchInput = screen.getByPlaceholderText('Search here...');
    await user.type(searchInput, 'test query');
    expect(onSearch).toHaveBeenCalledWith('test query');
  });

  it('should call onSearch callback correctly when invoked', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn();
    renderDrawer({ onSearch });

    const searchInput = screen.getByPlaceholderText('Search here...');
    await user.type(searchInput, 'search term');
    expect(onSearch).toHaveBeenCalledWith('search term');
  });
});
