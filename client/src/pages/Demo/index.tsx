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
    <div className="flex flex-col min-w-screen gap-20 px-20 py-10">
      <Link className="hover:underline" to="/">
        &#60;-- Return to landing page
      </Link>
      <div className="flex justify-center items-center flex-col gap-6">
        <UploadSuccess />
        <UploadError />
        <ReportableConditions />
        <Container color="blue">
          <img src={UploadSvg} alt="Upload zipfile" />
          <p className="text-black text-base font-normal">
            We will upload a test file for you to view the refinement results
          </p>
          <button
            className="font-bold text-white px-5 py-3 bg-blue-300 rounded inline-flex justify-center items-center gap-2.5 overflow-hidden cursor-pointer"
            onClick={async () => await refetch()}
          >
            Run test
          </button>
          <a
            className="justify-start text-blue-300 text-base font-bold hover:underline"
            href="/api/demo/download"
            download
          >
            Download test file
          </a>
        </Container>
      </div>
      <div className="flex flex-col min-h-full gap-2">
        <div>
          <button
            className="text-white text-xl font-bold bg-blue-300 px-6 px-4 rounded cursor-pointer"
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
          className="border min-h-full"
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
      <img
        src={ErrorSvg}
        alt="Red X indicating an error occured during upload."
      />
      <p className="text-center text-black text-xl font-bold">
        The file could not be read.
      </p>
      <p className="leading-snug">
        Please double check the format and size. It must be less than 1GB.
      </p>
      <button className="font-bold text-white px-5 py-3 bg-black rounded inline-flex justify-start items-center gap-2.5 overflow-hidden">
        Try again
      </button>
    </Container>
  );
}

function UploadSuccess() {
  return (
    <Container color="green">
      <img
        src={SuccessSvg}
        alt="Green checkmark indicating a successful upload."
      />
      <p className="text-center text-black text-xl font-bold">
        eCR successfully refined!
      </p>
      <div className="p-6 bg-white rounded-lg inline-flex flex-col justify-start items-center gap-6">
        <div className="flex flex-col gap-6">
          <p className="leading-snug font-bold">
            eCR file size reduced from XXMB to YYMB
          </p>
          <p className="flex flex-col leading-snug gap-2 items-center">
            <span className="font-bold">
              Found the following data for the condition:
            </span>
            <span>XX labs, Y medications</span>
          </p>
        </div>
      </div>
      <button className="font-bold text-white px-5 py-3 bg-black rounded inline-flex justify-start items-center gap-2.5 overflow-hidden">
        Download file
      </button>
    </Container>
  );
}

function ReportableConditions() {
  return (
    <Container color="blue">
      <img src={InformationSvg} alt="Information icon" />
      <div className="flex flex-col gap-2">
        <p className="text-center text-black text-xl font-bold">
          We found these reportable conditions:
        </p>
        <ul className="text-black text-xl font-bold list-disc ml-6">
          <li>Example condition</li>
        </ul>
      </div>
      <div className="flex flex-col gap-2 items-center">
        <p>Would you like to refine the eCR?</p>
        <p>
          Taking this action will retain information relevant only to the
          conditions listed.
        </p>
      </div>
      <button className="font-bold text-white px-5 py-3 bg-blue-300 rounded inline-flex justify-center items-center gap-2.5 overflow-hidden cursor-pointer">
        Refine eCR
      </button>
    </Container>
  );
}

interface ContainerProps {
  color: 'blue' | 'red' | 'green';
  children: React.ReactNode;
  className?: string;
}
function Container({ color, children, className }: ContainerProps) {
  const colors = {
    blue: 'bg-blue-100 border-blue-300',
    red: 'bg-rose-600/10 border-red-300',
    green: 'bg-green-500/10 border-green-500',
  };

  return (
    <div
      className={`${colors[color]} ${className} px-16 py-10 rounded-lg border-1 border-dashed inline-flex flex-col justify-start items-center gap-6 overflow-hidden`}
    >
      {children}
    </div>
  );
}
