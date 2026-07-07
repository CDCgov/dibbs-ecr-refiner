import { Button } from '@components/Button';
import { CloseIcon } from '@components/Icons/CloseIcon';
import { InfoIcon } from '@components/Icons/InfoIcon';

interface NotificationBannerProps {
  message: string;
  navigateToPageUrl: string;
  onDismiss: () => void;
  type: 'app' | 'tes';
}
export function NotificationBanner({
  message,
  navigateToPageUrl,
  onDismiss,
  type,
}: NotificationBannerProps) {
  return (
    <div className="drop-shadow-nav bg-blue-100 px-4 py-3">
      <div className="mx-auto flex max-w-7xl items-center">
        <div className="flex flex-1 items-center justify-center gap-10">
          <div className="flex items-center gap-2">
            <InfoIcon className="fill-blue-40v shrink-0" />
            <span className="font-bold text-blue-500">{message}</span>
          </div>
          <Button
            ariaLabel={type === 'tes' ? 'View TES updates' : 'View app updates'}
            variant="secondary"
            to={navigateToPageUrl}
            onClick={onDismiss}
          >
            View updates
          </Button>
        </div>
        <Button
          ariaLabel={
            type === 'tes'
              ? 'Dismiss TES updates notification'
              : 'Dismiss app updates notification'
          }
          variant="unstyled"
          className="hover:cursor-pointer hover:opacity-75 focus:outline-none"
          onClick={onDismiss}
        >
          <CloseIcon size={24} className="fill-blue-500" />
        </Button>
      </div>
    </div>
  );
}
