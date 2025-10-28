import { Success } from './Success';
import { RunTest } from './RunTest';
import { TestRefinerDescription } from './TestRefinerDescription';

import { useState } from 'react';
import { useUploadEcr } from '../../api/demo/demo';
import { ReportableConditionsResults } from './ReportableConditionsResults';
import { Uploading } from './Uploading';
import FileUploadWarning from '../../components/FileUploadWarning';
import { useApiErrorFormatter } from '../../hooks/useErrorFormatter';

type Status =
  | 'run-test'
  | 'reportable-conditions'
  | 'success'
  | 'error'
  | 'pending';

export default function Demo() {
  const [status, setStatus] = useState<Status>('run-test');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const {
    uploadZip,
    data: response,
    errorMessage,
    resetState,
  } = useZipUpload();

  async function runTestWithCustomFile() {
    try {
      setStatus('pending');
      await uploadZip(selectedFile);
      setStatus('reportable-conditions');
    } catch {
      setStatus('error');
    }
  }

  async function runTestWithSampleFile() {
    try {
      setStatus('pending');
      await uploadZip(null);
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
              matchedConditions={response.data.refined_conditions.map(
                (c) => c.display_name
              )}
              unmatchedConditions={
                response.data.conditions_without_matching_configs
              }
              startOver={reset}
              goToSuccessScreen={() => setStatus('success')}
            />
          </>
        )}
        {status === 'success' && response?.data && (
          <Success
            refined_conditions={response.data.refined_conditions}
            unrefined_eicr={response.data.unrefined_eicr}
            refined_download_url={response.data.refined_download_url}
          />
        )}
        {status === 'error' && (
          <FileUploadWarning errorMessage={errorMessage ?? ''} reset={reset} />
        )}
      </div>
    </div>
  );
}

function useZipUpload() {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const formatError = useApiErrorFormatter();
  const {
    mutateAsync,
    data,
    isError,
    isPending,
    reset: resetState,
  } = useUploadEcr({
    mutation: {
      onError: (error) => {
        setErrorMessage(formatError(error));
      },
    },
  });

  async function uploadZip(selectedFile: File | null) {
    setErrorMessage(null);

    const resp = await mutateAsync({ data: { uploaded_file: selectedFile } });

    return resp;
  }

  return {
    uploadZip,
    data,
    errorMessage,
    isError,
    isPending,
    resetState,
  };
}
