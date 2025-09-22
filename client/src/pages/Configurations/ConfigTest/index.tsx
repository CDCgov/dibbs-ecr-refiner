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

export default function ConfigTest() {
  const { id } = useParams<{ id: string }>();
  const {
    data: response,
    isLoading,
    isError,
  } = useGetConfiguration(id ?? '', {
    query: { enabled: !!id },
  });

  if (isLoading || !response?.data) return 'Loading...';
  if (!id || isError) return 'Error!';

  return (
    <div>
      <TitleContainer>
        <Title>{response.data.display_name}</Title>
      </TitleContainer>
      <NavigationContainer>
        <StepsContainer>
          <Steps configurationId={id} />
          <Button to={`/configurations/${id}/activate`}>
            Next: Turn on configuration
          </Button>
        </StepsContainer>
      </NavigationContainer>
      <SectionContainer>
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

  const {
    data: uploadResponseData,
    errorMessage,
    resetState,
    uploadZip,
  } = useZipUpload();

  return (
    <div>
      {status === 'idle' && (
        <RunTest
          onClickSampleFile={() => runTest(null)}
          onClickCustomFile={() => runTest(selectedFile)}
          selectedFile={selectedFile}
          setSelectedFile={setSelectedFile}
        />
      )}

      {status === 'pending' && <p>Loading...</p>}

      {status === 'error' && (
        <div className="flex flex-col gap-3">
          <ServerError>{errorMessage}</ServerError>
          <div>
            <Button onClick={reset}>Go back</Button>
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
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const {
    mutateAsync,
    data,
    reset: resetState,
  } = useRunInlineConfigurationTest({
    mutation: {
      onError: (error) => {
        const rawError = error.response?.data;

        const message = Array.isArray(rawError?.detail)
          ? rawError.detail.map((d) => d.msg).join(' ')
          : rawError?.detail || 'Upload failed. Please try again.';
        setErrorMessage(message);
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

interface ServerErrorProps {
  children: React.ReactNode;
}
function ServerError({ children }: ServerErrorProps) {
  return (
    <div className="bg-state-error-lighter rounded p-4">
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
