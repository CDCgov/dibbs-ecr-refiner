import { useNavigate } from 'react-router';
import {
  GetConfigurationsResponse,
  GetConfigurationsResponseStatus,
} from '../../api/schemas';
import { Table } from '../Table';
interface ConfigurationsTableProps {
  data: GetConfigurationsResponse[];
}

export function ConfigurationsTable({ data }: ConfigurationsTableProps) {
  const navigate = useNavigate();

  const reportableConditionHeader = 'Reportable condition';
  const statusHeader = 'Status';

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
        </tr>
      </thead>
      <tbody>
        {data.map(({ id, name, status }) => {
          return (
            <tr
              key={id}
              aria-label={`View ${status === GetConfigurationsResponseStatus.draft || status === GetConfigurationsResponseStatus.inactive ? 'inactive' : 'active'} configuration for ${name}`}
            >
              <td
                data-label={reportableConditionHeader}
                className="p-0! font-bold!"
                scope="row"
              >
                <button
                  aria-label={`Configure the configuration for ${name}`}
                  className="block h-full w-full cursor-pointer px-4 py-2 text-left"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      void navigate(`/configurations/${id}/build`);
                    }
                  }}
                  onClick={() => {
                    void navigate(`/configurations/${id}/build`);
                  }}
                >
                  {name}
                </button>
              </td>
              <td data-label={statusHeader} className="flex p-0! align-middle">
                <button
                  aria-label={`Configure the configuration for ${name}`}
                  className="block h-full w-full cursor-pointer px-4 py-2 text-left"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      void navigate(`/configurations/${id}/build`);
                    }
                  }}
                  onClick={() => {
                    void navigate(`/configurations/${id}/build`);
                  }}
                >
                  {status === GetConfigurationsResponseStatus.active ? (
                    <span className="text-success-dark">
                      <span className="text-color-success not-sr-only pr-1">
                        ⏺︎
                      </span>
                      Active
                    </span>
                  ) : (
                    <span>Inactive</span>
                  )}
                </button>
              </td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
}
