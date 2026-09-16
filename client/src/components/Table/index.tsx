import React, { createContext, useContext } from 'react';
import classNames from 'classnames';

interface TableContextValue {
  striped: boolean;
  bordered: boolean;
  stickyHeader: boolean;
}

const TableContext = createContext<TableContextValue | undefined>(undefined);

function useTableContext() {
  const context = useContext(TableContext);
  if (!context) {
    throw new Error(
      'Table compound components must be used within a <Table />'
    );
  }
  return context;
}

interface TableProps {
  children: React.ReactNode;
  className?: string;
  striped?: boolean;
  bordered?: boolean;
  stickyHeader?: boolean;
}

/**
 * A flexible compound Table component for displaying tabular data.
 *
 * @example
 * function MyTable() {
 *   return (
 *     <Table striped stickyHeader>
 *       <TableHead>
 *         <TableRow>
 *           <TableHeaderCell>Name</TableHeaderCell>
 *           <TableHeaderCell>Value</TableHeaderCell>
 *         </TableRow>
 *       </TableHead>
 *       <TableBody>
 *         <TableRow>
 *           <TableCell>Foo</TableCell>
 *           <TableCell>Bar</TableCell>
 *         </TableRow>
 *       </TableBody>
 *     </Table>
 *   );
 * }
 */
export function Table({
  children,
  className,
  striped = false,
  bordered = false,
  stickyHeader = false,
}: TableProps) {
  return (
    <TableContext.Provider value={{ striped, bordered, stickyHeader }}>
      <table
        className={classNames(
          'text-gray-cool-90 w-full border-collapse text-left text-base',
          className
        )}
      >
        {children}
      </table>
    </TableContext.Provider>
  );
}

interface TableHeadProps extends React.HTMLAttributes<HTMLTableSectionElement> {
  children: React.ReactNode;
  className?: string;
}

export function TableHead({ children, className, ...props }: TableHeadProps) {
  const { stickyHeader, bordered } = useTableContext();
  return (
    <thead
      className={classNames(
        { 'z-sticky sticky top-0': stickyHeader },
        { 'border-gray-cool-70 border-b-2': bordered },
        className
      )}
      {...props}
    >
      {children}
    </thead>
  );
}

interface TableBodyProps extends React.HTMLAttributes<HTMLTableSectionElement> {
  children: React.ReactNode;
  className?: string;
}

export function TableBody({ children, className, ...props }: TableBodyProps) {
  const { striped, bordered } = useTableContext();
  return (
    <tbody
      className={classNames(
        {
          'divide-gray-cool-20 divide-y': bordered,
          '[&>tr:nth-child(even)]:bg-gray-cool-5': striped,
        },
        className
      )}
      {...props}
    >
      {children}
    </tbody>
  );
}

interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  children: React.ReactNode;
  className?: string;
}

export function TableRow({ children, className, ...props }: TableRowProps) {
  return (
    <tr className={className} {...props}>
      {children}
    </tr>
  );
}

interface TableHeaderCellProps extends Omit<
  React.ThHTMLAttributes<HTMLTableCellElement>,
  'scope'
> {
  children?: React.ReactNode;
  className?: string;
  scope?: 'col' | 'row';
}

export function TableHeaderCell({
  children,
  className,
  scope = 'col',
  ...props
}: TableHeaderCellProps) {
  return (
    <th
      scope={scope}
      className={classNames('px-4 py-2 font-semibold', className)}
      {...props}
    >
      {children}
    </th>
  );
}

interface TableCellProps extends React.TdHTMLAttributes<HTMLTableCellElement> {
  children: React.ReactNode;
  className?: string;
}

export function TableCell({ children, className, ...props }: TableCellProps) {
  return (
    <td className={classNames('px-4 py-2', className)} {...props}>
      {children}
    </td>
  );
}
