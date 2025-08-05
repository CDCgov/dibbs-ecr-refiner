import { Success } from './Success';
import { ReportableConditions } from './ReportableConditions';
import { Error as ErrorScreen } from './Error';
import { RunTest } from './RunTest';
import { ChangeEvent, useState } from 'react';
import { useUploadEcr } from '../../api/demo/demo';

type View = 'run-test' | 'reportable-conditions' | 'success' | 'error';

export default function Demo() {
  const [view, setView] = useState<View>('run-test');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const { uploadZip, data, errorMessage, isPending, resetState } =
    useZipUpload();

  function onSelectedFileChange(e: ChangeEvent<HTMLInputElement>) {
    if (e.target.files) {
      const file = e.target.files[0];
      if (file.name.endsWith('.zip')) {
        setSelectedFile(file);
      } else {
        console.error('No file input or incorrect file type.');
        setSelectedFile(null);
      }
    }
  }

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
    <div className="flex justify-center px-10 md:px-20">
      <div className="flex flex-col gap-10 py-10">
        {view === 'run-test' && (
          <RunTest
            onClickSampleFile={runTestWithSampleFile}
            onClickCustomFile={runTestWithCustomFile}
            selectedFile={selectedFile}
            onSelectedFileChange={onSelectedFileChange}
          />
        )}
        {view === 'reportable-conditions' && data?.data && (
          <ReportableConditions
            conditionNames={data?.data.conditions.map((c) => c.display_name)}
            onClick={() => setView('success')}
          />
        )}
        {view === 'success' && data?.data && (
          <Success
            conditions={data?.data.conditions}
            unrefinedEicr={data?.data.unrefined_eicr}
            downloadToken={data?.data.refined_download_token}
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
