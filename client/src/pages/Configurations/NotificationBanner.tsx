import { Button } from '@components/Button';
import { CloseIcon } from '@components/Icons/CloseIcon';
import { InfoIcon } from '@components/Icons/InfoIcon';

interface NotificationBannerProps {
  message: string;
  onDismiss: () => void;
  children: React.ReactNode;
}
export function NotificationBanner({
  message,
  onDismiss,
  children,
}: NotificationBannerProps) {
  return (
    <div className="drop-shadow-nav bg-blue-100 px-4 py-3">
      <div className="mx-auto flex max-w-7xl items-center justify-center">
        <div className="flex flex-1 items-center justify-center gap-10">
          <div className="flex items-center justify-between gap-2">
            <InfoIcon className="fill-blue-40v shrink-0" />
            <span className="w-30 font-bold text-blue-500 md:w-75">
              {message}
            </span>
          </div>
          {children}
        </div>
        <Button
          type="button"
          variant="unstyled"
          className="hover:cursor-pointer hover:opacity-75 focus:outline-none"
          onClick={onDismiss}
        >
          <CloseIcon size={24} className="fill-blue-500" />
          <span className="sr-only">Dismiss notification for {message}</span>
        </Button>
      </div>
    </div>
  );
}
