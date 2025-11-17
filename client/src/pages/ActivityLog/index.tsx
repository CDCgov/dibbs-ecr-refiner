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
  const [filteredLogEntries, setFilteredLogEntries] =
    useState<EventResponse[]>();
  const [conditionFilter, setConditionFilter] = useState<string>(
    ALL_CONDITIONS_LITERAL
  );

  useEffect(() => {
    if (
      filteredLogEntries === undefined ||
      conditionFilter === ALL_CONDITIONS_LITERAL
    ) {
      setFilteredLogEntries(eventResponse?.data);
    } else {
      const matchingActivityEntries = eventResponse?.data.filter((e) => {
        return e.configuration_name === conditionFilter;
      });
      console.log(matchingActivityEntries);
      setFilteredLogEntries(matchingActivityEntries);
    }
  }, [conditionFilter, filteredLogEntries, eventResponse]);

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
            value={conditionFilter}
            onChange={(e) => setConditionFilter(e.target.value)}
          >
            <option>{ALL_CONDITIONS_LITERAL}</option>
            {Array.from(conditionOptions).map((c) => {
              return <option key={c}>{c}</option>;
            })}
          </Select>
        </div>
      </div>

      <div className="mt-6">
        {filteredLogEntries && (
          <ActivityLogEntries filteredLogEntries={filteredLogEntries} />
        )}
      </div>
    </section>
  );
}

const ALL_CONDITIONS_LITERAL = 'All conditions';
