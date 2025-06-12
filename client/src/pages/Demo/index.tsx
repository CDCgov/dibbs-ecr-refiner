import { LandingPageLink } from '../../components/LandingPageLink';
import { Success } from './Success';
import { ReportableConditions } from './ReportableConditions';
import { Error } from './Error';
import { RunTest } from './RunTest';
import { ChangeEvent, useState } from 'react';
import {
  DemoUploadResponse,
  uploadCustomZipFile,
  uploadDemoFile,
} from '../../services/demo';

type View = 'run-test' | 'reportable-conditions' | 'success' | 'error';

export default function Demo() {
  const [view, setView] = useState<View>('run-test');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
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
      setView('reportable-conditions');
    } catch {
      setUploadResponse(null);
      setView('error');
    }
  }

  async function runTestWithSampleFile() {
    try {
      const resp = await uploadDemoFile();
      setUploadResponse(resp);
      setView('reportable-conditions');
    } catch {
      setUploadResponse(null);
      setView('error');
    }
  }

  function reset() {
    setView('run-test');
    setUploadResponse(null);
  }

  return (
    <main className="flex min-w-screen flex-col gap-20 px-20 py-10">
      <LandingPageLink />
      <div className="flex flex-col items-center justify-center gap-6">
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
        {view === 'error' && <Error onClick={reset} />}
      </div>
    </main>
  );
}
