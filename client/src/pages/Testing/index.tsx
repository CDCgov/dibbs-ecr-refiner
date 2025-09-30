import { Success } from './Success';
import { ReportableConditions } from './ReportableConditions';
import { Error as ErrorScreen } from './Error';
import { RunTest } from './RunTest';
import { useState } from 'react';
import { useUploadEcr } from '../../api/demo/demo';
import { Title } from '../../components/Title';
import { Button } from '../../components/Button';
import { Icon } from '@trussworks/react-uswds';

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

  const conditions = {
    missing: [
      {
        display_name:
          'Influenza caused by Influenza A virus subtype H5N1 (disorder)',
      },
      { display_name: 'Syphilis' },
    ],
    found: [
      {
        display_name:
          'Disease caused by severe acute respiratory syndrome coronavirus 2 (disorder)',
      },
    ],
  };

  return (
    <div className="flex flex-col gap-8">
      <OutcomeMessageContainer>
        <div className="flex items-center gap-4">
          <Icon.Warning
            className="[&_path]:fill-state-error shrink-0"
            aria-label="Warning"
            size={3}
          />
          <p className="text-state-error-dark">
            The following detected conditions have not been configured and will
            not produce a refined eICR in the output
          </p>
        </div>
        <ul className="ml-2 list-inside list-disc">
          {conditions.missing.map((missingCondition) => (
            <li>{missingCondition.display_name}</li>
          ))}
        </ul>
      </OutcomeMessageContainer>
      <div className="flex flex-col gap-4">
        <p className="md:w-1/3">
          Please either create configurations for these conditions or upload a
          file that includes conditions that have been configured.
        </p>
        <div>
          <Button onClick={reset}>Start over</Button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex justify-center px-10 md:px-20">
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
          <ReportableConditions
            conditionNames={response.data.conditions.map((c) => c.display_name)}
            onClick={() => setView('success')}
          />
        )}
        {view === 'success' && response?.data && (
          <Success
            conditions={response.data.conditions}
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

function OutcomeMessageContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="!border-blue-cool-20 flex flex-col gap-4 rounded-lg border border-dashed bg-white px-6 py-8 md:w-2/3">
      {children}
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
