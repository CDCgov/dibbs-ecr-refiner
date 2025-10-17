import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { StepsContainer, Steps } from '../Steps';
import { useParams } from 'react-router';
import { Title } from '../../../components/Title';
import { RunTest } from '../../Testing/RunTest';
import { useState } from 'react';
import {
  useGetConfiguration,
  useRunInlineConfigurationTest,
} from '../../../api/configurations/configurations';
import { Diff } from '../../../components/Diff';
import { GetConfigurationResponse } from '../../../api/schemas';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { ConfigurationTitleBar } from '../titleBar';
import { Spinner } from '../../../components/Spinner';
import { Uploading } from '../../Testing/Uploading';
import ErrorFallback from '../../ErrorFallback';
import FileUploadWarning from '../../../components/FileUploadWarning';

export default function ConfigTest() {
  const { id } = useParams<{ id: string }>();
  const {
    data: response,
    isPending,
    isError,
    error,
  } = useGetConfiguration(id ?? '');

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return <ErrorFallback error={error} />;

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

      {status === 'pending' && <Uploading />}

      {status === 'error' && (
        <FileUploadWarning errorMessage={errorMessage ?? ''} reset={reset} />
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
