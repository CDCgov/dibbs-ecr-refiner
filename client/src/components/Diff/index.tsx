import { useState } from 'react';
import SuccessSvg from '../../assets/green-check.svg';
import { Condition } from '../../services/demo';
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';
import { FaColumns, FaAlignLeft } from 'react-icons/fa'; // Icons for split and inline

interface SuccessProps {
  condition: Condition;
  unrefinedEicr: string;
  downloadToken: string;
}

export function Diff({
  condition,
  downloadToken,
  unrefinedEicr,
}: SuccessProps) {
  const [downloadError, setDownloadError] = useState<string>('');
  const [showDiffOnly, setShowDiffOnly] = useState(true);
  const [splitView, setSplitView] = useState(true);

  async function downloadFile(token: string) {
    try {
      const resp = await fetch(`/api/v1/demo/download/${token}`);
      if (!resp.ok) {
        const errorMsg = `Failed to download refined eCR with token: ${token}`;
        setDownloadError(errorMsg);
        throw Error(errorMsg);
      }

      const blob = await resp.blob();
      const blobUrl = URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = 'ecr_download.zip';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error(error);
    }
  }

  return (
    <div>
      {/* Main header container */}
      <div className="mt-6 mb-8 flex h-[64px] items-center justify-between rounded-md bg-sky-100 p-3">
        {/* Left section */}
        <div className="flex items-center gap-4">
          <div className="flex flex-col gap-4 lg:flex-row">
            {condition.stats.map((stat) => (
              <SuccessItem key={stat}>{stat}</SuccessItem>
            ))}
          </div>
          <div>
            <div className="flex flex-col items-start gap-3">
              <a
                href="#"
                onClick={async (e) => {
                  e.preventDefault();
                  await downloadFile(downloadToken);
                }}
                className="text-blue-500 underline hover:text-blue-700"
              >
                Download results
              </a>
              {downloadError && <span>File download has expired.</span>}
            </div>
          </div>
        </div>

        {/* Right section */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between sm:gap-8">
          {/* Layout group */}
          <div className="flex h-[38px] items-center gap-2">
            <span className="font-medium">Layout</span>
            <button
              onClick={() => setSplitView(true)}
              className={`rounded-md border border-blue-500 px-3 py-1 hover:bg-blue-100 ${
                splitView ? 'bg-blue-500 text-white' : 'bg-white text-black'
              }`}
            >
              <FaColumns />
            </button>
            <button
              onClick={() => setSplitView(false)}
              className={`rounded-md border border-blue-500 px-3 py-1 hover:bg-blue-100 ${
                !splitView ? 'bg-blue-500 text-white' : 'bg-white text-black'
              }`}
            >
              <FaAlignLeft />
            </button>
          </div>

          {/* Content toggle */}
          <div className="flex items-center gap-2">
            <span className="font-medium">Content</span>
            <div className="flex h-[38px] overflow-hidden rounded-full border-[4px] border-blue-500 bg-white">
              <button
                onClick={() => setShowDiffOnly(false)}
                className={`px-4 py-1 text-sm font-medium transition-colors hover:bg-blue-100 ${
                  !showDiffOnly
                    ? 'bg-blue-500 text-white'
                    : 'bg-white text-blue-500'
                }`}
              >
                Show all
              </button>
              <button
                onClick={() => setShowDiffOnly(true)}
                className={`px-4 py-1 text-sm font-medium transition-colors hover:bg-blue-100 ${
                  showDiffOnly
                    ? 'bg-blue-500 text-white'
                    : 'bg-white text-blue-500'
                }`}
              >
                Diff only
              </button>
            </div>
          </div>
        </div>
      </div>
      <ReactDiffViewer
        oldValue={unrefinedEicr}
        newValue={condition.refined_eicr}
        splitView={splitView}
        showDiffOnly={showDiffOnly}
        compareMethod={DiffMethod.WORDS_WITH_SPACE}
        leftTitle={'Original eICR'}
        rightTitle={'Refined eICR'}
        styles={{
          titleBlock: {
            fontFamily: 'Public Sans, sans-serif',
            fontSize: '16px',
          },
          diffContainer: {
            borderRadius: '1px',
            borderStyle: '',
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
      <GreenCheck />
      <p className="leading-snug">{children}</p>
    </div>
  );
}

function GreenCheck() {
  return <img className="h-6 w-6" src={SuccessSvg} alt="" />;
}
