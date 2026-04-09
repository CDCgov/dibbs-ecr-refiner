import { Link } from 'react-router';
import {
  DbConfigurationStatus,
  GetConfigurationsResponse,
} from '../../api/schemas';
import { Table } from '../Table';
interface ConfigurationsTableProps {
  data: GetConfigurationsResponse[];
}

export function ConfigurationsTable({ data }: ConfigurationsTableProps) {
  const reportableConditionHeader = 'Reportable Condition Configurations';
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
              aria-label={`View ${status === DbConfigurationStatus.draft || status === DbConfigurationStatus.inactive ? 'inactive' : 'active'} configuration for ${name}`}
            >
              <td
                data-label={reportableConditionHeader}
                className="p-0! font-bold!"
                scope="row"
              >
                <Link
                  aria-label={`Configure the configuration for ${name}`}
                  to={`/configurations/${id}/build`}
                  className="flex h-full w-full items-center px-4 py-2 text-left"
                >
                  {name}
                </Link>
              </td>
              <td data-label={statusHeader} className="flex p-0! align-middle">
                <Link
                  aria-label={`Configure the configuration for ${name}`}
                  to={`/configurations/${id}/build`}
                  className="flex h-full w-full items-center px-4 py-2 text-left"
                >
                  {status === DbConfigurationStatus.active ? (
                    <span className="text-success-dark">
                      <span className="text-color-success not-sr-only pr-1">
                        ⏺︎
                      </span>
                      Active
                    </span>
                  ) : (
                    <span>Inactive</span>
                  )}
                </Link>
              </td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
}
