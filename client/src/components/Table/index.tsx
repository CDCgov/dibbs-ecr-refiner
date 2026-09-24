import React from 'react';
import classNames from 'classnames';

interface TableProps extends React.HTMLAttributes<HTMLTableElement> {
  children: React.ReactNode;
  className?: string;

  // New styling props to replace legacy CSS:
  rounded?: boolean; // rounded-lg + corner cell radius (7px)
  bordered?: boolean; // border-gray-cool-30 border + cell borders
  borderless?: boolean; // border-separate border-spacing-0 + minimal borders
  hover?: boolean; // hover:bg-gray-200 on tbody rows
  maxWidth?: 'sm' | 'md' | 'lg' | 'full'; // max-w-302 equivalent
  layout?: 'auto' | 'fixed'; // table-auto vs table-fixed
  cellHeight?: 'compact' | 'normal' | 'spacious'; // h-17 equivalent
}

export function Table({
  children,
  className,
  rounded = false,
  bordered = false,
  borderless = false,
  hover = false,
  maxWidth,
  layout = 'auto',
  cellHeight = 'normal',
  ...props
}: TableProps) {
  const maxWidthClasses = {
    sm: 'max-w-96',
    md: 'max-w-302',
    lg: 'max-w-4xl',
    full: 'max-w-full',
  };

  const cellHeightClasses = {
    compact: '[&_tbody_td]:h-12',
    normal: '[&_tbody_td]:h-17',
    spacious: '[&_tbody_td]:h-20',
  };

  return (
    <table
      className={classNames(
        'text-gray-cool-90 w-full text-left text-base',
        { 'border-collapse': !borderless && !rounded },
        { 'border-separate border-spacing-0 rounded-lg': rounded },
        { 'border-gray-cool-30 border': bordered },
        { 'border-separate border-spacing-0': borderless },
        { '[&_tbody_tr:hover]:bg-gray-200': hover },
        layout === 'auto' ? 'table-auto' : 'table-fixed',
        maxWidth ? maxWidthClasses[maxWidth] : '',
        cellHeightClasses[cellHeight],
        // Custom CSS for corner cell radius when rounded is true
        rounded &&
          '[&_tr:first-child_th:first-child]:rounded-tl-lg [&_tr:first-child_th:last-child]:rounded-tr-lg [&_tr:last-child_td:first-child]:rounded-bl-lg [&_tr:last-child_td:last-child]:rounded-br-lg',
        className
      )}
      {...props}
    >
      {children}
    </table>
  );
}

interface TableHeadProps extends React.HTMLAttributes<HTMLTableSectionElement> {
  children: React.ReactNode;
  className?: string;
  stickyHeader?: boolean;
  bordered?: boolean;
}

export function TableHead({
  children,
  className,
  stickyHeader = false,
  bordered = false,
  ...props
}: TableHeadProps) {
  return (
    <thead
      className={classNames(
        { 'z-sticky sticky top-0': stickyHeader },
        { 'border-gray-cool-40 border-b': bordered },
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
  striped?: boolean;
  bordered?: boolean;
  background?: 'white' | 'transparent';
}

export function TableBody({
  children,
  className,
  striped = false,
  bordered = false,
  background = 'transparent',
  ...props
}: TableBodyProps) {
  return (
    <tbody
      className={classNames(
        {
          'divide-gray-cool-40 divide-y': bordered,
          '[&>tr:nth-child(even)]:bg-gray-cool-2': striped,
          'bg-white': background === 'white',
          'bg-transparent': background === 'transparent',
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
  bordered?: boolean;
}

export function TableRow({
  children,
  className,
  bordered = false,
  ...props
}: TableRowProps) {
  return (
    <tr
      className={classNames(
        { 'border-gray-cool-60 border-b': bordered },
        className
      )}
      {...props}
    >
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
  size?: 'sm' | 'base';
}

export function TableCell({
  children,
  className,
  size = 'base',
  ...props
}: TableCellProps) {
  return (
    <td
      className={classNames(
        'px-4 py-2',
        { 'text-sm': size === 'sm' },
        { 'text-base': size === 'base' },
        className
      )}
      {...props}
    >
      {children}
    </td>
  );
}
