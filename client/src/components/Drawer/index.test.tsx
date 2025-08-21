import { describe, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Drawer from './index';

// Mocking dependencies
vi.mock('@trussworks/react-uswds', () => ({
  Icon: { Close: () => <div>X</div> },
}));
vi.mock('focus-trap-react', () => ({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  default: ({ children }: any) => <div>{children}</div>,
}));

// Initial setup
describe('Drawer Component', () => {
  it('should render correctly', () => {
    const { container } = render(
      <Drawer
        title="Test Drawer"
        placeHolder="Search here..."
        toRender={<div>Drawer Content</div>}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(container).toBeInTheDocument();
    expect(screen.getByText('Test Drawer')).toBeInTheDocument();
    expect(screen.getByText('Drawer Content')).toBeInTheDocument();
  });

  it('should close the drawer when the close button is clicked', () => {
    const onCloseMock = vi.fn();
    render(
      <Drawer
        title="Test Drawer"
        placeHolder="Search here..."
        toRender={<div>Drawer Content</div>}
        isOpen={true}
        onClose={onCloseMock}
      />
    );

    const closeButton = screen.getByTestId('close-drawer');
    fireEvent.click(closeButton);
    expect(onCloseMock).toHaveBeenCalled();
  });

  it('should respect drawerWidth prop for 35%', () => {
    const { container } = render(
      <Drawer
        title="Test Drawer"
        placeHolder="Search here..."
        toRender={<div>Drawer Content</div>}
        isOpen={true}
        onClose={vi.fn()}
        drawerWidth="35%"
      />
    );

    const drawer = container.querySelector('#drawer-container');
    expect(drawer).toHaveClass('w-[35%]');
  });

  it.skip('should filter content based on search input', () => {
    const onSearchMock = vi.fn();
    render(
      <Drawer
        title="Test Drawer"
        placeHolder="Search here..."
        toRender={<div>Drawer Content</div>}
        isOpen={true}
        onClose={vi.fn()}
        onSearch={onSearchMock}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search here...');
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    expect(onSearchMock).toHaveBeenCalledWith('test query');
  });

  it.skip('should call onSearch callback correctly when invoked', () => {
    const onSearchMock = vi.fn();
    render(
      <Drawer
        title="Test Drawer"
        placeHolder="Search here..."
        toRender={<div>Drawer Content</div>}
        isOpen={true}
        onClose={vi.fn()}
        onSearch={onSearchMock}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search here...');
    fireEvent.change(searchInput, { target: { value: 'search term' } });
    expect(onSearchMock).toHaveBeenCalledWith('search term');
  });
});
