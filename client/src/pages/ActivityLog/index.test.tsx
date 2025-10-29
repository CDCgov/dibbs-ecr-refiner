import { MemoryRouter, Routes, Route } from 'react-router';
import { ToastContainer } from 'react-toastify';
import { TestQueryClientProvider } from '../../test-utils';
import { ActivityLog } from '.';
import { render, screen } from '@testing-library/react';

interface ActivityEntry {
  id: string;
  username: string;
  configuration_name: string;
  action_text: string;
  created_at: string;
}
const configurationEvents: ActivityEntry[] = [
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

    configurationEvents.forEach((r) => {
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
  });
});
