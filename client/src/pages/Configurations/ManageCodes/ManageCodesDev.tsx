import { useParams } from 'react-router';
import {
  getGetCodeCountsQueryKey,
  getGetCodesInfiniteQueryKey,
  useGetCodeCounts,
  useGetCodesInfinite,
  useGetConfiguration,
  useSetCodesStatus,
} from '../../../api/configurations/configurations';
import { useConfigLock } from '../../../hooks/useConfigLock';
import { Spinner } from '@components/Spinner';
import { Header, SectionContainer } from '../layout';
import { ConfigurationTitleBar } from '../ConfigurationTitleBar';
import { Button } from '@components/Button';
import classNames from 'classnames';
import { Checkbox } from '@components/Checkbox';
import { useState } from 'react';
import { QuestionIcon } from '@components/Tooltip/QuestionIcon';
import {
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@components/Modal';
import { Search } from '@components/Search';
import { AddCustomCodeButton } from './CustomCodes/AddCustomCodeButton';
import InfiniteScroll from 'react-infinite-scroll-component';
import { Switch } from '@components/Switch';
import { AddConditionCodeSetsDrawer } from './CodeSets/AddConditionCodeSetsDrawer';
import { CodeResponse, GetConfigurationResponse } from '../../../api/schemas';
import { useQueryClient } from '@tanstack/react-query';
import { DeleteCustomCodeButton } from './CustomCodes/DeleteCustomCodeButton';
import { EditCustomCodeButton } from './CustomCodes/EditCustomCodeButton';

/**
 * TODO: This component will live under the /manage-codes route once complete.
 */

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

  const isDisabled =
    configuration.data.status !== 'draft' || configuration.data.is_locked;

  return (
    <div>
      <Header configuration={configuration.data} />
      <SectionContainer>
        <ConfigurationTitleBar
          title="Manage codes"
          subtitle="These codes will be used alongside the condition codesets by the Refiner to search for and retain."
        />
        <div className="flex w-full flex-row items-center justify-end gap-2">
          <AddCodeSetsButton
            id={configuration.data.id}
            included_conditions={configuration.data.included_conditions}
            display_name={configuration.data.display_name}
            disabled={isDisabled}
          />
          <AddCustomCodeButton configurationId={id} disabled={isDisabled} />
        </div>
        <CodeInformationBar id={id} />
        <CodesTable id={configuration.data.id} disabled={isDisabled} />
      </SectionContainer>
    </div>
  );
}

interface CodesTableProps {
  id: string;
  disabled: boolean;
}

function CodesTable({ id, disabled }: CodesTableProps) {
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
    <div className="flex flex-col items-end gap-4">
      <SourceModal
        isOpen={isSourceModalOpen}
        onClose={() => setIsSourceModalOpen(false)}
      />
      <div className="flex w-full flex-col items-start justify-between gap-4 md:flex-row">
        <Search placeholder="Search by keyword" className="w-70!" />
        <div className="flex flex-col items-start gap-4 md:flex-row">
          <div className="border p-2">Code system filter</div>
          <div className="border p-2">Source filter</div>
          <div className="border p-2">Status filter</div>
        </div>
      </div>
      <InfiniteScroll
        dataLength={codes.length}
        next={fetchNextPage}
        hasMore={!!hasNextPage}
        loader={isFetchingNextPage ? <Spinner variant="centered" /> : null}
        endMessage={
          <p className="text-center italic">You've reached the end.</p>
        }
      >
        <table className="w-full table-fixed">
          <thead className="bg-gray-cool-5 sticky top-0 z-10">
            <tr className="border-gray-cool-60 text-gray-cool-60 border-b-2 text-left [&>th]:px-4 [&>th]:py-2">
              <th scope="col" className="w-10 text-center">
                <Checkbox
                  disabled={disabled}
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
              <th scope="col">Status</th>
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
                    disabled={disabled}
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
                <td>
                  <SourceCell configurationId={id} code={code} />
                </td>
                <td>
                  <IncludeSwitch
                    configurationId={id}
                    code={code}
                    disabled={disabled}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </InfiniteScroll>
    </div>
  );
}

interface SourceCellProps {
  configurationId: string;
  code: CodeResponse;
}

function SourceCell({ configurationId, code }: SourceCellProps) {
  if (!code.is_custom) return code.source;

  return (
    <div className="flex flex-col items-center gap-2 xl:flex-row">
      <span className="text-violet-warm-60 rounded-xs border bg-[#f9f4f9] px-2 py-0.5 text-sm font-bold whitespace-nowrap">
        Custom code
      </span>
      <div className="flex flex-row gap-2">
        <EditCustomCodeButton configurationId={configurationId} id={code.id} />
        <DeleteCustomCodeButton
          configurationId={configurationId}
          id={code.id}
          code={code.code}
        />
      </div>
    </div>
  );
}

interface IncludeSwitchProps {
  configurationId: string;
  code: CodeResponse;
  disabled: boolean;
}
function IncludeSwitch({
  configurationId,
  code,
  disabled,
}: IncludeSwitchProps) {
  const queryClient = useQueryClient();
  const { mutate } = useSetCodesStatus();

  const toggleStatus = () => {
    mutate(
      {
        configurationId,
        params: {
          status: code.status === 'Included' ? 'excluded' : 'included',
        },
        data: [code.id],
      },
      {
        onSuccess: async () => {
          await queryClient.invalidateQueries({
            queryKey: getGetCodesInfiniteQueryKey(configurationId),
          });
          await queryClient.invalidateQueries({
            queryKey: getGetCodeCountsQueryKey(configurationId),
          });
        },
      }
    );
  };

  return (
    <div className="flex flex-row items-center gap-2">
      <Switch
        checked={code.status === 'Included'}
        disabled={code.is_custom || disabled}
        onClick={toggleStatus}
      />
      {code.status}
    </div>
  );
}

type AddCodeSetsButtonProps = Pick<
  GetConfigurationResponse,
  'id' | 'included_conditions' | 'display_name'
> & {
  disabled: boolean;
};

function AddCodeSetsButton({
  id,
  included_conditions,
  display_name,
  disabled,
}: AddCodeSetsButtonProps) {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  return (
    <>
      <Button
        variant="unstyled"
        className="border-blue-cool-50! h-8 rounded-md border-2! bg-white px-3 text-sm! hover:cursor-pointer hover:bg-[#eef5f8]!"
        onClick={() => setIsDrawerOpen(true)}
      >
        <div className="flex flex-row items-center gap-2">
          <span className="bg-blue-cool-50 inline-flex h-5 min-w-5 items-center justify-center rounded-2xl font-bold text-white">
            {included_conditions.filter((ic) => ic.associated).length}
          </span>
          <span className="font-bold text-[#224a58]">Condition code sets</span>
          <CodeSetButtonSymbol />
        </div>
      </Button>
      <AddConditionCodeSetsDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        conditions={included_conditions}
        configurationId={id}
        reportable_condition_display_name={display_name}
        disabled={disabled}
      />
    </>
  );
}

function CodeSetButtonSymbol() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="#3a7d95">
      <path d="M4 4h7v16H4zm9 0h7v7h-7zm0 9h7v7h-7z" />
    </svg>
  );
}

function CodeInformationBar({ id }: { id: string }) {
  const { data: codeCounts, isPending, isError } = useGetCodeCounts(id);

  if (isError) return 'Error!';
  if (isPending)
    return (
      <div className="bg-blue-cool-5 border-blue-cool-20! flex min-h-20 w-full flex-col gap-2 border px-10 py-4">
        <div className="absolute inset-0 top-10 flex items-center justify-center">
          <Spinner />
        </div>
      </div>
    );

  const includedCount =
    codeCounts.data.total_code_count -
    codeCounts.data.total_excluded_codes_count;
  const total = codeCounts.data.total_code_count;
  const barFillPercentage = total > 0 ? (includedCount / total) * 100 : 0;

  return (
    <div className="bg-blue-cool-5 border-blue-cool-20! flex min-h-20 w-full flex-col gap-2 border px-10 py-4">
      <div className="flex flex-row items-center justify-between">
        <div>
          <span className="text-2xl font-bold">
            {includedCount.toLocaleString()}
          </span>{' '}
          <span className="text-lg">
            of {total.toLocaleString()} codes included
          </span>
        </div>
        <div className="flex flex-col gap-4 text-left md:flex-row md:gap-8">
          <span>
            {codeCounts.data.total_excluded_codes_count.toLocaleString()}{' '}
            excluded
          </span>
          <span>
            {codeCounts.data.total_custom_codes_count.toLocaleString()} custom
          </span>
          <span>
            {codeCounts.data.total_code_sets_count.toLocaleString()} condition
            code sets
          </span>
        </div>
      </div>
      <div
        aria-hidden
        className="bg-blue-cool-20 relative min-h-2 w-full overflow-hidden rounded-2xl"
      >
        <div
          className="bg-blue-cool-50 absolute inset-y-0 left-0 rounded-2xl transition-all duration-500"
          style={{ width: `${barFillPercentage}%` }}
        />
      </div>
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
