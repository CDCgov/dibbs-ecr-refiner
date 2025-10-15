import { Success } from './Success';
import { RunTest } from './RunTest';
import { useState } from 'react';
import { useUploadEcr } from '../../api/demo/demo';
import { Title } from '../../components/Title';
import { ReportableConditionsResults } from './ReportableConditionsResults';
import { Uploading } from './Uploading';
import FileUploadWarning from '../../components/FileUploadWarning';

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

  console.log(errorMessage);

  return (
    <div className="flex px-10 md:px-20">
      <div className="flex flex-col gap-10 py-10">
        {status === 'run-test' && (
          <>
            <Title>Test Refiner</Title>
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
            <Title>Test Refiner</Title>
            <Uploading />
          </>
        )}

        {status === 'reportable-conditions' && response?.data && (
          <>
            <Title>Test Refiner</Title>
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
