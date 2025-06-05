import { useState } from 'react';
import SuccessSvg from '../../assets/green-check.svg';
// import { Button } from '../../components/Button';
import { Container, Content } from './Layout';
import XMLViewer from 'react-xml-viewer';
import { Condition } from '../../services/demo';
import { Label, Select } from '@trussworks/react-uswds';

interface SuccessProps {
  conditions: Condition[];
  downloadToken: string;
}

// export function Success({ conditions, downloadToken }: SuccessProps) {
//   const [downloadError, setDownloadError] = useState<string>('');

export function Success({ conditions }: SuccessProps) {

  // defaults to first condition found
  const [selectedCondition, setSelectedCondition] = useState<Condition>(
    conditions[0]
  );

  // async function downloadFile(token: string) {
  //   try {
  //     const resp = await fetch(`/api/v1/demo/download/${token}`);
  //     if (!resp.ok) {
  //       const errorMsg = `Failed to download refined eCR with token: ${token}`;
  //       setDownloadError(errorMsg);
  //       throw Error(errorMsg);
  //     }
  //
  //     const blob = await resp.blob();
  //     const blobUrl = URL.createObjectURL(blob);
  //
  //     const link = document.createElement('a');
  //     link.href = blobUrl;
  //     link.download = 'ecr_download.zip';
  //     document.body.appendChild(link);
  //     link.click();
  //     document.body.removeChild(link);
  //     URL.revokeObjectURL(blobUrl);
  //   } catch (error) {
  //     console.error(error);
  //   }
  // }

  function onChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const value = e.currentTarget.value;
    const newSelectedCondition = conditions.find((c) => c.code === value);

    if (!newSelectedCondition) return selectedCondition;

    setSelectedCondition(newSelectedCondition);
  }

  return (
    <>
      <Container color="green" className="w-full !p-8">
        <Content className="flex flex-col items-start gap-4">
          <div className="flex flex-col">
            <h1 className="!m-0 !p-0 text-xl font-bold text-black">
              eCR successfully refined!
            </h1>
          </div>
          <div className="flex min-h-full min-w-full flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-10">
              <div className="flex items-center gap-2">
                <Label htmlFor="condition-select" className="text-bold !m-0">
                  CONDITION:
                </Label>
                <Select
                  id="condition-select"
                  name="condition-select"
                  className="!m-0"
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
              <div className="flex flex-col gap-4 sm:flex-row">
                {selectedCondition.stats.map((stat) => (
                  <SuccessItem key={stat}>{stat}</SuccessItem>
                ))}
              </div>
            </div>
            {/*<div className="flex flex-col items-center gap-3">*/}
            {/*  <Button onClick={async () => await downloadFile(downloadToken)}>*/}
            {/*    Download refined eCR*/}
            {/*  </Button>*/}
            {/*  {downloadError ? <span>File download has expired.</span> : null}*/}
            {/*</div>*/}
          </div>
        </Content>
      </Container>
      <EicrComparison
        unrefinedEicr={selectedCondition.unrefined_eicr}
        refinedEicr={selectedCondition.refined_eicr}
        stats={selectedCondition.stats}
      />
    </>
  );
}

interface SuccessItemProps {
  children: React.ReactNode;
}

function SuccessItem({ children }: SuccessItemProps) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-white p-4">
      <GreenCheck />
      <p className="flex flex-col items-center gap-2 leading-snug font-bold">
        {children}
      </p>
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
    <div className="flex w-full justify-between gap-10">
      <EicrText title="Unrefined eICR" xml={unrefinedEicr} />
      <div className="border-thin border-gray-300"></div>
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
    <div className="mt-10 flex w-1/2 flex-col gap-1">
      <h2 className="mb-4 text-3xl font-bold">{title}</h2>
      {/* There's not an easy way to apply classes directly to XMLViewer
      so we're using Tailwind to target the child XMLViewer div instead */}
      <div className="[&>div]:ml-5 [&>div]:h-190 [&>div]:w-full [&>div]:overflow-auto">
        <XMLViewer xml={xml} collapsible theme={{ commentColor: 'black' }} />
      </div>
    </div>
  );
}
