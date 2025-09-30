import { Success } from './Success';
import { Error as ErrorScreen } from './Error';
import { RunTest } from './RunTest';
import { useState } from 'react';
import { useUploadEcr } from '../../api/demo/demo';
import { Title } from '../../components/Title';
import { Button } from '../../components/Button';
import { Icon } from '@trussworks/react-uswds';
import classNames from 'classnames';

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
          <>
            <Title>Test Refiner</Title>
            <ConditionsResults
              conditions={conditions}
              startOver={reset}
              goToSuccessScreen={() => setView('success')}
            />
          </>
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

interface Conditions {
  found: { display_name: string }[];
  missing: { display_name: string }[];
}

interface ConditionsResultsProps {
  conditions: Conditions;
  startOver: () => void;
  goToSuccessScreen: () => void;
}

function ConditionsResults({
  conditions,
  startOver,
  goToSuccessScreen,
}: ConditionsResultsProps) {
  const hasFoundConditions = conditions.found.length > 0;
  // const hasFoundConditions = false;
  const hasMissingConditions = conditions.missing.length > 0;

  if (hasFoundConditions) {
    return (
      <Container className="lg:w-4/7">
        <ConditionsContainer>
          <FoundConditions foundConditions={conditions.found} />
          {hasMissingConditions ? (
            <>
              <hr className="border-gray-cool-20" />
              <MissingConditions missingConditions={conditions.missing} />
            </>
          ) : null}
        </ConditionsContainer>
        <div className="flex flex-col gap-4 md:w-full">
          <p>Would you like to refine the eCR?</p>
          <p>
            Taking this action will split the original eICR, producing one
            refined eICR for each reportable condition and retaining content
            relevant only to that condition as defined in its configuration.
          </p>
        </div>
        <div>
          <Button onClick={goToSuccessScreen}>Refine eCR</Button>
          <Button variant="secondary" onClick={startOver}>
            Start over
          </Button>
        </div>
      </Container>
    );
  }

  return (
    <Container className="lg:w-4/7">
      <ConditionsContainer>
        <MissingConditions missingConditions={conditions.missing} />
      </ConditionsContainer>
      <div className="flex flex-col gap-4 md:w-2/3">
        <p>
          Please either create configurations for these conditions or upload a
          file that includes conditions that have been configured.
        </p>
        <div>
          <Button onClick={startOver}>Start over</Button>
        </div>
      </div>
    </Container>
  );
}

interface ContainerProps {
  children: React.ReactNode;
  className?: string;
}

function Container({ children, className }: ContainerProps) {
  return (
    <div className={classNames('flex flex-col gap-8', className)}>
      {children}
    </div>
  );
}

function ConditionsContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="!border-blue-cool-20 flex flex-col gap-5 rounded-lg border border-dashed bg-white px-6 py-8">
      {children}
    </div>
  );
}

interface FoundConditionsProps {
  foundConditions: { display_name: string }[];
}

function FoundConditions({ foundConditions }: FoundConditionsProps) {
  return (
    <div className="flex flex-col gap-4">
      <p className="font-bold">
        We found the following reportable condition(s) in the RR:
      </p>
      <ul className="ml-2 list-inside list-disc">
        {foundConditions.map((foundCondition) => (
          <li key={foundCondition.display_name}>
            {foundCondition.display_name}
          </li>
        ))}
      </ul>
    </div>
  );
}

interface MissingConditionsProps {
  missingConditions: { display_name: string }[];
}

function MissingConditions({ missingConditions }: MissingConditionsProps) {
  return (
    <div className="flex flex-col gap-4">
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
        {missingConditions.map((missingCondition) => (
          <li key={missingCondition.display_name}>
            {missingCondition.display_name}
          </li>
        ))}
      </ul>
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
