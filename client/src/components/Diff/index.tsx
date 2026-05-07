import { useState } from 'react';
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';
import {
  FileInfoResponseValue,
  IndependentTestUploadResponse,
} from '../../api/schemas';
import { Button } from '../Button';
import { getDownloadRefinedEcrQueryKey } from '../../api/demo/demo';
import { DiffToggleOptions } from './DiffToggleOptions';
import { Warning } from './Warning';
import { Spinner } from '@components/Spinner';
import { SpinnerWithMinimalRender } from '@components/Spinner/TimedSpinner';

type DiffProps = Pick<
  IndependentTestUploadResponse,
  'refined_download_key' | 'unrefined_eicr'
> & {
  condition: IndependentTestUploadResponse['refined_conditions'][0];
  renderDiff: boolean;
};

export function Diff({
  refined_download_key,
  unrefined_eicr,
  condition,
  renderDiff,
}: DiffProps) {
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [showDiffOnly, setShowDiffOnly] = useState(true);
  const [splitView, setSplitView] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);

  async function downloadFile(filename: string) {
    setIsDownloading(true);

    try {
      const url = getDownloadRefinedEcrQueryKey(filename)[0];
      const response = await fetch(url);

      if (!response.ok) {
        const { detail } = await response.json();
        setDownloadError(detail ?? 'An unknown error occurred.');
        return;
      }

      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(blobUrl);
      setDownloadError(null);
    } catch (error) {
      console.error(error);
      setDownloadError('An unknown error occurred.');
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <div>
      {/* Main header container */}
      <div className="mt-6 mb-8 flex flex-col items-start justify-between rounded-md bg-white px-2 py-1 md:flex-row md:items-center">
        {/* Left section */}
        <div className="flex items-center gap-4">
          <div className="flex flex-col gap-4 lg:flex-row">
            {condition.stats.map((stat) => (
              <SuccessItem key={stat}>{stat}</SuccessItem>
            ))}
          </div>
          <div>
            <div className="flex flex-col items-start gap-1 py-1">
              <SpinnerWithMinimalRender
                isLoading={isDownloading}
                loadingMessage="Downloading..."
                renderWhenDone={
                  <Button
                    variant="tertiary"
                    onClick={() => downloadFile(refined_download_key)}
                  >
                    Download results
                  </Button>
                }
              />

              {downloadError ? (
                <span className="text-state-error-dark">
                  Error: {downloadError}
                </span>
              ) : null}
            </div>
          </div>
        </div>

        {/* Right section */}
        {renderDiff ? (
          <DiffToggleOptions
            setShowDiffOnly={setShowDiffOnly}
            showDiffOnly={showDiffOnly}
            splitView={splitView}
            setSplitView={setSplitView}
          />
        ) : null}
      </div>

      {renderDiff ? (
        <ReactDiffViewer
          oldValue={unrefined_eicr}
          newValue={condition.refined_eicr}
          splitView={splitView}
          showDiffOnly={showDiffOnly}
          compareMethod={DiffMethod.WORDS_WITH_SPACE}
          leftTitle="Original eICR"
          rightTitle="Refined eICR"
          loadingElement={() => {
            return (
              <div className="m-auto flex w-50 items-center justify-center">
                <Spinner className="m-2" /> Computing diff...
              </div>
            );
          }}
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
      ) : (
        <DiffViewWarning />
      )}
    </div>
  );
}

function DiffViewWarning() {
  return (
    <Warning
      heading={`Maximum uncompressed file size is ${FileInfoResponseValue.max_for_uncompressed_mb}MB`}
      message="This file is too large to view in-browser. Please download the results to compare them."
    />
  );
}

interface SuccessItemProps {
  children: React.ReactNode;
}

function SuccessItem({ children }: SuccessItemProps) {
  return (
    <div className="gapx-2 flex items-center p-4 py-1">
      <span className="mr-1 font-bold">Refiner results: </span>
      <p data-testid="test-refinement-result" className="leading-snug">
        {children}
      </p>
    </div>
  );
}
