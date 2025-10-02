import { Success } from './Success';
import { Error as ErrorScreen } from './Error';
import { RunTest } from './RunTest';
import { useState } from 'react';
import { useUploadEcr } from '../../api/demo/demo';
import { Title } from '../../components/Title';
import { ReportableConditionsResults } from './ReportableConditionsResults';

type View = 'run-test' | 'reportable-conditions' | 'success' | 'error';

export default function Demo() {
  const [view, setView] = useState<View>('run-test');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const {
    uploadZip,
    data: response,
    errorMessage,
    isPending,
    resetState,
  } = useZipUpload();

  async function runTestWithCustomFile() {
    try {
      await uploadZip(selectedFile);
      setView('reportable-conditions');
    } catch {
      setView('error');
    }
  }

  async function runTestWithSampleFile() {
    try {
      await uploadZip(null);
      setView('reportable-conditions');
    } catch {
      setView('error');
    }
  }

  function reset() {
    setView('run-test');
    resetState();
  }

  if (isPending) return 'Loading...';

  return (
    <div className="flex px-10 md:px-20">
      <div className="flex flex-col gap-10 py-10">
        {view === 'run-test' && (
          <RunTest
            onClickSampleFile={runTestWithSampleFile}
            onClickCustomFile={runTestWithCustomFile}
            selectedFile={selectedFile}
            setSelectedFile={setSelectedFile}
          />
        )}
        {view === 'reportable-conditions' && response?.data && (
          <>
            <Title>Test Refiner</Title>
            <ReportableConditionsResults
              refined_condition_names={response.data.refined_conditions.map(
                (c) => c.display_name
              )}
              conditions_without_config_names={
                response.data.conditions_without_matching_configs
              }
              startOver={reset}
              goToSuccessScreen={() => setView('success')}
            />
          </>
        )}
        {view === 'success' && response?.data && (
          <Success
            refined_conditions={response.data.refined_conditions}
            unrefined_eicr={response.data.unrefined_eicr}
            refined_download_url={response.data.refined_download_url}
          />
        )}
        {view === 'error' && (
          <ErrorScreen message={errorMessage} onClick={reset} />
        )}
      </div>
    </div>
  );
}

function useZipUpload() {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const {
    mutateAsync,
    data,
    isError,
    isPending,
    reset: resetState,
  } = useUploadEcr({
    mutation: {
      onError: (error) => {
        const rawError = error.response?.data;

        const message = Array.isArray(rawError?.detail)
          ? rawError.detail.map((d) => d.msg).join(' ')
          : rawError?.detail || 'Upload failed. Please try again.';
        setErrorMessage(message);
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
