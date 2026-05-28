import { RunSimulation } from './RunSimulation';
import { useState } from 'react';
import {
  useDiscoverConfigurations,
  useUploadEcr,
} from '../../api/simulator/simulator';
import { ReportableConditionsResults } from './ReportableConditionsResults';
import { Uploading } from './Uploading';
import { useApiErrorFormatter } from '../../hooks/useErrorFormatter';
import { FileUploadWarning } from '@components/FileUploadWarning';
import { Success } from './Success';
import { Title } from '@components/Title';

type Status =
  | 'run-simulator'
  | 'reportable-conditions'
  | 'success'
  | 'error'
  | 'pending';

export function Simulator() {
  const [status, setStatus] = useState<Status>('run-simulator');
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

  async function runSimulationWithCustomFile() {
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

  async function runSimulationWithSampleFile() {
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
    setStatus('run-simulator');
    resetConfigurations();
    resetRefinement();
  }

  function executeSimulator(
    configIds: string[],
    conditionsWithoutConfigIds: string[],
    uncheckedConditionIds: string[]
  ) {
    return async () => {
      try {
        setStatus('pending');
        await runRefinement(
          selectedFile,
          configIds,
          conditionsWithoutConfigIds,
          uncheckedConditionIds
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
        {status === 'run-simulator' && (
          <>
            <SimulateRefinerDescription />
            <RunSimulation
              onClickSampleFile={runSimulationWithSampleFile}
              onClickCustomFile={runSimulationWithCustomFile}
              selectedFile={selectedFile}
              setSelectedFile={setSelectedFile}
            />
          </>
        )}

        {status === 'pending' && (
          <>
            <SimulateRefinerDescription />
            <Uploading />
          </>
        )}

        {status === 'reportable-conditions' && configurationsResponse?.data && (
          <>
            <SimulateRefinerDescription />
            <ReportableConditionsResults
              configurationSets={configurationsResponse.data.sets}
              startOver={reset}
              runRefinement={executeSimulator}
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
    unconfiguredConditionIds: string[],
    uncheckedConditionIds: string[]
  ) {
    setErrorMessage(null);

    const resp = await mutateAsync({
      data: {
        uploaded_file: selectedFile,
        body: JSON.stringify({
          configuration_ids: configIds,
          unconfigured_condition_ids: unconfiguredConditionIds,
          unused_condition_ids: uncheckedConditionIds,
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

function SimulateRefinerDescription() {
  return (
    <div className="mb-6">
      <div className="flex flex-col gap-2">
        <Title>Simulate Refiner</Title>
        <p>
          This module allows you to simulate how the Refiner would work in
          production for a zipped eICR/RR pair input based on the reportable
          conditions your jurisdiction has configured.
        </p>
      </div>
    </div>
  );
}
