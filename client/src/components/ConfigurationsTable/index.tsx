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
  const lastActivatedHeader = 'Last activated';

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
          <th scope="col">{lastActivatedHeader}</th>
        </tr>
      </thead>
      <tbody>
        {data.map(
          ({
            name,
            link_to_config_id,
            status,
            version,
            last_activated_time,
            last_activated_by_user,
            show_has_draft,
          }) => {
            return (
              <tr
                key={link_to_config_id}
                onClick={() =>
                  void navigate(`/configurations/${link_to_config_id}/build`)
                }
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    void navigate(`/configurations/${link_to_config_id}/build`);
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
                  <div className="flex flex-col">
                    <span>Version {version}</span>
                    {show_has_draft ? (
                      <span className="italic">Draft created</span>
                    ) : null}
                  </div>
                </td>
                <td data-label={lastActivatedHeader}>
                  {last_activated_time ? (
                    <div className="flex flex-col">
                      <span>{last_activated_time}</span>
                      <span>{last_activated_by_user}</span>
                    </div>
                  ) : (
                    <span>N/A</span>
                  )}
                </td>
              </tr>
            );
          }
        )}
      </tbody>
    </Table>
  );
}
