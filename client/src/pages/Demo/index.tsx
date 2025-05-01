import { LandingPageLink } from '../../components/LandingPageLink';
import { Success } from './Success';
import { ReportableConditions } from './ReportableConditions';
import { Error } from './Error';
import { RunTest } from './RunTest';
import { useState } from 'react';
import {
  ApiUploadError,
  DemoUploadResponse,
  uploadDemoFile,
} from '../../services/demo';

type View = 'run-test' | 'reportable-conditions' | 'success' | 'error';

export default function Demo() {
  const [view, setView] = useState<View>('run-test');
  const [uploadResponse, setUploadResponse] =
    useState<DemoUploadResponse | null>(null);
  const [uploadError, setUploadError] = useState<Error | null>(null);

  async function runTest() {
    try {
      const resp = await uploadDemoFile();
      setUploadResponse(resp);
      setUploadError(null);
      setView('reportable-conditions');
    } catch (e: unknown) {
      setUploadResponse(null);
      setView('error');
      if (e instanceof ApiUploadError) {
        setUploadError(e);
      }
    }
  }

  function reset() {
    setView('run-test');
    setUploadResponse(null);
    setUploadError(null);
  }

  return (
    <main className="flex min-w-screen flex-col gap-20 px-20 py-10">
      <LandingPageLink />
      <div className="flex flex-col items-center justify-center gap-6">
        {view === 'run-test' && <RunTest onClick={runTest} />}
        {uploadResponse && view === 'reportable-conditions' && (
          <ReportableConditions
            conditions={['Chlamydia trachomatis infection']}
            onClick={() => setView('success')}
          />
        )}
        {uploadResponse && view === 'success' && (
          <Success
            unrefinedEicr={uploadResponse.unrefined_eicr}
            refinedEicr={uploadResponse.refined_eicr}
          />
        )}
        {uploadError && <Error onClick={reset} />}
      </div>
    </main>
  );
}
