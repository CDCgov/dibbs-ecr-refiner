import { Header, SectionContainer } from '../layout';
import { useParams } from 'react-router';
import { RunSimulation } from '../../Simulator/RunSimulation';
import { useState } from 'react';
import {
  useGetConfiguration,
  useRunInlineConfigurationTest,
} from '../../../api/configurations/configurations';
import { Diff } from '@components/Diff';
import { GetConfigurationResponse } from '../../../api/schemas';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { ConfigurationTitleBar } from '../ConfigurationTitleBar';
import { Spinner } from '@components/Spinner';
import { Uploading } from '../../Simulator/Uploading';
import { Status } from '../ManageCodes/Status';
import { FileUploadWarning } from '@components/FileUploadWarning';
import { Button } from '@components/Button';
import { SpinnerWithMinimalRender } from '@components/Spinner/SpinnerWithMinimalRender';

export function ConfigTest() {
  const { id } = useParams<{ id: string }>();
  const {
    data: configuration,
    isPending,
    isError,
  } = useGetConfiguration(id ?? '');

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return 'Error!';

  return (
    <div className="flex flex-1 flex-col">
      <Header configuration={configuration.data} />
      <SectionContainer>
        <div className="mb-4 flex flex-wrap justify-between">
          <ConfigurationTitleBar
            title="Test configuration"
            subtitle="Check the results of your configuration before turning it on."
          />
          <Export
            id={configuration.data.id}
            config_name={configuration.data.display_name}
          />
        </div>

        <Test config={configuration.data} />
      </SectionContainer>
    </div>
  );
}

type Status = 'idle' | 'pending' | 'error' | 'success';

interface Test {
  config: GetConfigurationResponse;
}

function Test({ config }: Test) {
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
    <div className="mb-51">
      {status === 'idle' && (
        <RunSimulation
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
          refined_download_key={uploadResponseData.data.refined_download_key}
          unrefined_eicr={uploadResponseData.data.original_eicr}
          renderDiff={uploadResponseData.data.condition.render_diff}
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

interface ExportBuilderProps {
  id: string;
  config_name: string;
}

function Export({ id, config_name }: ExportBuilderProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleExport = async (e: React.MouseEvent) => {
    e.preventDefault();
    try {
      setIsDownloading(true);
      const response = await fetch(`/api/v1/configurations/${id}/export`);
      if (!response.ok) {
        const { detail } = await response.json();
        setDownloadError(detail ?? 'An unknown error occurred.');
        return;
      }

      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;

      const now = new Date();
      const dateDisplay = now.toLocaleDateString('en-GB').replace(/\//g, '-');
      link.download = `${config_name}-Export-${dateDisplay}.zip`;
      link.click();
      URL.revokeObjectURL(blobUrl);
      setDownloadError(null);
    } catch (error) {
      console.error(error);
      setDownloadError('An unknown error occurred.');
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <>
      <SpinnerWithMinimalRender
        isLoading={isDownloading}
        loadingMessage="Exporting..."
        renderWhenDone={
          <Button variant="tertiary" onClick={handleExport}>
            Export configuration
          </Button>
        }
      />
      {downloadError ? (
        <span className="text-state-error-dark">Error: {downloadError}</span>
      ) : null}
    </>
  );
}
