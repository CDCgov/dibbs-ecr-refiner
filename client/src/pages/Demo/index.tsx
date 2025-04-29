import UploadSvg from '../../assets/upload.svg';
import ErrorSvg from '../../assets/red-x.svg';
import SuccessSvg from '../../assets/green-check.svg';
import InformationSvg from '../../assets/information.svg';
import { LandingPageLink } from '../../components/LandingPageLink';
import { Button } from '../../components/Button';
import classNames from 'classnames';

export default function Demo() {
  return (
    <main className="flex min-w-screen flex-col gap-20 px-20 py-10">
      <LandingPageLink />
      <div className="flex flex-col items-center justify-center gap-6">
        <UploadError />
        <UploadSuccess />
        <ReportableConditions />
        <RunTest />
        <EicrComparison
          unrefinedEicr="<data>unrefined eICR data</data>"
          refinedEicr="<data>refined eICR data</data>"
        />
      </div>
    </main>
  );
}

function RunTest() {
  return (
    <Container color="blue">
      <Content className="flex gap-3">
        <img src={UploadSvg} alt="" className="p-3" />
        <div className="flex flex-col items-center gap-6">
          <p className="text-base font-normal text-black">
            We will upload a test file for you to view the refinement results
          </p>
          <Button>Run test</Button>
          <a
            className="justify-start text-base font-bold text-blue-300 hover:underline"
            href="/api/demo/download"
            download
          >
            Download test file
          </a>
        </div>
      </Content>
    </Container>
  );
}

function UploadError() {
  return (
    <Container color="red">
      <Content className="gap-10">
        <div className="flex flex-col items-center">
          <img
            className="p-8"
            src={ErrorSvg}
            alt="Red X indicating an error occured during upload."
          />
          <div className="flex flex-col items-center gap-6">
            <p className="text-xl font-bold text-black">
              The file could not be read.
            </p>
            <p className="leading-snug">
              Please double check the format and size. It must be less than 1GB.
            </p>
          </div>
        </div>
        <Button color="black">Try again</Button>
      </Content>
    </Container>
  );
}

function UploadSuccess() {
  return (
    <Container color="green" className="w-full !p-8">
      <Content className="flex flex-col items-start gap-4">
        <p className="text-xl font-bold text-black">
          eCR successfully refined!
        </p>
        <div className="flex min-w-full flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex flex-col gap-4 sm:flex-row">
            <div className="rounded-lg bg-white p-4">
              <div className="flex gap-2">
                <GreenCheck />
                <p className="leading-snug font-bold">
                  eCR file size reduced by 14%
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 rounded-lg bg-white p-4">
              <GreenCheck />
              <p className="flex flex-col items-center gap-2 leading-snug font-bold">
                Found 32 observations relevant to the condition(s)
              </p>
            </div>
          </div>
          <div>
            <Button color="black">Download refined eCR</Button>
          </div>
        </div>
      </Content>
    </Container>
  );
}

function GreenCheck() {
  return <img className="h-6 w-6" src={SuccessSvg} alt="" />;
}

function ReportableConditions() {
  return (
    <Container color="blue">
      <Content className="flex flex-col">
        <img className="p-3" src={InformationSvg} alt="Information icon" />
        <div className="flex flex-col items-center gap-10">
          <div className="flex flex-col gap-6">
            <div className="flex flex-col items-center gap-3">
              <p className="text-center text-xl font-bold text-black">
                We found the following reportable condition(s):
              </p>
              <ul className="list-disc text-xl font-bold text-black">
                <li>Chlamydia trachomatis infection</li>
              </ul>
            </div>
            <div className="flex flex-col items-center gap-2">
              <p>Would you like to refine the eCR?</p>
              <p>
                Taking this action will retain information relevant only to the
                conditions listed.
              </p>
            </div>
          </div>
          <div>
            <Button>Refine eCR</Button>
          </div>
        </div>
      </Content>
    </Container>
  );
}

interface EicrComparisonProps {
  unrefinedEicr: string;
  refinedEicr: string;
}

function EicrComparison({ unrefinedEicr, refinedEicr }: EicrComparisonProps) {
  return (
    <div className="flex w-full justify-between gap-10">
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
    <div className="flex w-1/2 flex-col gap-2">
      <h2 className="text-3xl font-bold">{title}</h2>
      <p className="bg-gray-200">{xml}</p>
    </div>
  );
}

interface ContainerProps {
  color: 'blue' | 'red' | 'green';
  children: React.ReactNode;
  className?: string;
}
function Container({ color, children, className }: ContainerProps) {
  const defaultStyles =
    'items-center gap-6 rounded-lg border-1 border-dashed px-20 py-8';
  return (
    <div
      className={classNames(defaultStyles, className, {
        'border-blue-300 bg-blue-100': color === 'blue',
        'border-red-300 bg-rose-600/10': color === 'red',
        'border-green-500 bg-green-500/10': color === 'green',
      })}
    >
      {children}
    </div>
  );
}

interface ContentProps {
  children: React.ReactNode;
  className?: string;
}

function Content({ children, className }: ContentProps) {
  return (
    <div className={classNames('flex flex-col items-center', className)}>
      {children}
    </div>
  );
}
