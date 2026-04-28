import { Button } from '@components/Button';
import classNames from 'classnames';

interface IconProps {
  isActive: boolean;
}
function SymbolsIcon({ isActive }: IconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M5 21C4.45 21 3.97917 20.8042 3.5875 20.4125C3.19583 20.0208 3 19.55 3 19V5C3 4.45 3.19583 3.97917 3.5875 3.5875C3.97917 3.19583 4.45 3 5 3H19C19.55 3 20.0208 3.19583 20.4125 3.5875C20.8042 3.97917 21 4.45 21 5V19C21 19.55 20.8042 20.0208 20.4125 20.4125C20.0208 20.8042 19.55 21 19 21H5ZM5 19H11V5H5V19Z"
        fill={isActive ? '#2E6276' : '#71767A'}
      />
      <rect
        x="13"
        y="5"
        width="6"
        height="14"
        fill={isActive ? '#2E6276' : '#71767A'}
      />
    </svg>
  );
}

function DashboardIcon({ isActive }: IconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M7 17H14V15H7V17ZM7 13H17V11H7V13ZM7 9H17V7H7V9ZM5 21C4.45 21 3.97917 20.8042 3.5875 20.4125C3.19583 20.0208 3 19.55 3 19V5C3 4.45 3.19583 3.97917 3.5875 3.5875C3.97917 3.19583 4.45 3 5 3H19C19.55 3 20.0208 3.19583 20.4125 3.5875C20.8042 3.97917 21 4.45 21 5V19C21 19.55 20.8042 20.0208 20.4125 20.4125C20.0208 20.8042 19.55 21 19 21H5ZM5 19H19V5H5V19Z"
        fill={isActive ? '#2E6276' : '#71767A'}
      />
    </svg>
  );
}

type DiffToggleProps = {
  setShowDiffOnly: React.Dispatch<React.SetStateAction<boolean>>;
  showDiffOnly: boolean;
  splitView: boolean;
  setSplitView: React.Dispatch<React.SetStateAction<boolean>>;
};
export function DiffToggleOptions({
  setShowDiffOnly,
  showDiffOnly,
  splitView,
  setSplitView,
}: DiffToggleProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between sm:gap-8">
      {/* Layout group */}
      <div className="flex items-center gap-2">
        <span className="font-bold">Layout</span>
        <div className="border-blue-cool-60 flex gap-1 rounded-sm border p-0">
          <Button
            variant="unstyled"
            aria-label="Show split diff"
            onClick={() => setSplitView(true)}
            className={classNames(
              'rounded-sm px-3 py-2 text-sm font-medium hover:cursor-pointer hover:text-black',
              {
                'bg-blue-cool-10 text-blue-cool-60': splitView,
                'text-gray-cool-50 bg-white': !splitView,
              }
            )}
          >
            <SymbolsIcon isActive={splitView} />
          </Button>
          <Button
            variant="unstyled"
            aria-label="Show stacked diff"
            onClick={() => setSplitView(false)}
            className={classNames(
              'rounded-sm px-3 py-2 text-sm font-medium hover:cursor-pointer hover:text-black focus:outline-offset-0 focus:outline-solid',
              {
                'bg-blue-cool-10 text-blue-cool-60': !splitView,
                'text-gray-cool-50 bg-white': splitView,
              }
            )}
          >
            <DashboardIcon isActive={!splitView} />
          </Button>
        </div>
      </div>

      {/* Content toggle */}
      <div className="flex items-center gap-2">
        <span className="font-bold">Content</span>
        <div className="border-blue-cool-60 flex gap-1 rounded-sm border p-0">
          <Button
            variant="unstyled"
            onClick={() => setShowDiffOnly(false)}
            className={classNames(
              'rounded-sm px-3 py-2 text-sm font-medium hover:cursor-pointer hover:bg-blue-100 hover:text-black',
              {
                'text-gray-cool-50 bg-white': showDiffOnly,
                'bg-blue-cool-10 text-blue-cool-60': !showDiffOnly,
              }
            )}
          >
            Show all
          </Button>
          <Button
            variant="unstyled"
            onClick={() => setShowDiffOnly(true)}
            className={classNames(
              'rounded-sm px-3 py-2 text-sm font-medium hover:cursor-pointer hover:bg-blue-100 hover:text-black',
              {
                'bg-blue-cool-10 text-blue-cool-60': showDiffOnly,
                'text-gray-cool-50 bg-white': !showDiffOnly,
              }
            )}
          >
            Diff only
          </Button>
        </div>
      </div>
    </div>
  );
}
