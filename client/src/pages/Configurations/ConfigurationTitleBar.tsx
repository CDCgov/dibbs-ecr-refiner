import { Button } from '@components/Button';

interface ConfigurationTitleBarProps {
  title: string;
  subtitle?: React.ReactNode;
  actionButton?: {
    text: string;
    onClick: () => void;
    disabled?: boolean;
  };
}

export function ConfigurationTitleBar({
  title,
  subtitle,
  actionButton,
}: ConfigurationTitleBarProps) {
  return (
    <div className="flex items-start justify-between">
      <div className="flex flex-col">
        <div className="mb-2 flex items-center">
          <h2 className="text-gray-cool-90 mr-4 text-[1.75rem] font-bold">
            {title}
          </h2>
        </div>
        {subtitle ? <span>{subtitle}</span> : null}
      </div>
      {actionButton && (
        <Button
          className="m-0! p-2! px-4! text-sm! whitespace-nowrap"
          variant="secondary"
          onClick={actionButton.onClick}
          disabled={actionButton.disabled}
        >
          {actionButton.text}
        </Button>
      )}
    </div>
  );
}
