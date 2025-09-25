import {
  Table as UswdsTable,
  TableProps as UswdsTableProps,
} from '@trussworks/react-uswds';
import classNames from 'classnames';

type TableProps = Pick<
  UswdsTableProps,
  | 'children'
  | 'className'
  | 'bordered'
  | 'striped'
  | 'scrollable'
  | 'stackedStyle'
  | 'fullWidth'
> & { contained?: boolean };

const Table: React.FC<TableProps> = ({
  children,
  contained = true,
  bordered,
  className,
  striped,
  fullWidth,
  scrollable,
  stackedStyle = 'default',
}) => {
  return (
    <div className={classNames(className, contained)}>
      <UswdsTable
        bordered={bordered}
        striped={striped}
        fullWidth={fullWidth}
        scrollable={scrollable}
        stackedStyle={stackedStyle}
      >
        {children}
      </UswdsTable>
    </div>
  );
};

export default Table;
