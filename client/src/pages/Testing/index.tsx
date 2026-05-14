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

  const {
    configurationsResponse,
    fetchConfigurations,
    resetConfigurations,
    errorMessage: configurationsErrorMessage,
  } = useDiscoveredConfigurations();

  const {
    refinementResponse,
    runRefinement,
    resetRefinement,
    errorMessage: refinementErrorMessage,
  } = useRunRefinement();

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
    resetRefinement();
  }

  function executeTest(
    configIds: string[],
    conditionsWithoutConfigIds: string[]
  ) {
    return async () => {
      try {
        await runRefinement(
          selectedFile,
          configIds,
          conditionsWithoutConfigIds
        );
        setStatus('success');
      } catch {
        setStatus('error');
      }
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
          refinementResponse?.data && (
            <Success
              refined_conditions={refinementResponse.data.refined_conditions}
              unrefined_eicr={refinementResponse.data.unrefined_eicr}
              refined_download_key={
                refinementResponse.data.refined_download_key
              }
            />
          )}
        {status === 'error' && (
          <FileUploadWarning
            errorMessage={
              (refinementErrorMessage || configurationsErrorMessage) ?? ''
            }
            reset={reset}
          />
        )}
      </div>
    </div>
  );
}

function useDiscoveredConfigurations() {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const formatError = useApiErrorFormatter();

  const {
    data: configurationsResponse,
    mutateAsync: fetchConfigurations,
    reset: resetConfigurations,
  } = useDiscoverConfigurations({
    mutation: {
      onError: (error) => {
        setErrorMessage(formatError(error));
      },
    },
  });

  return {
    configurationsResponse,
    fetchConfigurations,
    resetConfigurations,
    errorMessage,
    setErrorMessage,
  };
}

function useRunRefinement() {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const formatError = useApiErrorFormatter();
  const {
    mutateAsync,
    data: refinementResponse,
    reset: resetRefinement,
  } = useUploadEcr({
    mutation: {
      onError: (error) => {
        setErrorMessage(formatError(error));
      },
    },
  });

  async function runRefinement(
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
    refinementResponse,
    resetRefinement,
    runRefinement,
    errorMessage,
  };
}
