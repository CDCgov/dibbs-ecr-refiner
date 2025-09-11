import { Table as UswdsTable } from '@trussworks/react-uswds';
import { StatusPill } from '../StatusPill';
import { useNavigate } from 'react-router';
import { GetConfigurationsResponse } from '../../api/schemas';
interface ConfigurationsTableProps {
  data: GetConfigurationsResponse[];
}

export function ConfigurationsTable({ data }: ConfigurationsTableProps) {
  const navigate = useNavigate();

  const reportableConditionHeader = 'reportable condition'.toUpperCase();
  const statusHeader = 'status'.toUpperCase();

  if (!data.length) {
    return (
      <UswdsTable stackedStyle="default">
        <thead>
          <tr>
            <th scope="col">{reportableConditionHeader}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th data-label={reportableConditionHeader} scope="row">
              No configurations available
            </th>
          </tr>
        </tbody>
      </UswdsTable>
    );
  }

  return (
    <UswdsTable stackedStyle="default">
      <thead>
        <tr>
          <th scope="col">{reportableConditionHeader}</th>
          <th scope="col">{statusHeader}</th>
        </tr>
      </thead>
      <tbody>
        {data.map(({ name, id, is_active }) => {
          return (
            <tr
              key={id}
              onClick={() => void navigate(`/configurations/${id}/build`)}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  void navigate(`/configurations/${id}/build`);
                }
              }}
              aria-label={`View configuration for ${name}`}
            >
              <td
                data-label={reportableConditionHeader}
                className="!font-bold"
                scope="row"
              >
                {name}
              </td>
              <td data-label={statusHeader}>
                <StatusPill status={is_active ? 'on' : 'off'} />
              </td>
            </tr>
          );
        })}
      </tbody>
    </UswdsTable>
  );
}
