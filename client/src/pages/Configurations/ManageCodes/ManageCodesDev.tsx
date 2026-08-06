import { useParams } from 'react-router';
import {
  useGetCodeCounts,
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
import { Tooltip } from '@components/Tooltip';
import { QuestionIcon } from '@components/Tooltip/QuestionIcon';
import {
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@components/Modal';
import { Search } from '@components/Search';

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
  const [isSourceModalOpen, setIsSourceModalOpen] = useState(false);

  if (isPending) return 'Loading...';
  if (isError) return 'Error!';

  const codes = data?.pages.flatMap((page) => page.data.codes) ?? [];

  const allSelected = codes.length > 0 && selectedIds.size === codes.length;

  return (
    <div className="flex flex-col items-start gap-4">
      <SourceModal
        isOpen={isSourceModalOpen}
        onClose={() => setIsSourceModalOpen(false)}
      />
      <Button
        onClick={() => fetchNextPage()}
        disabled={!hasNextPage || isFetchingNextPage}
      >
        Next
      </Button>
      <CodeInformationBar id={id} />
      <div className="flex w-full justify-between">
        <Search placeholder="Search by keyword" className="w-80!" />
        <div className="flex flex-row gap-4">
          <div className="border p-2">Code system filter</div>
          <div className="border p-2">Source filter</div>
          <div className="border p-2">Status filter</div>
        </div>
      </div>
      <table className="w-full table-fixed">
        <thead className="sticky top-0 z-10">
          <tr className="border-gray-cool-60 text-gray-cool-60 border-b-2 text-left [&>th]:px-4 [&>th]:py-2">
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
            <th scope="col">
              <div className="flex flex-row items-center gap-1">
                <span>Source</span>
                <Button
                  variant="tertiary"
                  onClick={() => setIsSourceModalOpen(true)}
                  className="p-0!"
                  aria-label="Open reporting specification details modal"
                >
                  <QuestionIcon />
                </Button>
              </div>
            </th>
            <th scope="col" className="text-center">
              Status
            </th>
            <th>
              <div className="flex flex-row items-center gap-1">
                <span>Actions</span>
                <Tooltip label="Include or exclude a code from this configuration, or edit and delete custom codes you've added." />
              </div>
            </th>
          </tr>
        </thead>
        <tbody className="divide-gray-cool-20 divide-y">
          {codes.map((code) => (
            <tr
              key={code.id}
              className={classNames(
                'text-gray-cool-60 [&>td]:px-4 [&>td]:py-2',
                {
                  italic: code.status === 'Excluded',
                }
              )}
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
              <td className="text-center">{code.status}</td>
              <td>Actions</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CodeInformationBar({ id }: { id: string }) {
  const { data: codeCounts, isPending, isError } = useGetCodeCounts(id);

  if (isPending) return 'Loading...';
  if (isError) return 'Error!';

  const {
    total_code_count,
    total_code_sets_count,
    total_custom_codes_count,
    total_excluded_codes_count,
  } = codeCounts.data;

  return (
    <div className="bg-blue-cool-5 border-blue-cool-20! flex w-full flex-col gap-2 border px-10 py-4">
      <div className="flex flex-row items-center justify-between">
        <div>
          <span className="text-2xl font-bold">
            {(total_code_count - total_excluded_codes_count).toLocaleString()}
          </span>{' '}
          <span className="text-lg">
            of {total_code_count.toLocaleString()} codes included
          </span>
        </div>
        <div className="flex flex-row gap-8">
          <span>{total_excluded_codes_count.toLocaleString()} excluded</span>
          <span>{total_custom_codes_count.toLocaleString()} custom</span>
          <span>
            {total_code_sets_count.toLocaleString()} condition code sets
          </span>
        </div>
      </div>
      <div aria-hidden className="bg-blue-cool-50 h-3 w-full rounded-2xl" />
    </div>
  );
}

interface SourceModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function SourceModal({ isOpen, onClose }: SourceModalProps) {
  return (
    <Modal open={isOpen} onClose={onClose} position="center">
      <ModalHeader>
        <ModalTitle>Where codes come from</ModalTitle>
      </ModalHeader>
      <ModalBody>
        <div className="flex flex-col gap-4">
          <p>
            Each code's Source is the code set it comes from within the
            Terminology Exchange Service (TES). A condition's Condition Grouper
            is made up of two component types:
          </p>
          <p>
            <span className="font-bold">
              Reporting Specification Grouper (RSG)
            </span>{' '}
            — a ValueSet that combines all RCKMS reporting specification codes
            linked to a specific SNOMED condition.
          </p>
          <p>
            <span className="font-bold">Additional Context Grouper (ACG)</span>{' '}
            — a ValueSet curated for the TES containing codes that provide
            context to a Condition Grouper (e.g., RxNorm, LOINC, SNOMED,
            ICD-10-CM).
          </p>
          <p>
            <span className="font-bold">Condition Grouper</span> — a grouping
            ValueSet that contains both components (Reporting Specification &
            Additional Context).
          </p>
          <p>
            <span className="font-bold">Custom Code</span> — a code you added
            directly to this configuration, outside the TES code sets.
          </p>
        </div>
      </ModalBody>
      <ModalFooter align="left">
        <Button onClick={onClose}>Close</Button>
      </ModalFooter>
    </Modal>
  );
}
