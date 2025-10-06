import { useState } from 'react';
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';
import { IndependentTestUploadResponse } from '../../api/schemas';
import classNames from 'classnames';
import { Button } from '../Button';

type DiffProps = Pick<
  IndependentTestUploadResponse,
  'refined_download_url' | 'unrefined_eicr'
> & {
  condition: IndependentTestUploadResponse['refined_conditions'][0];
};

export function Diff({
  refined_download_url,
  unrefined_eicr,
  condition,
}: DiffProps) {
  const [downloadError, setDownloadError] = useState<boolean>(false);
  const [showDiffOnly, setShowDiffOnly] = useState(true);
  const [splitView, setSplitView] = useState(true);

  function downloadFile(presignedUrl: string) {
    try {
      const link = document.createElement('a');
      link.href = presignedUrl;
      link.download = '';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setDownloadError(false);
    } catch (error) {
      console.error(error);
      setDownloadError(true);
    }
  }

  return (
    <div>
      {/* Main header container */}
      <div className="mt-6 mb-8 flex flex-col items-start justify-between rounded-md bg-white p-3 md:flex-row md:items-center">
        {/* Left section */}
        <div className="flex items-center gap-4">
          <div className="flex flex-col gap-4 lg:flex-row">
            {condition.stats.map((stat) => (
              <SuccessItem key={stat}>{stat}</SuccessItem>
            ))}
          </div>
          <div>
            <div className="flex flex-col items-start gap-3">
              <Button
                variant="tertiary"
                onClick={() => downloadFile(refined_download_url)}
                className="text-blue-400 underline"
              >
                Download results
              </Button>
              {downloadError && <span>File download has expired.</span>}
            </div>
          </div>
        </div>

        {/* Right section */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between sm:gap-8">
          {/* Layout group */}
          <div className="flex items-center gap-2">
            <span className="font-bold">Layout</span>
            <div className="border-blue-cool-60 bg-blue-cool-10 flex overflow-hidden rounded-md border-[1px]">
              <button
                aria-label="Show split diff"
                onClick={() => setSplitView(true)}
                className={classNames(
                  'px-3 py-2 text-sm font-medium hover:cursor-pointer hover:text-black',
                  {
                    'bg-blue-cool-10 text-blue-cool-60': splitView,
                    'text-gray-cool-50 bg-white': !splitView,
                  }
                )}
              >
                <SymbolsIcon isActive={splitView} />
              </button>
              <button
                aria-label="Show stacked diff"
                onClick={() => setSplitView(false)}
                className={classNames(
                  'px-3 py-2 text-sm font-medium hover:cursor-pointer hover:text-black',
                  {
                    'bg-blue-cool-10 text-blue-cool-60': !splitView,
                    'text-gray-cool-50 bg-white': splitView,
                  }
                )}
              >
                <DashboardIcon isActive={!splitView} />
              </button>
            </div>
          </div>

          {/* Content toggle */}
          <div className="flex items-center gap-2">
            <span className="font-bold">Content</span>
            <div className="border-blue-cool-60 bg-blue-cool-10 flex overflow-hidden rounded-sm border-[1px]">
              <button
                onClick={() => setShowDiffOnly(false)}
                className={classNames(
                  'px-3 py-2 text-sm font-medium hover:cursor-pointer hover:bg-blue-100 hover:text-black',
                  {
                    'text-gray-cool-50 bg-white': showDiffOnly,
                    'bg-blue-cool-10 text-blue-cool-60': !showDiffOnly,
                  }
                )}
              >
                Show all
              </button>
              <button
                onClick={() => setShowDiffOnly(true)}
                className={classNames(
                  'px-4 py-1 text-sm font-medium hover:cursor-pointer hover:bg-blue-100 hover:text-black',
                  {
                    'bg-blue-cool-10 text-blue-cool-60': showDiffOnly,
                    'text-gray-cool-50 bg-white': !showDiffOnly,
                  }
                )}
              >
                Diff only
              </button>
            </div>
          </div>
        </div>
      </div>
      <ReactDiffViewer
        oldValue={unrefined_eicr}
        newValue={condition.refined_eicr}
        splitView={splitView}
        showDiffOnly={showDiffOnly}
        compareMethod={DiffMethod.WORDS_WITH_SPACE}
        leftTitle="Original eICR"
        rightTitle="Refined eICR"
        styles={{
          titleBlock: {
            fontFamily: 'Public Sans, sans-serif',
            fontSize: '16px',
          },
          diffContainer: {
            borderRadius: '1px',
            borderStyle: '',
          },
          lineNumber: {
            color: 'black !important',
            opacity: '100 !important',
          },
        }}
      />
    </div>
  );
}

interface SuccessItemProps {
  children: React.ReactNode;
}

function SuccessItem({ children }: SuccessItemProps) {
  return (
    <div className="flex items-center gap-3 p-4">
      <span className="font-bold">Refiner results:</span>
      <p className="leading-snug">{children}</p>
    </div>
  );
}

interface IconProps {
  isActive: boolean;
}
const SymbolsIcon = ({ isActive }: IconProps) => {
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
};

const DashboardIcon = ({ isActive }: IconProps) => {
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
};
