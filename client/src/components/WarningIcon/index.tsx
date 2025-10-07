import { Icon, IconProps } from '@trussworks/react-uswds';
import classNames from 'classnames';

export function WarningIcon({ className, ...props }: IconProps) {
  return (
    <Icon.Warning
      className={classNames('[&_path]:fill-state-error shrink-0', className)}
      {...props}
    />
  );
}
