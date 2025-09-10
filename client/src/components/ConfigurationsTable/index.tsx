import { Table as UswdsTable } from '@trussworks/react-uswds';
import { StatusPill } from '../StatusPill';
import { useNavigate } from 'react-router';
import { GetConfigurationsResponse } from '../../api/schemas';
interface ConfigurationsTableProps {
  data: GetConfigurationsResponse[];
}

export function ConfigurationsTable({ data }: ConfigurationsTableProps) {
  const navigate = useNavigate();

  if (!data.length) {
    return (
      <UswdsTable stackedStyle="default">
        <thead>
          <tr>
            <th scope="col">REPORTABLE CONDITION</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">No configurations available</th>
          </tr>
        </tbody>
      </UswdsTable>
    );
  }

  return (
    <UswdsTable stackedStyle="default">
      <thead>
        <tr>
          <th scope="col">REPORTABLE CONDITION</th>
          <th scope="col">STATUS</th>
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
              <td className="!font-bold" scope="row">
                {name}
              </td>
              <td>
                <StatusPill status={is_active ? 'on' : 'off'} />
              </td>
            </tr>
          );
        })}
      </tbody>
    </UswdsTable>
  );
}
