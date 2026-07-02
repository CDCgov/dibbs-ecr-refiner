import { useParams } from 'react-router';
import { useGetSerializedConfiguration } from '../../../api/configurations/configurations';
import { Button } from '@components/Button';
import { Spinner } from '@components/Spinner';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';

export function ConfigSerialized() {
  const { id } = useParams<{ id: string }>();
  const formatError = useApiErrorFormatter();
  const {
    data: response,
    isPending,
    isError,
    error,
  } = useGetSerializedConfiguration(id ?? '');

  if (isPending) return <Spinner variant="centered" />;

  if (!id) {
    return null;
  }

  if (isError) {
    return (
      <Container id={id}>
        <p>{formatError(error)}</p>
      </Container>
    );
  }

  return (
    <Container id={id}>
      <details>
        <summary>{`current.json (${response.data.current.key})`}</summary>
        <CodeBlock>{response.data.current.content}</CodeBlock>
      </details>
      <details>
        <summary>{`metadata.json (${response.data.metadata.key})`}</summary>
        <CodeBlock>{response.data.metadata.content}</CodeBlock>
      </details>
      <details open>
        <summary>{`active.json (${response.data.active.key})`}</summary>
        <CodeBlock>{response.data.active.content}</CodeBlock>
      </details>
    </Container>
  );
}

function CodeBlock({ children }: { children: React.ReactNode }) {
  return (
    <pre className="border-gray-1 border border-dashed p-2">{children}</pre>
  );
}

function Container({
  children,
  id,
}: {
  children: React.ReactNode;
  id: string;
}) {
  return (
    <div className="flex flex-col items-start gap-10 p-6">
      <Button
        to={`/configurations/${id}/build`}
        variant="tertiary"
        className="p-0!"
      >
        Back to build page
      </Button>

      {children}
    </div>
  );
}
