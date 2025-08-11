import { useState } from 'react';
import SuccessSvg from '../../assets/green-check.svg';
import XMLViewer from 'react-xml-viewer';
import { Condition } from '../../services/demo';
import { Label, Select } from '@trussworks/react-uswds';
import { Title } from '../../components/Title';
import { Button } from '../../components/Button';

interface SuccessProps {
  conditions: Condition[];
  unrefinedEicr: string;
  presignedDownloadUrl: string;
}

export function Success({
  conditions,
  presignedDownloadUrl,
  unrefinedEicr,
}: SuccessProps) {
  const [downloadError, setDownloadError] = useState<boolean>(false);
  // defaults to first condition found
  const [selectedCondition, setSelectedCondition] = useState<Condition>(
    conditions[0]
  );

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

  function onChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const value = e.currentTarget.value;
    const newSelectedCondition = conditions.find((c) => c.code === value);

    if (!newSelectedCondition) return selectedCondition;

    setSelectedCondition(newSelectedCondition);
  }

  return (
    <div>
      <Title>eCR refinement results</Title>
      <hr className="border-blue-cool-20 mt-12 mb-12" />
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center">
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
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col gap-4 lg:flex-row">
            {selectedCondition.stats.map((stat) => (
              <SuccessItem key={stat}>{stat}</SuccessItem>
            ))}
          </div>
          <div>
            <div className="flex flex-col items-start gap-3">
              <Button onClick={() => downloadFile(presignedDownloadUrl)}>
                Download results
              </Button>
              {downloadError ? (
                <span>File download URL is incorrect or has expired.</span>
              ) : null}
            </div>
          </div>
        </div>
      </div>
      <EicrComparison
        unrefinedEicr={unrefinedEicr}
        refinedEicr={selectedCondition.refined_eicr}
        stats={selectedCondition.stats}
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

interface EicrComparisonProps {
  unrefinedEicr: string;
  refinedEicr: string;
  stats: string[];
}

export function EicrComparison({
  unrefinedEicr,
  refinedEicr,
}: EicrComparisonProps) {
  return (
    <div className="flex flex-col justify-between gap-10 xl:flex-row">
      <EicrText title="Unrefined eICR" xml={unrefinedEicr} />
      <EicrText title="Refined eICR" xml={refinedEicr} />
    </div>
  );
}

interface EicrTextProps {
  title: string;
  xml: string;
}

function EicrText({ title, xml }: EicrTextProps) {
  return (
    <div className="mt-10 flex flex-col gap-1 xl:w-1/2">
      <h3 className="font-public-sans mb-4 text-3xl font-bold">{title}</h3>
      {/* There's not an easy way to apply classes directly to XMLViewer
      so we're using Tailwind to target the child XMLViewer div instead */}
      <div className="rounded-lg bg-white [&>div]:h-190 [&>div]:overflow-auto md:[&>div]:px-10 md:[&>div]:py-7">
        <XMLViewer xml={xml} collapsible theme={{ commentColor: 'black' }} />
      </div>
    </div>
  );
}
