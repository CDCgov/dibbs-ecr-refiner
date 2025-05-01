import { LandingPageLink } from '../../components/LandingPageLink';
import { Success } from './Success';
import { ReportableConditions } from './ReportableConditions';
import { Error } from './Error';
import { RunTest } from './RunTest';
import { useDemoUpload } from '../../services/demo';
import { useEffect, useState } from 'react';

export default function Demo() {
  const [isComplete, setIsComplete] = useState(false);
  const {
    data,
    resetData,
    refetch: runTest,
    isError,
    isSuccess,
  } = useDemoUpload();

  useEffect(() => {
    async function reset() {
      await resetData();
    }
    reset();
  }, []);

  return (
    <main className="flex min-w-screen flex-col gap-20 px-20 py-10">
      <LandingPageLink />
      <div className="flex flex-col items-center justify-center gap-6">
        {!data && <RunTest onClick={runTest} />}
        {data && isSuccess && !isComplete && (
          <ReportableConditions
            conditions={['Chlamydia trachomatis infection']}
            onClick={() => setIsComplete(true)}
          />
        )}
        {isComplete && (
          <Success
            unrefinedEicr="<data>unrefined</data>"
            refinedEicr="<data>refined</data>"
          />
        )}
        {isError && <Error />}
      </div>
    </main>
  );
}
