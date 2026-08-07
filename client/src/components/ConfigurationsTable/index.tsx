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
            <td data-label={reportableConditionHeader}>
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
          const isActive = status === DbConfigurationStatus.active;
          return (
            <tr key={id} className="relative">
              <td
                data-label={reportableConditionHeader}
                className="p-0! font-bold!"
              >
                <Link
                  aria-label={`Configure ${name}`}
                  to={`/configurations/${id}/customize-sections`}
                  className="relative z-0 flex items-center px-4 py-2 after:absolute after:inset-0 after:content-['']"
                >
                  {name}
                </Link>
              </td>
              <td data-label={statusHeader} className="p-0! align-middle">
                {isActive ? (
                  <span className="text-success-dark flex items-center px-4 py-2">
                    <span
                      className="bg-state-success-dark mr-1 inline-block h-3 w-3"
                      aria-hidden
                    />
                    enabled
                  </span>
                ) : (
                  <span className="text-gray-cool-60 flex items-center px-4 py-2">
                    <span
                      className="bg-gray-cool-60 mr-1 inline-block h-3 w-3"
                      aria-hidden
                    />
                    disabled
                  </span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
}
