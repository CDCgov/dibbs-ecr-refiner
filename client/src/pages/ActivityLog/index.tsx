import { Label, Select } from '@trussworks/react-uswds';
import { Spinner } from '../../components/Spinner';
import { Title } from '../../components/Title';
import { ErrorFallback } from '../ErrorFallback';
import { useState } from 'react';
import { ActivityLogEntries } from './ActivityLogEntries';
import { useGetEvents } from '../../api/events/events';

export function ActivityLog() {
  const [conditionFilter, setConditionFilter] = useState<string>(
    ALL_CONDITIONS_LITERAL
  );

  const {
    data: eventResponse,
    isPending: isPending,
    isError: isError,
    error: error,
  } = useGetEvents({
    cannonical_url:
      conditionFilter === ALL_CONDITIONS_LITERAL ? undefined : conditionFilter,
  });

  if (isPending) {
    return <Spinner variant="centered" />;
  }
  if (isError) {
    return <ErrorFallback error={error} />;
  }

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
            onChange={(e) => setConditionFilter(e.target.value)}
          >
            <option value={ALL_CONDITIONS_LITERAL}>
              {ALL_CONDITIONS_LITERAL}
            </option>
            {eventResponse.data.configuration_options.map((c) => {
              return (
                <option value={c.cannonical_url} key={c.cannonical_url}>
                  {c.name}
                </option>
              );
            })}
          </Select>
        </div>
      </div>

      <div className="mt-6">
        <ActivityLogEntries
          filteredLogEntries={eventResponse.data.audit_events}
        />
      </div>
    </section>
  );
}

const ALL_CONDITIONS_LITERAL = 'All conditions';
