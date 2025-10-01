import { useState } from 'react';
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';
import { FaColumns, FaAlignLeft } from 'react-icons/fa';
import { RefinedTestingDocument } from '../../api/schemas';
import classNames from 'classnames';
import { Button } from '../Button';

type DiffProps = Pick<
  RefinedTestingDocument,
  'refined_download_url' | 'unrefined_eicr'
> & {
  condition: RefinedTestingDocument['conditions'][0];
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
                Download eICR file
              </Button>
              {downloadError && <span>File download has expired.</span>}
            </div>
          </div>
        </div>

        {/* Right section */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between sm:gap-8">
          {/* Layout group */}
          <div className="flex items-center gap-2">
            <span className="font-medium">Layout</span>
            <button
              aria-label="Show split diff"
              onClick={() => setSplitView(true)}
              className={classNames(
                'rounded-md border border-blue-500 px-3 py-1 hover:cursor-pointer hover:bg-blue-100 hover:text-black',
                {
                  'bg-blue-500 text-white': splitView,
                  'bg-white text-black': !splitView,
                }
              )}
            >
              <FaColumns />
            </button>
            <button
              aria-label="Show stacked diff"
              onClick={() => setSplitView(false)}
              className={classNames(
                'rounded-md border border-blue-500 px-3 py-1 hover:cursor-pointer hover:bg-blue-100 hover:text-black',
                {
                  'bg-blue-500 text-white': !splitView,
                  'bg-white text-black': splitView,
                }
              )}
            >
              <FaAlignLeft />
            </button>
          </div>

          {/* Content toggle */}
          <div className="flex items-center gap-2">
            <span className="font-medium">Content</span>
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
