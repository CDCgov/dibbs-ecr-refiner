import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import AddConditionCodeSetsDrawer from './AddConditionCodeSets';
import userEvent from '@testing-library/user-event';

// Mocks for child components and hooks
vi.mock('../../../components/Drawer', () => ({
  default: ({
    children,
    title,
    onClose,
    onSearch,
  }: {
    children: React.ReactNode;
    title: string | React.ReactNode;
    onClose: () => void;
    onSearch: (filter: string) => void;
  }) => (
    <div>
      <div data-testid="drawer-title">{title}</div>
      <button data-testid="drawer-close" onClick={onClose}>
        Close
      </button>
      <input
        data-testid="search-input"
        onChange={(e) => onSearch(e.target.value)}
        aria-label="search"
      />
      {children}
    </div>
  ),
}));

vi.mock('./ConditionCodeSet', () => ({
  default: ({
    conditionName,
    onAssociate,
    onDisassociate,
    highlight,
  }: {
    conditionName: string;
    onAssociate: () => void;
    onDisassociate: () => void;
    highlight?: React.ReactNode;
  }) => (
    <div>
      <span>{conditionName}</span>
      <button data-testid={`associate-${conditionName}`} onClick={onAssociate}>
        Add
      </button>
      <button
        data-testid={`disassociate-${conditionName}`}
        onClick={onDisassociate}
      >
        Remove
      </button>
      {highlight && <span data-testid="highlight">highlighted</span>}
    </div>
  ),
}));

vi.mock('../../../hooks/useToast', () => ({
  useToast: () => vi.fn(),
}));

vi.mock('@tanstack/react-query', () => ({
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
  }),
}));

vi.mock('../../../api/configurations/configurations', () => ({
  useAssociateConditionWithConfiguration: () => ({ mutate: vi.fn() }),
  useDisassociateConditionWithConfiguration: () => ({ mutate: vi.fn() }),
  getGetConfigurationQueryKey: vi.fn(),
}));

vi.mock('../../../api/conditions/conditions', () => ({
  getGetConditionsByConfigurationQueryKey: vi.fn(),
}));

const mockConditions = [
  { id: '1', display_name: 'Asthma', associated: false },
  { id: '2', display_name: 'Diabetes', associated: true },
  { id: '3', display_name: 'Flu', associated: false },
];

describe('AddConditionCodeSetsDrawer', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    configurationId: 'my-config',
    conditions: mockConditions,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders drawer and condition names', () => {
    render(
      <AddConditionCodeSetsDrawer
        {...defaultProps}
        conditions={mockConditions.map((condition) => ({
          ...condition,
          canonical_url: '',
          version: '',
        }))}
      />
    );
    expect(screen.getByTestId('drawer-title').textContent).toMatch(
      /Add condition code sets/
    );
    mockConditions.forEach(({ display_name }) => {
      expect(screen.getByText(display_name)).toBeInTheDocument();
    });
  });

  it('triggers onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <AddConditionCodeSetsDrawer
        {...defaultProps}
        conditions={mockConditions.map((condition) => ({
          ...condition,
          canonical_url: '',
          version: '',
        }))}
      />
    );
    await user.click(screen.getByTestId('drawer-close'));
    expect(defaultProps.onClose).toHaveBeenCalledOnce();
  });

  it('filters conditions when searching', async () => {
    const user = userEvent.setup();
    render(
      <AddConditionCodeSetsDrawer
        {...defaultProps}
        conditions={mockConditions.map((condition) => ({
          ...condition,
          canonical_url: '',
          version: '',
        }))}
      />
    );
    const searchInput = screen.getByTestId('search-input');
    await user.type(searchInput, 'Flu');
    expect(screen.getByText('Flu')).toBeInTheDocument();
    expect(screen.queryByText('Asthma')).not.toBeInTheDocument();
    expect(screen.queryByText('Diabetes')).not.toBeInTheDocument();
  });

  it('shows highlight when search matches a condition', async () => {
    const user = userEvent.setup();
    render(
      <AddConditionCodeSetsDrawer
        {...defaultProps}
        conditions={mockConditions.map((condition) => ({
          ...condition,
          canonical_url: '',
          version: '',
        }))}
      />
    );
    const searchInput = screen.getByTestId('search-input');
    await user.type(searchInput, 'Asthma');
    expect(await screen.findByText('Asthma')).toBeInTheDocument();
  });

  it('calls onAssociate/onDisassociate for condition actions', async () => {
    const user = userEvent.setup();
    render(
      <AddConditionCodeSetsDrawer
        {...defaultProps}
        conditions={mockConditions.map((condition) => ({
          ...condition,
          canonical_url: '',
          version: '',
        }))}
      />
    );
    await user.click(await screen.findByText('Asthma'));
    await user.click(await screen.findByText('Diabetes'));
  });
});
