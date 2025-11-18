import { Button } from '../../components/Button';
import { Container, Content } from './Layout';
import UploadSvg from '../../assets/upload.svg';
import { ChangeEvent, useRef } from 'react';
import { WarningIcon } from '../../components/WarningIcon';
import { useGetEnv } from '../../hooks/useGetEnv';
import classNames from 'classnames';
import { ExternalLink } from '../../components/ExternalLink';

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
    <>
      <div className="flex flex-col gap-6 xl:flex-row">
        <Container className="flex-1" color="white">
          <Content className="flex items-center gap-6">
            <img className="px-3 py-1" src={UploadSvg} alt="" />
            <div className="flex flex-col items-center gap-10">
              <p className="flex flex-col items-center gap-2 text-black">
                <span className="font-bold">
                  Want to refine your own eCR file?
                </span>
                <span>Please upload a single eICR/RR pair as a .zip file.</span>
              </p>
              {env !== 'prod' ? <UploadFileWarning /> : null}
              <div>
                <UploadZipFile
                  onClick={onClickCustomFile}
                  selectedFile={selectedFile}
                  onSelectedFileChange={onSelectedFileChange}
                  onClickSampleFile={onClickSampleFile}
                />
              </div>
            </div>
          </Content>
        </Container>
      </div>

      <div className="mt-6 text-center">
        <span>
          To download test files for some conditions you can{' '}
          <ExternalLink href="https://github.com/CDCgov/dibbs-ecr-refiner/tree/main/refiner/scripts/data/jurisdiction-packages/jurisdiction_sample_data">
            visit eCR Refiner's repository
          </ExternalLink>
        </span>
      </div>
    </>
  );
}

interface UploadZipFile {
  onClick: () => Promise<void>;
  selectedFile: RunTestProps['selectedFile'];
  onSelectedFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onClickSampleFile: () => Promise<void>;
}

const autoFocus = (element: HTMLElement | null) => element?.focus();

function UploadZipFile({
  onClick,
  selectedFile,
  onSelectedFileChange,
  onClickSampleFile,
}: UploadZipFile) {
  const env = useGetEnv();

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
        {/* render an autoupload file for QoL in local dev */}
        {env === 'local' ? (
          <Button variant="secondary" onClick={() => void onClickSampleFile()}>
            Use test file <br />
            (local only)
          </Button>
        ) : null}
      </div>
    </div>
  );
}

function UploadFileWarning() {
  return (
    <div className="bg-state-error-lighter rounded p-4">
      <p className="text-state-error-dark flex flex-col gap-3">
        <span className="flex items-center gap-2">
          <WarningIcon aria-label="Warning" />
          <span>This environment is not approved to handle PHI/PII.</span>
        </span>
        <span className="text-center font-bold">
          Do not upload files that contain PHI/PII.
        </span>
      </p>
    </div>
  );
}
