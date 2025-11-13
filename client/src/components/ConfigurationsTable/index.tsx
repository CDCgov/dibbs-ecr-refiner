import { StatusPill } from '../StatusPill';
import { useNavigate } from 'react-router';
import { GetConfigurationsResponse } from '../../api/schemas';
import Table from '../Table';
interface ConfigurationsTableProps {
  data: GetConfigurationsResponse[];
}

export function ConfigurationsTable({ data }: ConfigurationsTableProps) {
  const navigate = useNavigate();

  const reportableConditionHeader = 'Reportable condition';
  const statusHeader = 'Status';
  const versionHeader = 'Version';

  if (!data.length) {
    return (
      <Table stackedStyle="default">
        <thead>
          <tr>
            <th scope="col">{reportableConditionHeader}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td data-label={reportableConditionHeader} scope="row">
              No configurations available
            </td>
          </tr>
        </tbody>
      </Table>
    );
  }

  return (
    <Table>
      <thead>
        <tr>
          <th scope="col">{reportableConditionHeader}</th>
          <th scope="col">{statusHeader}</th>
          <th scope="col">{versionHeader}</th>
        </tr>
      </thead>
      <tbody>
        {data.map(({ id, name, status, version }) => {
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
              className="cursor-pointer"
            >
              <td
                data-label={reportableConditionHeader}
                className="!font-bold"
                scope="row"
              >
                {name}
              </td>
              <td data-label={statusHeader}>
                <StatusPill status={status} />
              </td>
              <td data-label={versionHeader}>
                <span>Version {version}</span>
              </td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
}
