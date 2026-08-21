import { InfoIcon } from '@components/Icons/InfoIcon';
import classNames from 'classnames';
import { LayoutContainer } from '@components/Layout/LayoutContainer';

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
    <LayoutContainer
      breakout
      background={classNames(
        'bg-state-warning-lighter border-b-state-warning! shadow-lg',
        className
      )}
      maxWidth="max-w-7xl"
      padding="px-8 py-4 lg:px-20"
    >
      <div
        role="status"
        aria-live="polite"
        className="flex w-full flex-col gap-4 md:flex-row md:justify-between"
      >
        <div className="flex items-center gap-2">
          <InfoIcon className="fill-state-warning-darker shrink-0" />
          <p className="text-state-warning-darker">
            <strong>View only:</strong> [
            <span className="font-bold">{lockedByName}</span>/
            <span className="font-bold">{lockedByEmail}</span>] currently has
            this configuration open.
          </p>
        </div>
      </div>
    </LayoutContainer>
  );
}
