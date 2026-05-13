import { Success } from './Success';
import { RunTest } from './RunTest';
import { TestRefinerDescription } from './TestRefinerDescription';
import { useState } from 'react';
import { useDiscoverConfigurations, useUploadEcr } from '../../api/demo/demo';
import { ReportableConditionsResults } from './ReportableConditionsResults';
import { Uploading } from './Uploading';
import { FileUploadWarning } from '@components/FileUploadWarning';
import { useApiErrorFormatter } from '../../hooks/useErrorFormatter';

type Status =
  | 'run-test'
  | 'reportable-conditions'
  | 'success'
  | 'error'
  | 'pending';

export function Testing() {
  const [status, setStatus] = useState<Status>('run-test');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const { data, mutateAsync } = useDiscoverConfigurations();

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
      // TODO: move this later
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
      await uploadZip(null);
      // TODO: move this later
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

        {status === 'reportable-conditions' && response?.data && data?.data && (
          <>
            <TestRefinerDescription />
            <ReportableConditionsResults
              configurationGroups={data?.data.groups}
              unmatchedConditions={
                response.data.conditions_without_matching_configs
              }
              inactiveConditions={
                response.data.conditions_without_active_configs
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
            refined_download_key={response.data.refined_download_key}
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
