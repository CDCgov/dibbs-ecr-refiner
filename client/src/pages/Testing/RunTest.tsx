import { Button } from '../../components/Button';
import { Container, Content } from './Layout';
import UploadSvg from '../../assets/upload.svg';
import ForwardSvg from '../../assets/forward.svg';
import { ChangeEvent, useRef } from 'react';
import { Icon } from '@trussworks/react-uswds';
import { useGetEnv } from '../../hooks/useGetEnv';
import classNames from 'classnames';

interface RunTestProps {
  onClickCustomFile: () => Promise<void>;
  onClickSampleFile: () => Promise<void>;
  selectedFile: File | null;
  setSelectedFile: React.Dispatch<React.SetStateAction<File | null>>;
}
export function RunTest({
  onClickSampleFile,
  onClickCustomFile,
  selectedFile,
  setSelectedFile,
}: RunTestProps) {
  const env = useGetEnv();

  function onSelectedFileChange(e: ChangeEvent<HTMLInputElement>) {
    if (e.target.files) {
      const file = e.target.files[0];
      if (file.name.endsWith('.zip')) {
        setSelectedFile(file);
      } else {
        console.error('No file input or incorrect file type.');
        setSelectedFile(null);
      }
    }
  }

  return (
    <div className="flex flex-col gap-6 xl:flex-row">
      <Container color="white">
        <Content className="flex items-start gap-6">
          <img className="px-3 py-1" src={UploadSvg} alt="" />
          <div className="flex flex-col gap-10">
            <p className="flex flex-col gap-2 text-black">
              <span className="font-bold">
                Want to refine your own eCR file?
              </span>
              <span>Please upload a single eICR/RR pair as a .zip file.</span>
            </p>
            {env === 'demo' || env === 'local' ? <UploadFileWarning /> : null}
            <div>
              <UploadZipFile
                onClick={onClickCustomFile}
                selectedFile={selectedFile}
                onSelectedFileChange={onSelectedFileChange}
              />
            </div>
          </div>
        </Content>
      </Container>
      <Container color="blue">
        <Content className="flex items-start gap-6">
          <img className="px-3 py-5" src={ForwardSvg} alt="" />
          <div className="flex flex-col gap-10">
            <p className="flex flex-col gap-2 text-black">
              <span className="font-bold">Don't have a file ready?</span>
              <span>You can try out eCR Refiner with our test file.</span>
            </p>
            <div className="flex flex-col items-start gap-4 md:flex-row md:items-center">
              <Button
                variant="secondary"
                onClick={() => void onClickSampleFile()}
              >
                Use test file
              </Button>
              <a
                className="text-blue-cool-60 font-bold hover:underline"
                href="/api/v1/demo/download"
                download
              >
                Download test file
              </a>
            </div>
          </div>
        </Content>
      </Container>
    </div>
  );
}

interface UploadZipFile {
  onClick: () => Promise<void>;
  selectedFile: RunTestProps['selectedFile'];
  onSelectedFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
}

const autoFocus = (element: HTMLElement | null) => element?.focus();

function UploadZipFile({
  onClick,
  selectedFile,
  onSelectedFileChange,
}: UploadZipFile) {
  const inputRef = useRef<HTMLInputElement>(null);

  const labelStyling = classNames({
    'usa-button !bg-violet-warm-60 hover:!bg-violet-warm-70': !selectedFile,
    'text-violet-warm-60 hover:text-violet-warm-70 justify-start font-bold hover:underline hover:cursor-pointer !text-blue-cool-60':
      selectedFile,
  });

  return (
    <div className="flex flex-col items-start gap-3">
      <input
        ref={inputRef}
        id="zip-upload"
        data-testid="zip-upload-input"
        type="file"
        className="hidden"
        accept=".zip"
        onChange={onSelectedFileChange}
      />
      <div className="flex flex-col gap-6">
        {selectedFile ? <p>{selectedFile.name}</p> : null}
        <div className="flex items-center gap-4">
          {selectedFile ? (
            <Button ref={autoFocus} onClick={() => void onClick()}>
              Refine .zip file
            </Button>
          ) : null}
          <label
            htmlFor="zip-upload"
            className={labelStyling}
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                inputRef.current?.click();
              }
            }}
          >
            {selectedFile ? 'Change file' : 'Upload .zip file'}
          </label>
        </div>
      </div>
    </div>
  );
}

function UploadFileWarning() {
  return (
    <div className="bg-state-error-lighter rounded p-4">
      <p className="text-state-error-dark flex flex-col gap-3">
        <span className="flex items-center gap-2">
          <Icon.Warning
            className="[&_path]:fill-state-error shrink-0"
            aria-label="Warning"
          />
          <span>This environment is not approved to handle PHI/PII.</span>
        </span>
        <span className="font-bold">
          Do not upload files that contain PHI/PII.
        </span>
      </p>
    </div>
  );
}
