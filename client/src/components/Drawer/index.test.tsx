import { describe, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Drawer } from '.';
import userEvent from '@testing-library/user-event';
import { ClassAttributes, InputHTMLAttributes } from 'react';
import { JSX } from 'react/jsx-runtime';

// Mocking dependencies
vi.mock('@trussworks/react-uswds', () => ({
  Icon: { Close: () => <div>X</div> },
  InputGroup: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  InputPrefix: ({ children }: { children: React.ReactNode }) => (
    <span>{children}</span>
  ),
  TextInput: (
    props: JSX.IntrinsicAttributes &
      ClassAttributes<HTMLInputElement> &
      InputHTMLAttributes<HTMLInputElement>
  ) => <input {...props} />,
}));
vi.mock('focus-trap-react', () => ({
  default: ({ children }: any) => <div>{children}</div>,
}));

// Initial setup
describe('Drawer Component', () => {
  it('should render correctly', () => {
    const { container } = render(
      <Drawer
        title="Test Drawer"
        searchPlaceholder="Search here..."
        isOpen={true}
        onClose={vi.fn()}
      >
        <div>Drawer Content</div>
      </Drawer>
    );

    expect(container).toBeInTheDocument();
    expect(screen.getByText('Test Drawer')).toBeInTheDocument();
    expect(screen.getByText('Drawer Content')).toBeInTheDocument();
  });

  it('should close the drawer when the close button is clicked', async () => {
    const user = userEvent.setup();
    const onCloseMock = vi.fn();
    render(
      <Drawer
        title="Test Drawer"
        searchPlaceholder="Search here..."
        isOpen={true}
        onClose={onCloseMock}
      >
        <div>Drawer Content</div>
      </Drawer>
    );

    await user.click(screen.getByRole('button', { name: 'Close drawer' }));
    expect(onCloseMock).toHaveBeenCalled();
  });

  it('should filter content based on search input', async () => {
    const user = userEvent.setup();
    const onSearchMock = vi.fn();
    render(
      <Drawer
        title="Test Drawer"
        searchPlaceholder="Search here..."
        isOpen={true}
        onClose={vi.fn()}
        onSearch={onSearchMock}
      >
        <div>Drawer Content</div>
      </Drawer>
    );

    const searchInput = screen.getByPlaceholderText('Search here...');
    await user.type(searchInput, 'test query');
    expect(onSearchMock).toHaveBeenCalledWith('test query');
  });

  it('should call onSearch callback correctly when invoked', async () => {
    const onSearchMock = vi.fn();
    const user = userEvent.setup();
    render(
      <Drawer
        title="Test Drawer"
        searchPlaceholder="Search here..."
        isOpen={true}
        onClose={vi.fn()}
        onSearch={onSearchMock}
      >
        <div>Drawer Content</div>
      </Drawer>
    );

    const searchInput = screen.getByPlaceholderText('Search here...');
    await user.type(searchInput, 'search term');
    expect(onSearchMock).toHaveBeenCalledWith('search term');
  });
});
