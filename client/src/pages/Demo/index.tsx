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
    <div className="flex justify-center px-10 md:px-20">
      <div className="flex flex-col gap-10 py-10">
        <LandingPageLink />
        {view === 'run-test' && <RunTest onClick={runTest} />}
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
    </div>
  );
}
