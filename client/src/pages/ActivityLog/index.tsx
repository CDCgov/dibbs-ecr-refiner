import { Label, Select } from '@trussworks/react-uswds';
import { Pagination } from '../../components/Pagination';
import { Spinner } from '../../components/Spinner';
import { Title } from '../../components/Title';
import { useState } from 'react';
import { ActivityLogEntries } from './ActivityLogEntries';
import { useGetEvents } from '../../api/events/events';

export function ActivityLog() {
  const ALL_CONDITIONS_LITERAL = 'All conditions';

  const [selectedPage, setSelectedPage] = useState(1);
  const [conditionFilter, setConditionFilter] = useState<string>(
    ALL_CONDITIONS_LITERAL
  );
  const {
    data: eventResponse,
    isPending,
    isError,
  } = useGetEvents({
    canonical_url:
      conditionFilter === ALL_CONDITIONS_LITERAL ? undefined : conditionFilter,
    page: selectedPage,
  });

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error!';

  const { total_pages, configuration_options } = eventResponse.data;

  return (
    <section className="mx-auto p-4">
      <div className="mt-10">
        <Title>Activity log</Title>
        <p className="mt-2">
          Review activity in eCR Refiner from yourself and others on the team.
        </p>
        <div className="mt-6">
          <Label htmlFor="condition-filter">Condition</Label>
          <Select
            id="condition-filter"
            name="condition-filter"
            value={conditionFilter}
            onChange={(e) => {
              setSelectedPage(1);
              setConditionFilter(e.target.value);
            }}
          >
            <option value={ALL_CONDITIONS_LITERAL}>
              {ALL_CONDITIONS_LITERAL}
            </option>
            {configuration_options.map(({ canonical_url, name }) => {
              return (
                <option value={canonical_url} key={canonical_url}>
                  {name}
                </option>
              );
            })}
          </Select>
        </div>
      </div>
      <div className="mt-6 flex flex-col">
        <ActivityLogEntries
          filteredLogEntries={eventResponse.data.audit_events}
        />
        <Pagination
          currentPage={selectedPage}
          totalPages={total_pages}
          maxSlots={6}
          onClickNext={() => setSelectedPage((p) => p + 1)}
          onClickPrevious={() => setSelectedPage((p) => p - 1)}
          onClickPageNumber={(_, page) => setSelectedPage(page)}
        />
      </div>
    </section>
  );
}
