import { Table as UswdsTable } from '@trussworks/react-uswds';
import { StatusPill } from '../StatusPill';

interface HeaderProps {
  items: string[];
}

interface TableBodyProps {
  data: Array<TableItem>;
}

interface TableItem {
  name: string;
  status: string;
  id: string;
}

interface ConfigurationsTableProps {
  columns: string[];
  data: Array<TableItem>;
}

function TableHeader({ items }: HeaderProps) {
  return (
    <thead>
      <tr>
        {items.map((name, idx) => {
          return <th key={idx} scope="col">{name}</th>;
        })}
      </tr>
    </thead>
  );
}

function TableBody({ data }: TableBodyProps) {
  return (
    <tbody>
      {data.map((row, idx) => {
        return (
          <tr key={idx}>
            <th scope="row">{row.name}</th>
            <td>
              <StatusPill status={row.status} />
            </td>
          </tr>
        );
      })}
    </tbody>
  );
}
export function ConfigurationsTable({
  columns,
  data,
}: ConfigurationsTableProps) {
  return (
    <UswdsTable stackedStyle="headers">
      <TableHeader items={columns} />
      <TableBody data={data} />
    </UswdsTable>
  );
}
