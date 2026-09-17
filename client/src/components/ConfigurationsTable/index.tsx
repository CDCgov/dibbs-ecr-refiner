import { Link } from 'react-router';
import {
  DbConfigurationStatus,
  GetConfigurationsResponse,
} from '../../api/schemas';
import {
  Table,
  TableBody,
  TableHead,
  TableHeaderCell,
  TableCell,
  TableRow,
} from '../Table';
import { StatusIndicator } from '@components/StatusIndicator';

interface ConfigurationsTableProps {
  data: GetConfigurationsResponse[];
}

// NOTE: text-gray-cool-90 applied explicitly here because <Table>'s inherited text color doesn't reliably cascade to th/td/a; consider making this a Table component default with design sign-off.
export function ConfigurationsTable({ data }: ConfigurationsTableProps) {
  const reportableConditionHeader = 'Reportable Condition Configurations';
  const statusHeader = 'Status';

  if (!data.length) {
    return (
      <div className="overflow-x-auto">
        <Table className="legacy-table legacy-table--borderless max-w-full!">
          <TableHead>
            <TableRow>
              <TableHeaderCell scope="col" className="text-gray-cool-90">
                {reportableConditionHeader}
              </TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow>
              <TableCell
                data-label={reportableConditionHeader}
                className="text-gray-cool-90"
              >
                No configurations available
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <Table className="legacy-table legacy-table--borderless max-w-full!">
        <TableHead>
          <TableRow>
            <TableHeaderCell scope="col" className="text-gray-cool-90">
              {reportableConditionHeader}
            </TableHeaderCell>
            <TableHeaderCell scope="col" className="text-gray-cool-90">
              {statusHeader}
            </TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map(({ id, name, status }) => {
            const isActive = status === DbConfigurationStatus.active;
            return (
              <TableRow key={id} className="relative">
                <TableCell
                  data-label={reportableConditionHeader}
                  className="p-0! font-bold!"
                >
                  <Link
                    aria-label={`Configure ${name}`}
                    to={`/configurations/${id}/customize-sections`}
                    className="text-gray-cool-90 relative z-0 flex items-center px-4 py-2 after:absolute after:inset-0 after:content-['']"
                  >
                    {name}
                  </Link>
                </TableCell>
                <TableCell
                  data-label={statusHeader}
                  className="p-0! align-middle"
                >
                  <StatusIndicator isActive={isActive} className="px-4 py-2" />
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
