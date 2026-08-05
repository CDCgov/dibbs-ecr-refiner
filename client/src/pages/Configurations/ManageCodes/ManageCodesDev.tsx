import { useParams } from 'react-router';
import {
  useGetCodesInfinite,
  useGetConfiguration,
} from '../../../api/configurations/configurations';
import { useConfigLock } from '../../../hooks/useConfigLock';
import { Spinner } from '@components/Spinner';
import { Header, SectionContainer } from '../layout';
import { ConfigurationTitleBar } from '../ConfigurationTitleBar';
import { Button } from '@components/Button';
import classNames from 'classnames';
import { Checkbox } from '@components/Checkbox';
import { useState } from 'react';

export function ManageCodesDev() {
  const { id } = useParams<{ id: string }>();

  // acquire lock on mount, schedule release on unmount
  useConfigLock(id);

  const {
    data: configuration,
    isPending,
    isError,
  } = useGetConfiguration(id ?? '');

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return 'Error!';

  return (
    <div>
      <Header configuration={configuration.data} />
      <SectionContainer>
        <ConfigurationTitleBar
          title="Manage codes"
          subtitle="These codes will be used alongside the condition codesets by the Refiner to search for and retain."
        />
        <CodesTable id={configuration.data.id} />
      </SectionContainer>
    </div>
  );
}

interface CodesTableProps {
  id: string;
}

function CodesTable({ id }: CodesTableProps) {
  const {
    data,
    isPending,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useGetCodesInfinite(id, undefined, {
    query: {
      getNextPageParam: (lastPage) => lastPage.data.next_cursor ?? undefined,
    },
  });
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  if (isPending) return 'Loading...';
  if (isError) return 'Error!';

  const codes = data?.pages.flatMap((page) => page.data.codes) ?? [];

  const allSelected = codes.length > 0 && selectedIds.size === codes.length;

  return (
    <div className='flex flex-col gap-4 items-start'>
      <Button
        onClick={() => fetchNextPage()}
        disabled={!hasNextPage || isFetchingNextPage}
      >
        Next
      </Button>
      <table className="w-full table-fixed">
        <thead className="sticky top-0 z-10">
          <tr className="border-gray-cool-20 text-gray-cool-60 border-b text-left">
            <th scope="col" className="w-10 text-center">
              <Checkbox
                checked={allSelected}
                onChange={(checked) =>
                  setSelectedIds(
                    checked ? new Set(codes.map((c) => c.id)) : new Set()
                  )
                }
              />
            </th>
            <th scope="col">Code no.</th>
            <th scope="col">System</th>
            <th scope="col">Description</th>
            <th scope="col">Source</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody className="divide-gray-cool-20 divide-y">
          {codes.map((code) => (
            <tr
              key={code.id}
              className={classNames('text-gray-cool-60', {
                italic: code.status === 'excluded',
              })}
            >
              <td className="text-center">
                <Checkbox
                  checked={selectedIds.has(code.id)}
                  onChange={(checked) =>
                    setSelectedIds((prev) => {
                      const next = new Set(prev);
                      if (checked) {
                        next.add(code.id);
                      } else {
                        next.delete(code.id);
                      }
                      return next;
                    })
                  }
                />
              </td>
              <td>{code.code}</td>
              <td>{code.system_name}</td>
              <td>{code.description}</td>
              <td>{code.source}</td>
              <td>{code.status === 'included' ? 'Included' : 'Excluded'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
