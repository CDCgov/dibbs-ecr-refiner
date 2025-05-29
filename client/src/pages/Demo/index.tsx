import { LandingPageLink } from '../../components/LandingPageLink';
import { Success } from './Success';
import { ReportableConditions } from './ReportableConditions';
import { Error } from './Error';
import { RunTest } from './RunTest';
import { useState } from 'react';
import { DemoUploadResponse, uploadDemoFile } from '../../services/demo';

type View = 'run-test' | 'reportable-conditions' | 'success' | 'error';

/**
 * TODO: Remove this later when `additionalSampleConditions` is deleted.
 */
type SampleReportableConditions = Pick<DemoUploadResponse, 'conditions'>;

export default function Demo() {
  const [view, setView] = useState<View>('run-test');
  const [uploadResponse, setUploadResponse] =
    useState<DemoUploadResponse | null>(null);

  /**
   * TODO: Remove this later. See description below.
   *
   * This is mock data that gets appended to the response coming from the API when
   * `runTest()` is called. This is used to show how we'll switch between conditions
   * using the dropdown on the Success page.
   */
  const additionalSampleConditions: SampleReportableConditions = {
    conditions: [
      {
        code: '101',
        display_name: 'COVID-19',
        refined_eicr: '<refined>COVID REFINED</refined>',
        unrefined_eicr: '<unrefined>COVID UNREFINED</unrefined>',
        stats: ['eCR file size reduced by 14%'],
      },
      {
        code: '102',
        display_name: 'RSV',
        refined_eicr: '<refined>RSV REFINED</refined>',
        unrefined_eicr: '<unrefined>RSV UNREFINED</unrefined>',
        stats: ['eCR file size reduced by 37%'],
      },
      {
        code: '103',
        display_name: 'Influenza',
        refined_eicr: '<refined>INFLUENZA REFINED</refined>',
        unrefined_eicr: '<unrefined>INFLUENZA UNREFINED</unrefined>',
        stats: ['eCR file size reduced by 55%'],
      },
    ],
  };

  async function runTest() {
    try {
      const resp = await uploadDemoFile();

      /**
       * TODO: Remove this when `additionalSampleConditions` is removed.
       * Update line below to be `setUploadResponse(resp)`.
       */
      const modifiedResponse: DemoUploadResponse = {
        refined_download_token: resp.refined_download_token,
        conditions: [
          ...resp.conditions,
          ...additionalSampleConditions.conditions,
        ],
      };

      setUploadResponse(modifiedResponse);
      setView('reportable-conditions');
    } catch (e) {
      console.error(e);
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
            downloadToken={uploadResponse.refined_download_token}
          />
        )}
        {view === 'error' && <Error onClick={reset} />}
      </div>
    </main>
  );
}
