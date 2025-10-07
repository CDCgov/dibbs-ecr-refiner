import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { StepsContainer, Steps } from '../Steps';
import { useParams } from 'react-router';
import { Button } from '../../../components/Button';
import { Title } from '../../../components/Title';
import { RunTest } from '../../Testing/RunTest';
import { useState } from 'react';
import {
  useGetConfiguration,
  useRunInlineConfigurationTest,
} from '../../../api/configurations/configurations';
import { Diff } from '../../../components/Diff';
import { Icon } from '@trussworks/react-uswds';
import { GetConfigurationResponse } from '../../../api/schemas';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { ConfigurationTitleBar } from '../titleBar';
import { Spinner } from '../../../components/Spinner';

export default function ConfigTest() {
  const { id } = useParams<{ id: string }>();
  const { data: response, isPending, isError } = useGetConfiguration(id ?? '');

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return 'Error!';

  return (
    <div>
      <TitleContainer>
        <Title>{response.data.display_name}</Title>
      </TitleContainer>
      <NavigationContainer>
        <StepsContainer>
          <Steps configurationId={id} />
        </StepsContainer>
      </NavigationContainer>
      <SectionContainer>
        <ConfigurationTitleBar step="test" />
        <Tester config={response.data} />
      </SectionContainer>
    </div>
  );
}

type Status = 'idle' | 'pending' | 'error' | 'success';

interface TesterProps {
  config: GetConfigurationResponse;
}

function Tester({ config }: TesterProps) {
  const [status, setStatus] = useState<Status>('idle');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const {
    data: uploadResponseData,
    errorMessage,
    resetState,
    uploadZip,
  } = useZipUpload();

  async function runTest(file: File | null) {
    setStatus('pending');
    try {
      await uploadZip(config.id, file);
      setStatus('success');
    } catch {
      setStatus('error');
    }
  }

  function reset() {
    setStatus('idle');
    resetState();
  }

  return (
    <div className="mb-6">
      {status === 'idle' && (
        <RunTest
          onClickSampleFile={() => runTest(null)}
          onClickCustomFile={() => runTest(selectedFile)}
          selectedFile={selectedFile}
          setSelectedFile={setSelectedFile}
        />
      )}

      {status === 'pending' && <Spinner variant="centered" />}

      {status === 'error' && (
        <div className="flex flex-col gap-8">
          <div className="flex flex-col gap-4">
            <WarningMessage>{errorMessage}</WarningMessage>
          </div>

          <div className="flex flex-col gap-4">
            <p className="max-w-[550px]">
              Please ensure your file is valid and includes the reportable
              condition matching the configuration being tested.
            </p>
            <div>
              <Button onClick={reset}>Try again</Button>
            </div>
          </div>
        </div>
      )}

      {status === 'success' && uploadResponseData?.data && (
        <Diff
          condition={uploadResponseData.data.condition}
          refined_download_url={uploadResponseData.data.refined_download_url}
          unrefined_eicr={uploadResponseData.data.original_eicr}
        />
      )}
    </div>
  );
}

function useZipUpload() {
  const errorFormatter = useApiErrorFormatter();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const {
    mutateAsync,
    data,
    reset: resetState,
  } = useRunInlineConfigurationTest({
    mutation: {
      onError: (error) => {
        setErrorMessage(errorFormatter(error));
      },
      retry: false,
    },
  });

  async function uploadZip(configId: string, selectedFile: File | null) {
    setErrorMessage(null);

    const resp = await mutateAsync({
      data: { id: configId, uploaded_file: selectedFile },
    });

    return resp;
  }

  return {
    uploadZip,
    data,
    errorMessage,
    resetState,
  };
}

interface WarningMessageProps {
  children: React.ReactNode;
}
function WarningMessage({ children }: WarningMessageProps) {
  return (
    <div className="bg-state-error-lighter w-fit rounded p-4">
      <p className="text-state-error-dark flex flex-col gap-3">
        <span className="flex items-center gap-2">
          <Icon.Warning
            className="[&_path]:fill-state-error shrink-0"
            aria-label="Warning"
          />
          <span>{children}</span>
        </span>
      </p>
    </div>
  );
}
