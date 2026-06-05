import { Icon } from '@trussworks/react-uswds';
import classNames from 'classnames';

interface ConfigLockBannerProps {
  lockedByName: string | null | undefined;
  lockedByEmail: string | null | undefined;
  className?: string;
}

export function ConfigLockBanner({
  lockedByName,
  lockedByEmail,
  className,
}: ConfigLockBannerProps) {
  if (!lockedByName || !lockedByEmail) return null;
  return (
    <div
      role="status"
      aria-live="polite"
      tabIndex={0}
      className={classNames(
        'bg-state-warning-lighter border-b-state-warning! flex w-full flex-col gap-4 px-8 py-4 shadow-lg md:flex-row md:justify-between lg:px-20',
        className
      )}
    >
      <div className="flex items-center gap-2">
        <Icon.Info
          aria-hidden
          className="fill-state-warning-darker! shrink-0"
          size={3}
        />
        <p className="text-state-warning-darker">
          <strong>View only:</strong> [
          <span className="font-bold">{lockedByName}</span>/
          <span className="font-bold">{lockedByEmail}</span>] currently has this
          configuration open.
        </p>
      </div>
    </div>
  );
}
