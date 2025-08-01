import { Table as UswdsTable } from '@trussworks/react-uswds';
import { StatusPill } from '../StatusPill';

interface TableColumns {
  [key: string]: string;
}

interface TableItem {
  name: string;
  status: 'on' | 'off';
  id: string;
}

interface ConfigurationsTableProps {
  columns: TableColumns;
  data: TableItem[];
}

export function ConfigurationsTable({
  columns,
  data,
}: ConfigurationsTableProps) {
  if (!data.length) {
    return (
      <UswdsTable stackedStyle="default">
        <thead>
          <tr>
            <th scope="col">{columns['name']}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th data-label={columns['name']} scope="row">
              No configurations available
            </th>
          </tr>
        </tbody>
      </UswdsTable>
    );
  }

  // README: This maps the keys of the `data` to a list that can be  so it can be used to create a
  // Table Headers row.
  const dataColumnsMap = Object.keys(data[0]).filter((k) => k !== 'id');

  return (
    <UswdsTable stackedStyle="default">
      <thead>
        <tr>
          {dataColumnsMap.map((k, idx) => {
            return (
              <th key={idx} scope="col">
                {columns[k]}
              </th>
            );
          })}
        </tr>
      </thead>
      <tbody>
        {data.map(({ name, status }, idx) => {
          return (
            <tr key={idx}>
              <th data-label={columns['name']} scope="row">
                {name}
              </th>
              <td data-label={columns['status']}>
                <StatusPill status={status} />
              </td>
            </tr>
          );
        })}
      </tbody>
    </UswdsTable>
  );
}
