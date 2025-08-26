import { Button } from '../../components/Button';
import { Container, Content } from './Layout';
import UploadSvg from '../../assets/upload.svg';
import ForwardSvg from '../../assets/forward.svg';
import { Title } from '../../components/Title';
import { ChangeEvent } from 'react';
import classNames from 'classnames';
import { Icon } from '@trussworks/react-uswds';

interface RunTestProps {
  onClickCustomFile: () => Promise<void>;
  onClickSampleFile: () => Promise<void>;
  selectedFile: File | null;
  onSelectedFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
}
export function RunTest({
  onSelectedFileChange,
  onClickSampleFile,
  onClickCustomFile,
  selectedFile,
}: RunTestProps) {
  return (
    <div className="flex flex-col gap-12">
      <Title>Test filter</Title>
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
              <UploadFileWarning />
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
              <div className="flex flex-col items-center gap-4 md:flex-row">
                <Button
                  variant="secondary"
                  onClick={() => void onClickSampleFile()}
                >
                  Use test file
                </Button>
                <a
                  className="text-violet-warm-60 hover:text-violet-warm-70 justify-start font-bold hover:underline"
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
    </div>
  );
}

interface UploadZipFile {
  onClick: () => Promise<void>;
  selectedFile: RunTestProps['selectedFile'];
  onSelectedFileChange: RunTestProps['onSelectedFileChange'];
}

function UploadZipFile({
  onClick,
  selectedFile,
  onSelectedFileChange,
}: UploadZipFile) {
  const labelStyling = classNames({
    'usa-button !bg-violet-warm-60 hover:!bg-violet-warm-70': !selectedFile,
    'text-violet-warm-60 hover:text-violet-warm-70 justify-start font-bold hover:underline hover:cursor-pointer':
      selectedFile,
  });

  return (
    <div className="flex flex-col items-start gap-3">
      <input
        id="zip-upload"
        type="file"
        className="hidden"
        accept=".zip"
        onChange={onSelectedFileChange}
      />
      <div className="flex flex-col gap-6">
        {selectedFile ? <p>{selectedFile.name}</p> : null}
        <div className="flex items-center gap-4">
          {selectedFile ? (
            <Button onClick={() => void onClick()}>Upload .zip file</Button>
          ) : null}
          <label className={labelStyling} htmlFor="zip-upload">
            {selectedFile ? (
              <span>Change file</span>
            ) : (
              <span>Select .zip file</span>
            )}
          </label>
        </div>
      </div>
    </div>
  );
}

function UploadFileWarning() {
  return (
    <div className="rounded bg-[#FFF3F2] p-4">
      <p className="flex flex-col gap-3 text-[#B50909]">
        <span className="flex items-center gap-2">
          <Icon.Warning className="shrink-0 [&_path]:fill-[#FB5A47]" />
          <span>This environment is not approved to handle PHI/PII.</span>
        </span>
        <span className="font-bold">
          Do not upload files that contain PHI/PII.
        </span>
      </p>
    </div>
  );
}
