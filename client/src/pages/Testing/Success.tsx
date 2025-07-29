import { useState } from 'react';
import SuccessSvg from '../../assets/green-check.svg';
import { Button } from '../../components/Button';
import { Condition } from '../../services/demo';
import { Label, Select } from '@trussworks/react-uswds';
import { Title } from '../../components/Title';
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';
import { FaColumns, FaAlignLeft } from 'react-icons/fa'; // Icons for split and inline

interface SuccessProps {
  conditions: Condition[];
  unrefinedEicr: string;
  downloadToken: string;
}

export function Success({
  conditions,
  downloadToken,
  unrefinedEicr,
}: SuccessProps) {
  const [downloadError, setDownloadError] = useState<string>('');
  // defaults to first condition found
  const [selectedCondition, setSelectedCondition] = useState<Condition>(
    conditions[0]
  );
  const [showDiffOnly, setShowDiffOnly] = useState(false);
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

  function onChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const value = e.currentTarget.value;
    const newSelectedCondition = conditions.find((c) => c.code === value);

    if (!newSelectedCondition) return selectedCondition;

    setSelectedCondition(newSelectedCondition);
  }

  return (
    <div>
      <div className="flex items-center">
        <Title>eCR refinement results</Title>
        <div className="condition-dropdown">
          <Label htmlFor="condition-select" className="text-bold">
            CONDITION:
          </Label>
          <Select
            id="condition-select"
            name="condition-select"
            defaultValue={selectedCondition.code}
            onChange={onChange}
          >
            {conditions.map((c) => (
              <option key={c.code} value={c.code}>
                {c.display_name}
              </option>
            ))}
          </Select>
        </div>
      </div>
      <div className="diff-header">
        <div className="diff-header-left">
          <div className="diff-stats">
            {selectedCondition.stats.map((stat) => (
              <SuccessItem key={stat}>{stat}</SuccessItem>
            ))}
          </div>
          <div>
            <div className="diff-download">
              <Button onClick={async () => await downloadFile(downloadToken)}>
                Download results
              </Button>
              {downloadError ? <span>File download has expired.</span> : null}
            </div>
          </div>
        </div>
        <div className="diff-header-right">
          <div className="diff-layout-group">
            <span className="diff-label">Layout</span>
            <button
              onClick={() => setSplitView(true)}
              className={`diff-layout-btn ${splitView ? 'active' : ''}`}
            >
              <FaColumns />
            </button>
            <button
              onClick={() => setSplitView(false)}
              className={`diff-layout-btn ${!splitView ? 'active' : ''}`}
            >
              <FaAlignLeft />
            </button>
          </div>
          <div className="diff-toggle-group">
            <span className="diff-label">Content</span>
            <div className="diff-pill-group">
              <button
                onClick={() => setShowDiffOnly(false)}
                className={`diff-pill ${!showDiffOnly ? 'active' : ''}`}
              >
                Show all
              </button>
              <button
                onClick={() => setShowDiffOnly(true)}
                className={`diff-pill ${showDiffOnly ? 'active' : ''}`}
              >
                Diff only
              </button>
            </div>
          </div>
        </div>
      </div>
      <ReactDiffViewer
        oldValue={unrefinedEicr}
        newValue={selectedCondition.refined_eicr}
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
            borderRadius: '4px',
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
