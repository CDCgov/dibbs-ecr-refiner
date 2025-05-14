import { useState } from 'react';
import SuccessSvg from '../../assets/green-check.svg';
import { Button } from '../../components/Button';
import { Container, Content } from './Layout';
import XMLViewer from 'react-xml-viewer';

interface SuccessProps {
  unrefinedEicr: string;
  refinedEicr: string;
  stats: string[];
  downloadToken: string;
}

export function Success({
  unrefinedEicr,
  refinedEicr,
  stats,
  downloadToken,
}: SuccessProps) {
  const [downloadError, setDownloadError] = useState<string>('');

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
    <>
      <Container color="green" className="w-full !p-8">
        <Content className="flex flex-col items-start gap-4">
          <h1 className="text-xl font-bold text-black">
            eCR successfully refined!
          </h1>
          <div className="flex min-h-full min-w-full flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex flex-col gap-4 sm:flex-row">
              {stats.map((stat) => (
                <SuccessItem key={stat}>{stat}</SuccessItem>
              ))}
            </div>
            <div className="flex flex-col items-center">
              {/* TODO: make this button work */}
              <Button
                onClick={async () => await downloadFile(downloadToken)}
                color="black"
              >
                Download refined eCR
              </Button>
              {downloadError ? <span>File download has expired.</span> : null}
            </div>
          </div>
        </Content>
      </Container>
      <EicrComparison
        unrefinedEicr={unrefinedEicr}
        refinedEicr={refinedEicr}
        stats={stats}
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
      <div className="border-1 border-gray-300"></div>
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
    <div className="flex w-1/2 flex-col gap-2">
      <h2 className="text-3xl font-bold">{title}</h2>
      {/* There's not an easy way to apply classes directly to XMLViewer
      so we're using Tailwind to target the child XMLViewer div instead */}
      <div className="[&>div]:h-190 [&>div]:w-full [&>div]:overflow-auto [&>div]:p-10">
        <XMLViewer xml={xml} collapsible theme={{ commentColor: 'black' }} />
      </div>
    </div>
  );
}
