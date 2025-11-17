import { Label, Select } from '@trussworks/react-uswds';
import { useGetEvents } from '../../api/events/events';
import { Spinner } from '../../components/Spinner';
import { Title } from '../../components/Title';
import ErrorFallback from '../ErrorFallback';
import { useEffect, useState } from 'react';
import { EventResponse } from '../../api/schemas';
import { ActivityLogEntries } from './ActivityLogEntries';

export function ActivityLog() {
  const { data: eventResponse, isPending, isError, error } = useGetEvents();
  const [displayResponses, setDisplayResponses] = useState<EventResponse[]>();
  const [conditionEventFilter, setConditionEventFilter] = useState<string>(
    DEFAULT_CONDITION_FILTER_STATE
  );

  useEffect(() => {
    if (
      displayResponses === undefined ||
      conditionEventFilter === DEFAULT_CONDITION_FILTER_STATE
    ) {
      setDisplayResponses(eventResponse?.data);
    } else {
      const matchingActivityEntries = eventResponse?.data.filter((e) => {
        return e.configuration_name === conditionEventFilter;
      });
      setDisplayResponses(matchingActivityEntries);
    }
  }, [conditionEventFilter, displayResponses, eventResponse]);

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return <ErrorFallback error={error} />;

  const conditionOptions: Set<string> = new Set();

  eventResponse?.data.forEach((e) => {
    conditionOptions.add(e.configuration_name);
  });

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
            value={conditionEventFilter}
            onChange={(e) => setConditionEventFilter(e.target.value)}
          >
            <option>{DEFAULT_CONDITION_FILTER_STATE}</option>
            {Array.from(conditionOptions).map((c) => {
              return <option key={c}>{c}</option>;
            })}
          </Select>
        </div>
      </div>

      <div className="mt-6">
        {displayResponses && (
          <ActivityLogEntries displayResponses={displayResponses} />
        )}
      </div>
    </section>
  );
}

const DEFAULT_CONDITION_FILTER_STATE = 'All conditions';
