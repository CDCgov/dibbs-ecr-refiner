import { Label, Select } from '@trussworks/react-uswds';
import { useGetEvents } from '../../api/events/events';
import { Spinner } from '../../components/Spinner';
import { Title } from '../../components/Title';
import ErrorFallback from '../ErrorFallback';
import { useState } from 'react';
import { ActivityLogEntries } from './ActivityLogEntries';
import { useGetConfigurations } from '../../api/configurations/configurations';

export function ActivityLog() {
  const [conditionFilter, setConditionFilter] = useState<string>(
    ALL_CONDITIONS_LITERAL
  );

  const {
    data: eventResponse,
    isPending: isEventsPending,
    isError: isEventsError,
    error: eventsError,
  } = useGetEvents({
    condition_filter:
      conditionFilter === ALL_CONDITIONS_LITERAL ? undefined : conditionFilter,
  });

  const {
    data: configurationsResponse,
    isPending: isConfigurationsPending,
    isError: isConfigurationsError,
    error: configurationsError,
  } = useGetConfigurations();

  if (isEventsPending || isConfigurationsPending) {
    return <Spinner variant="centered" />;
  }
  if (isEventsError || isConfigurationsError) {
    return (
      <ErrorFallback error={eventsError ? eventsError : configurationsError} />
    );
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
            {configurationsResponse.data.map((c) => {
              return (
                <option value={c.id} key={c.id}>
                  {c.name}
                </option>
              );
            })}
          </Select>
        </div>
      </div>

      <div className="mt-6">
        <ActivityLogEntries filteredLogEntries={eventResponse.data} />
      </div>
    </section>
  );
}

const ALL_CONDITIONS_LITERAL = 'All conditions';
