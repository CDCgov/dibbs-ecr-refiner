import { LandingPageLink } from '../../components/LandingPageLink';
import { Success } from './Success';
import { ReportableConditions } from './ReportableConditions';
import { Error } from './Error';
import { RunTest } from './RunTest';
import { useState } from 'react';
import { DemoUploadResponse, uploadDemoFile } from '../../services/demo';

type View = 'run-test' | 'reportable-conditions' | 'success' | 'error';

export default function Demo() {
  const [view, setView] = useState<View>('run-test');
  const [uploadResponse, setUploadResponse] =
    useState<DemoUploadResponse | null>(null);

  async function runTest() {
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
        {view === 'run-test' && <RunTest onClick={runTest} />}
        {view === 'reportable-conditions' && uploadResponse && (
          // TODO: provide list of reportable conditions from backend
          <ReportableConditions
            conditions={['Chlamydia trachomatis infection']}
            onClick={() => setView('success')}
          />
        )}
        {view === 'success' && uploadResponse && (
          <Success
            unrefinedEicr={uploadResponse.unrefined_eicr}
            refinedEicr={uploadResponse.refined_eicr}
            stats={uploadResponse.stats}
            downloadToken={uploadResponse.refined_download_token}
          />
        )}
        {view === 'error' && <Error onClick={reset} />}
      </div>
    </main>
  );
}
