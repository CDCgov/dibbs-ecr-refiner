import { RunTest } from './RunTest';
import { TestRefinerDescription } from './TestRefinerDescription';
import { useState } from 'react';
import { useDiscoverConfigurations, useUploadEcr } from '../../api/demo/demo';
import { ReportableConditionsResults } from './ReportableConditionsResults';
import { Uploading } from './Uploading';
import { useApiErrorFormatter } from '../../hooks/useErrorFormatter';
import { FileUploadWarning } from '@components/FileUploadWarning';
import { Success } from './Success';

type Status =
  | 'run-test'
  | 'reportable-conditions'
  | 'success'
  | 'error'
  | 'pending';

export function Testing() {
  const [status, setStatus] = useState<Status>('run-test');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const formatError = useApiErrorFormatter();
  const [configurationsErrorMessage, setConfigurationsErrorMessage] = useState<
    string | null
  >(null);

  const {
    data: configurationsResponse,
    mutateAsync: fetchConfigurations,
    reset: resetConfigurations,
  } = useDiscoverConfigurations({
    mutation: {
      onError: (error) => {
        setConfigurationsErrorMessage(formatError(error));
      },
    },
  });

  const {
    data: ecrUploadResponse,
    errorMessage: ecrUploadErrorMessage,
    resetState: resetEcrUploadState,
    uploadZip,
  } = useZipUpload();

  async function runTestWithCustomFile() {
    try {
      setStatus('pending');
      await fetchConfigurations({
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
      await fetchConfigurations({
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
    resetConfigurations();
    resetEcrUploadState();
  }

  function executeTest(
    configIds: string[],
    conditionsWithoutConfigIds: string[]
  ) {
    return async () => {
      await uploadZip(selectedFile, configIds, conditionsWithoutConfigIds);
      setStatus('success');
    };
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

        {status === 'reportable-conditions' && configurationsResponse?.data && (
          <>
            <TestRefinerDescription />
            <ReportableConditionsResults
              configurationGroups={configurationsResponse?.data.groups}
              startOver={reset}
              runRefinement={executeTest}
            />
          </>
        )}
        {status === 'success' &&
          configurationsResponse?.data &&
          ecrUploadResponse?.data && (
            <Success
              refined_conditions={ecrUploadResponse.data.refined_conditions}
              unrefined_eicr={ecrUploadResponse.data.unrefined_eicr}
              refined_download_key={ecrUploadResponse.data.refined_download_key}
            />
          )}
        {status === 'error' && (
          <FileUploadWarning
            errorMessage={
              (ecrUploadErrorMessage || configurationsErrorMessage) ?? ''
            }
            reset={reset}
          />
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

  async function uploadZip(
    selectedFile: File | null,
    configIds: string[],
    unconfiguredConditionIds: string[]
  ) {
    setErrorMessage(null);

    const resp = await mutateAsync({
      data: {
        uploaded_file: selectedFile,
        body: JSON.stringify({
          configuration_ids: configIds,
          unconfigured_condition_ids: unconfiguredConditionIds,
        }),
      },
    });

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
