import { Link } from 'react-router';
import UploadSvg from '../../assets/upload.svg';
import ErrorSvg from '../../assets/red-x.svg';
import SuccessSvg from '../../assets/green-check.svg';
import InformationSvg from '../../assets/information.svg';
import { useQuery, useQueryClient } from '@tanstack/react-query';

async function upload(): Promise<string> {
  const resp = await fetch('/api/demo/upload');
  return resp.text();
}

export default function Demo() {
  const queryClient = useQueryClient();
  const { data, refetch } = useQuery({
    queryKey: ['upload'],
    queryFn: upload,
    enabled: false,
    initialData: '',
  });

  return (
    <div className="flex min-w-screen flex-col gap-20 px-20 py-10">
      <Link className="hover:underline" to="/">
        &#60;-- Return to landing page
      </Link>
      <div className="flex flex-col items-center justify-center gap-6">
        <UploadSuccess />
        <UploadError />
        <ReportableConditions />
        <Container color="blue">
          <Content>
            <img src={UploadSvg} alt="Upload zipfile" />
            <p className="text-base font-normal text-black">
              We will upload a test file for you to view the refinement results
            </p>
            <button
              className="inline-flex cursor-pointer items-center justify-center gap-2.5 overflow-hidden rounded bg-blue-300 px-5 py-3 font-bold text-white"
              onClick={async () => await refetch()}
            >
              Run test
            </button>
            <a
              className="justify-start text-base font-bold text-blue-300 hover:underline"
              href="/api/demo/download"
              download
            >
              Download test file
            </a>
          </Content>
        </Container>
      </div>
      <div className="flex min-h-full flex-col gap-2">
        <div>
          <button
            className="cursor-pointer rounded bg-blue-300 px-4 px-6 text-xl font-bold text-white"
            onClick={() =>
              queryClient.resetQueries({ queryKey: ['upload'], exact: true })
            }
          >
            Reset
          </button>
        </div>
        <label htmlFor="result">Refined eICR:</label>
        <textarea
          id="result"
          className="min-h-full border"
          disabled
          value={data}
        />
      </div>
    </div>
  );
}

function UploadError() {
  return (
    <Container color="red">
      <Content>
        <img
          src={ErrorSvg}
          alt="Red X indicating an error occured during upload."
        />
        <p className="text-center text-xl font-bold text-black">
          The file could not be read.
        </p>
        <p className="leading-snug">
          Please double check the format and size. It must be less than 1GB.
        </p>
        <button className="inline-flex items-center justify-start gap-2.5 overflow-hidden rounded bg-black px-5 py-3 font-bold text-white">
          Try again
        </button>
      </Content>
    </Container>
  );
}

function UploadSuccess() {
  return (
    <Container color="green">
      <Content>
        <img
          src={SuccessSvg}
          alt="Green checkmark indicating a successful upload."
        />
        <p className="text-center text-xl font-bold text-black">
          eCR successfully refined!
        </p>
        <div className="inline-flex flex-col items-center justify-start gap-6 rounded-lg bg-white p-6">
          <div className="flex flex-col gap-6">
            <p className="leading-snug font-bold">
              eCR file size reduced from XXMB to YYMB
            </p>
            <p className="flex flex-col items-center gap-2 leading-snug">
              <span className="font-bold">
                Found the following data for the condition:
              </span>
              <span>XX labs, Y medications</span>
            </p>
          </div>
        </div>
        <button className="inline-flex items-center justify-start gap-2.5 overflow-hidden rounded bg-black px-5 py-3 font-bold text-white">
          Download file
        </button>
      </Content>
    </Container>
  );
}

function ReportableConditions() {
  return (
    <Container color="blue">
      <Content>
        <img src={InformationSvg} alt="Information icon" />
        <div className="flex flex-col gap-2">
          <p className="text-center text-xl font-bold text-black">
            We found these reportable conditions:
          </p>
          <ul className="ml-6 list-disc text-xl font-bold text-black">
            <li>Example condition</li>
          </ul>
        </div>
        <div className="flex flex-col items-center gap-2">
          <p>Would you like to refine the eCR?</p>
          <p>
            Taking this action will retain information relevant only to the
            conditions listed.
          </p>
        </div>
        <button className="inline-flex cursor-pointer items-center justify-center gap-2.5 overflow-hidden rounded bg-blue-300 px-5 py-3 font-bold text-white">
          Refine eCR
        </button>
      </Content>
    </Container>
  );
}

interface ContainerProps {
  color: 'blue' | 'red' | 'green';
  children: React.ReactNode;
  className?: string;
}
function Container({ color, children, className }: ContainerProps) {
  const colorOptions = {
    blue: 'bg-blue-100 border-blue-300',
    red: 'bg-rose-600/10 border-red-300',
    green: 'bg-green-500/10 border-green-500',
  };

  return (
    <div
      className={`${colorOptions[color]} ${className} items-center gap-6 rounded-lg border-1 border-dashed px-20 py-8`}
    >
      {children}
    </div>
  );
}

interface ContentProps {
  children: React.ReactNode;
}

function Content({ children }: ContentProps) {
  return <div className="flex flex-col items-center gap-6">{children}</div>;
}
