import { MemoryRouter, Routes, Route } from 'react-router';
import { ToastContainer } from 'react-toastify';
import { TestQueryClientProvider } from '../../test-utils';
import { ActivityLog } from '.';
import { render, screen } from '@testing-library/react';
import { EventResponse } from '../../api/schemas';
import userEvent from '@testing-library/user-event';

const configurationEvents: EventResponse[] = [
  {
    id: 'fa74c1b3-a4e3-42eb-a350-c606083b5c5f',
    username: 'refiner',
    configuration_name: 'Alpha-gal Syndrome',
    action_text: 'Created configuration',
    created_at: '2025-10-28T13:58:45.363325Z',
  },
  {
    id: '10e1286d-487e-4f81-bee4-4c6d4df9ed92',
    username: 'refiner',
    configuration_name: 'Acanthamoeba',
    action_text: 'Created configuration',
    created_at: '2025-10-28T13:57:55.627842Z',
  },
];

vi.mock('../../api/events/events', async () => {
  const actual = await vi.importActual('../../api/events/events');
  return {
    ...actual,
    useGetEvents: vi.fn(() => ({
      data: {
        data: configurationEvents,
      },
    })),
  };
});

function checkActivityLogAgainstMockEvents(conditionFilter?: string) {
  const eventsToCheck = conditionFilter
    ? configurationEvents.filter(
        (e) => e.configuration_name === conditionFilter
      )
    : configurationEvents;

  eventsToCheck.forEach((r) => {
    const matchingRow = screen
      .getByRole('cell', { name: r.configuration_name })
      .closest('tr');
    expect(matchingRow).toBeInTheDocument();
    expect(matchingRow).toHaveTextContent(r.action_text);
    expect(matchingRow).toHaveTextContent(r.username);
    expect(matchingRow).toHaveTextContent(
      new Date(r.created_at).toLocaleDateString()
    );
  });
}

const renderPageView = () =>
  render(
    <TestQueryClientProvider>
      <ToastContainer />
      <MemoryRouter initialEntries={['/activity']}>
        <Routes>
          <Route path="/activity" element={<ActivityLog />} />
        </Routes>
      </MemoryRouter>
    </TestQueryClientProvider>
  );

describe('Activity log page', () => {
  beforeEach(() => vi.resetAllMocks());

  it('should render the activity log with the test entries', () => {
    renderPageView();

    expect(screen.getByText('Activity log')).toBeInTheDocument();
    expect(
      screen.getByText(
        'Review activity in eCR Refiner from yourself and others on the team.'
      )
    ).toBeInTheDocument();

    checkActivityLogAgainstMockEvents();
  });
  it('should filter the activity log when conditions are changed', async () => {
    const user = userEvent.setup();

    renderPageView();

    expect(screen.getByText('Activity log')).toBeInTheDocument();
    expect(
      screen.getByText(
        'Review activity in eCR Refiner from yourself and others on the team.'
      )
    ).toBeInTheDocument();

    const logEntries = screen.getAllByRole('row', { name: 'Log entry' });
    expect(logEntries).toHaveLength(configurationEvents.length);

    const conditionFilter = screen.getByLabelText('Condition');
    const conditionFilterToTest = 'Alpha-gal Syndrome';

    expect(conditionFilter).toBeInTheDocument();

    // the test was hanging when using the .selectOptions API bc our dropdown
    // isn't a native select, so we're doing the option selection manually using
    // .click
    await user.click(conditionFilter);
    const option = await screen.findByRole('option', {
      name: conditionFilterToTest,
    });
    await user.click(option);

    checkActivityLogAgainstMockEvents(conditionFilterToTest);

    await user.click(conditionFilter);
    const resetOption = await screen.findByRole('option', {
      name: 'All conditions',
    });
    await user.click(resetOption);

    checkActivityLogAgainstMockEvents();
  });
});
