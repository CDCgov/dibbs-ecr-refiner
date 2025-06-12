import { Button } from '../../components/Button';
import { Container, Content } from './Layout';
import UploadSvg from '../../assets/upload.svg';
import { ChangeEvent } from 'react';
import classNames from 'classnames';

interface RunTestProps {
  onClickCustomFile: () => Promise<void>;
  onClickSampleFile: () => Promise<void>;
  selectedFile: File | null;
  onSelectedFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
}
export function RunTest({
  onSelectedFileChange,
  onClickCustomFile,
  selectedFile,
  onClickSampleFile,
}: RunTestProps) {
  return (
    <Container color="blue">
      <Content className="flex gap-3">
        <img src={UploadSvg} alt="" className="p-3" />
        <div className="flex flex-col items-center gap-6">
          <p className="flex max-w-[500px] flex-col gap-4 text-center font-normal text-black">
            For this demo, we've provided a synthetic eICR/RR pair to test the
            Refiner that contains two reportable conditions.
            <span>
              The "Run test" button below will upload the test files to the
              Refiner.
            </span>
          </p>
          <UploadZipFile
            onClick={onClickCustomFile}
            selectedFile={selectedFile}
            onSelectedFileChange={onSelectedFileChange}
          />
          <Button onClick={onClickSampleFile}>Run test</Button>
          <a
            className="justify-start font-bold text-blue-300 hover:underline"
            href="/api/v1/demo/download"
            download
          >
            Download test file
          </a>
        </div>
      </Content>
    </Container>
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
            <Button onClick={onClick}>Upload .zip file</Button>
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
