import { RunTest } from './RunTest';
import { TestRefinerDescription } from './TestRefinerDescription';
import { useState } from 'react';
import { useDiscoverConfigurations } from '../../api/demo/demo';
import { ReportableConditionsResults } from './ReportableConditionsResults';
import { Uploading } from './Uploading';

type Status =
  | 'run-test'
  | 'reportable-conditions'
  | 'success'
  | 'error'
  | 'pending';

export function Testing() {
  const [status, setStatus] = useState<Status>('run-test');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const {
    data: response,
    mutateAsync,
    reset: resetState,
  } = useDiscoverConfigurations();

  async function runTestWithCustomFile() {
    try {
      setStatus('pending');
      await mutateAsync({
        data: {
          uploaded_file: selectedFile,
        },
      });
      setStatus('reportable-conditions');
    } catch {
      setStatus('error');
    }
  }

  async function runTestWithSampleFile() {
    try {
      setStatus('pending');
      await mutateAsync({
        data: {
          uploaded_file: null,
        },
      });
      setStatus('reportable-conditions');
    } catch {
      setStatus('error');
    }
  }

  function reset() {
    setStatus('run-test');
    resetState();
  }

  return (
    <div className="flex px-10 md:px-20">
      <div className="flex flex-1 flex-col py-10">
        {status === 'run-test' && (
          <>
            <TestRefinerDescription />
            <RunTest
              onClickSampleFile={runTestWithSampleFile}
              onClickCustomFile={runTestWithCustomFile}
              selectedFile={selectedFile}
              setSelectedFile={setSelectedFile}
            />
          </>
        )}

        {status === 'pending' && (
          <>
            <TestRefinerDescription />
            <Uploading />
          </>
        )}

        {status === 'reportable-conditions' && response?.data && (
          <>
            <TestRefinerDescription />
            <ReportableConditionsResults
              configurationGroups={response?.data.groups}
              startOver={reset}
              goToSuccessScreen={() => setStatus('success')}
            />
          </>
        )}
        {/* {status === 'success' && response?.data && (
          <Success
            refined_conditions={response.data.refined_conditions}
            unrefined_eicr={response.data.unrefined_eicr}
            refined_download_key={response.data.refined_download_key}
          />
        )}
        {status === 'error' && (
          <FileUploadWarning errorMessage={errorMessage ?? ''} reset={reset} />
        )} */}
      </div>
    </div>
  );
}
