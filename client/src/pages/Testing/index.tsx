// import { LandingPageLink } from '../../components/LandingPageLink';
import { Success } from './Success';
import { ReportableConditions } from './ReportableConditions';
import { Error } from './Error';
import { RunTest } from './RunTest';
import { ChangeEvent, useState } from 'react';
import {
  ApiUploadError,
  DemoUploadResponse,
  uploadCustomZipFile,
  uploadDemoFile,
} from '../../services/demo';

type View = 'run-test' | 'reportable-conditions' | 'success' | 'error';

export default function Demo() {
  const [view, setView] = useState<View>('run-test');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [uploadResponse, setUploadResponse] =
    useState<DemoUploadResponse | null>(null);

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

  async function runTestWithCustomFile() {
    try {
      const resp = await uploadCustomZipFile(selectedFile);
      setUploadResponse(resp);
      setServerError(null);
      setView('reportable-conditions');
    } catch (e: unknown) {
      setUploadResponse(null);
      handleError(e);
      setView('error');
    }
  }

  async function runTestWithSampleFile() {
    try {
      const resp = await uploadDemoFile();
      setUploadResponse(resp);
      setServerError(null);
      setView('reportable-conditions');
    } catch (e: unknown) {
      setUploadResponse(null);
      handleError(e);
      setView('error');
    }
  }

  function handleError(error: unknown) {
    if (error instanceof ApiUploadError) {
      setServerError(error.message);
    } else {
      setServerError('Unknown error occurred. Please try again.');
    }
  }

  function reset() {
    setView('run-test');
    setUploadResponse(null);
  }

  return (
    <div className="flex justify-center px-10 md:px-20">
      <div className="flex flex-col gap-10 py-10">
        {view === 'run-test' && (
          <RunTest
            onClickSampleFile={runTestWithSampleFile}
            onClickCustomFile={runTestWithCustomFile}
            selectedFile={selectedFile}
            onSelectedFileChange={onSelectedFileChange}
          />
        )}
        {view === 'reportable-conditions' && uploadResponse && (
          <ReportableConditions
            conditionNames={uploadResponse.conditions.map(
              (c) => c.display_name
            )}
            onClick={() => setView('success')}
          />
        )}
        {view === 'success' && uploadResponse && (
          <Success
            conditions={uploadResponse.conditions}
            unrefinedEicr={uploadResponse.unrefined_eicr}
            downloadToken={uploadResponse.refined_download_token}
          />
        )}
        {view === 'error' && <Error message={serverError} onClick={reset} />}
      </div>
    </div>
  );
}
