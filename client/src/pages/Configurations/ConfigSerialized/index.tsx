import { useParams } from 'react-router';
import { useGetSerializedConfiguration } from '../../../api/configurations/configurations';
import { Button } from '@components/Button';
import { Spinner } from '@components/Spinner';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef, useMemo } from 'react';

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

function CodeBlock({ children }: { children: string }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const lines = useMemo(() => children.split('\n'), [children]);

  /**
   * TODO: Known issue
   * See: https://github.com/TanStack/virtual/issues/1119
   */
  // eslint-disable-next-line react-hooks/incompatible-library
  const virtualizer = useVirtualizer({
    count: lines.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 20, // estimated line height in px
    overscan: 10,
  });

  return (
    <div
      ref={parentRef}
      className="border-gray-1 w-full overflow-auto border border-dashed p-2"
      style={{ height: '700px', width: '1280px' }}
    >
      <pre
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((item) => (
          <span
            key={item.key}
            style={{
              position: 'absolute',
              top: 0,
              transform: `translateY(${item.start}px)`,
              display: 'block',
            }}
          >
            {lines[item.index]}
          </span>
        ))}
      </pre>
    </div>
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
