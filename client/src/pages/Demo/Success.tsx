import SuccessSvg from '../../assets/green-check.svg';
import { Button } from '../../components/Button';
import { Container, Content } from './Layout';
import XMLViewer from 'react-xml-viewer';

export function Success({ unrefinedEicr, refinedEicr }: EicrComparisonProps) {
  // TODO: This will come from the API
  const successItems = [
    'eCR file size reduced by 14%',
    'Found 32 observations relevant to the condition(s)',
  ];

  return (
    <>
      <Container color="green" className="w-full !p-8">
        <Content className="flex flex-col items-start gap-4">
          <h1 className="text-xl font-bold text-black">
            eCR successfully refined!
          </h1>
          <div className="flex min-w-full flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex flex-col gap-4 sm:flex-row">
              {successItems.map((item) => (
                <SuccessItem>{item}</SuccessItem>
              ))}
            </div>
            <div>
              {/* TODO: make this button work */}
              <Button color="black">Download refined eCR</Button>
            </div>
          </div>
        </Content>
      </Container>
      <EicrComparison unrefinedEicr={unrefinedEicr} refinedEicr={refinedEicr} />
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
      <div className="p-10">
        <XMLViewer xml={xml} collapsible theme={{ commentColor: 'black' }} />
      </div>
    </div>
  );
}
