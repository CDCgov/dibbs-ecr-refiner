import {
  Table as UswdsTable,
  TableProps as UswdsTableProps,
} from '@trussworks/react-uswds';

type TableProps = Pick<
  UswdsTableProps,
  | 'children'
  | 'className'
  | 'bordered'
  | 'striped'
  | 'scrollable'
  | 'stackedStyle'
  | 'fullWidth'
>;

const Table = ({
  children,
  bordered,
  className,
  striped,
  fullWidth,
  scrollable,
  stackedStyle = 'default',
}: TableProps) => {
  return (
    <UswdsTable
      bordered={bordered}
      striped={striped}
      fullWidth={fullWidth}
      scrollable={scrollable}
      stackedStyle={stackedStyle}
      className={className}
    >
      {children}
    </UswdsTable>
  );
};

export default Table;
