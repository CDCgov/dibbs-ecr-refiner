import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AddConditionCodeSetsDrawer } from './AddConditionCodeSetsDrawer';
import userEvent from '@testing-library/user-event';

vi.mock('./ConditionCodeSet', () => ({
  ConditionCodeSet: ({
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

vi.mock('../../../../hooks/useToast', () => ({
  useToast: () => vi.fn(),
}));

vi.mock('@tanstack/react-query', () => ({
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
  }),
}));

vi.mock('../../../../api/configurations/configurations', () => ({
  useAssociateConditionWithConfiguration: () => ({ mutate: vi.fn() }),
  useDisassociateConditionWithConfiguration: () => ({ mutate: vi.fn() }),
  getGetConfigurationQueryKey: vi.fn(),
}));

vi.mock('../../../../api/conditions/conditions', () => ({
  getGetConditionsByConfigurationQueryKey: vi.fn(),
}));

const mockConditions = [
  { id: '1', display_name: 'Asthma', associated: false },
  { id: '2', display_name: 'Diabetes', associated: true },
  { id: '3', display_name: 'Flu', associated: false },
].map((c) => ({
  ...c,
  canonical_url: '',
  version: '',
  reportable_condition_display_name: '',
}));

describe('AddConditionCodeSetsDrawer', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    configurationId: 'my-config',
    conditions: mockConditions,
    reportable_condition_display_name: 'COVID-19',
    disabled: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders drawer and condition names', () => {
    render(<AddConditionCodeSetsDrawer {...defaultProps} />);
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent(
      /Add condition code sets/
    );
    mockConditions.forEach(({ display_name }) => {
      expect(screen.getByText(display_name)).toBeInTheDocument();
    });
  });

  it('triggers onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    render(<AddConditionCodeSetsDrawer {...defaultProps} />);
    await user.click(screen.getByRole('button', { name: /close drawer/i }));
    expect(defaultProps.onClose).toHaveBeenCalledOnce();
  });

  it('filters conditions when searching', async () => {
    const user = userEvent.setup();
    render(<AddConditionCodeSetsDrawer {...defaultProps} />);
    await user.type(screen.getByRole('searchbox'), 'Flu');
    expect(screen.getByText('Flu')).toBeInTheDocument();
    expect(screen.queryByText('Asthma')).not.toBeInTheDocument();
    expect(screen.queryByText('Diabetes')).not.toBeInTheDocument();
  });

  it('returns only the expected condition matches when using the search box', async () => {
    const user = userEvent.setup();
    render(<AddConditionCodeSetsDrawer {...defaultProps} />);
    await user.type(screen.getByRole('searchbox'), 'Asthma');
    expect(screen.getByText('Asthma')).toBeInTheDocument();
    expect(screen.queryByText('Diabetes')).not.toBeInTheDocument();
  });
});
