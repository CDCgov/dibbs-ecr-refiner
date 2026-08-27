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
import { QuestionIcon } from '@components/Tooltip/QuestionIcon';
import {
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@components/Modal';
import { AddCustomCodeButton } from './CustomCodes/AddCustomCodeButton';
import InfiniteScroll from 'react-infinite-scroll-component';
import { AddConditionCodeSetsDrawer } from './CodeSets/AddConditionCodeSetsDrawer';
import { CodeResponse, GetConfigurationResponse } from '../../../api/schemas';
import { DeleteCustomCodeButton } from './CustomCodes/DeleteCustomCodeButton';
import { EditCustomCodeButton } from './CustomCodes/EditCustomCodeButton';
import { CodeFilters, Filters } from './Filters';
import { useFilterState } from './useFilterState';
import { ControlPanel } from './ControlPanel';
import { SearchBar } from './SearchBar';
import { ImportCustomCodes } from './CustomCodes/CsvImport/ImportCustomCodes';
import { Tooltip } from '@components/Tooltip';

export function ManageCodes() {
  const { id } = useParams<{ id: string }>();
  const [isUploadingCustomCodes, setIsUploadingCustomCodes] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

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
    <div className="flex flex-1 flex-col">
      <Header configuration={configuration.data} />
      <SectionContainer>
        <div className="flex flex-col gap-6">
          <div className="flex flex-col items-start justify-between gap-4 lg:flex-row">
            <ConfigurationTitleBar
              title="Manage codes"
              subtitle="These codes will be used alongside the condition codesets by the Refiner to search for and retain."
            />
            <AddCodeSetsButton
              included_conditions={configuration.data.included_conditions}
              setIsDrawerOpen={setIsDrawerOpen}
            />
            <AddCustomCodeButton
              configurationId={id}
              disabled={isDisabled}
              setIsUploadingCustomCodes={setIsUploadingCustomCodes}
            />
          </div>
          {isUploadingCustomCodes ? (
            <ImportCustomCodes
              configurationId={id}
              disabled={isDisabled}
              onSuccess={() => setIsUploadingCustomCodes(false)}
            />
          ) : (
            <CodesPanel id={configuration.data.id} disabled={isDisabled} />
          )}
        </div>
      </SectionContainer>
      <AddConditionCodeSetsDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        conditions={configuration.data.included_conditions}
        configurationId={configuration.data.id}
        reportable_condition_display_name={configuration.data.display_name}
        disabled={isDisabled}
      />
    </div>
  );
}

interface CodesPanelProps {
  id: string;
  disabled: boolean;
}

function CodesPanel({ id, disabled }: CodesPanelProps) {
  const { filters, setFilters, clearFilters, isFilterActive, filtersKey } =
    useFilterState(id);
  return (
    <>
      <CodeInformationBar id={id} />
      <div className="flex w-full flex-col items-start justify-between gap-4 lg:flex-row">
        <SearchBar filters={filters} setFilters={setFilters} />
        <Filters
          configurationId={id}
          filters={filters}
          onFiltersChange={setFilters}
        />
      </div>
      <CodesTable
        key={filtersKey}
        id={id}
        disabled={disabled}
        filters={filters}
        onClearFilters={clearFilters}
        isFilterActive={isFilterActive}
      />
    </>
  );
}

interface CodesTableProps {
  id: string;
  disabled: boolean;
  filters: CodeFilters;
  isFilterActive: boolean;
  onClearFilters: () => void;
}

type ParamValue =
  | string
  | number
  | boolean
  | (string | number | boolean)[]
  | null
  | undefined;

function CodesTable({
  id,
  disabled,
  filters,
  isFilterActive,
  onClearFilters,
}: CodesTableProps) {
  const {
    data,
    isPending,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useGetCodesInfinite(
    id,
    {
      code_systems: filters.codeSystems.map((cs) => cs.id),
      sources: filters.sources.map((s) => s.id),
      statuses: filters.statuses.map((s) => s.id),
      search: filters.search,
    },
    {
      query: {
        getNextPageParam: (lastPage) => lastPage.data.next_cursor ?? undefined,
      },
      axios: {
        // This serializer allows us to pass the filter array values to the server in the expected format.
        // For example:
        // `/api/v1/configurations/<UUID>/codes?code_systems=<UUID>&code_systems=<UUID>&sources=<UUID>&statuses=excluded&search=code+description`
        paramsSerializer: (params: Record<string, ParamValue>) => {
          const searchParams = new URLSearchParams();
          for (const [key, value] of Object.entries(params)) {
            if (Array.isArray(value)) {
              value.forEach((v) => searchParams.append(key, String(v)));
            } else if (value !== null && value !== undefined) {
              searchParams.append(key, String(value));
            }
          }
          return searchParams.toString();
        },
      },
    }
  );

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isSourceModalOpen, setIsSourceModalOpen] = useState(false);

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error!';

  const codes = data?.pages.flatMap((page) => page.data.codes) ?? [];

  const codesWithoutPrimaryConditionRsgCodes = codes.filter(
    (c) => !c.is_primary_condition_rsg
  );

  const allSelected =
    codesWithoutPrimaryConditionRsgCodes.length > 0 &&
    selectedIds.size === codesWithoutPrimaryConditionRsgCodes.length;
  const selectedCustomCodes = codesWithoutPrimaryConditionRsgCodes.filter(
    (c) => selectedIds.has(c.id) && c.is_custom
  );

  const hasCodesSelected = selectedIds.size > 0;

  return (
    <div className="flex flex-col items-end gap-4">
      <SourceModal
        isOpen={isSourceModalOpen}
        onClose={() => setIsSourceModalOpen(false)}
      />
      <div>
        {hasCodesSelected ? (
          <ControlPanel
            configurationId={id}
            selectedCodeIds={selectedIds}
            selectedCustomCodes={selectedCustomCodes}
            clearSelections={() => setSelectedIds(new Set())}
          />
        ) : null}
        <InfiniteScroll
          dataLength={codes.length}
          next={fetchNextPage}
          hasMore={!!hasNextPage}
          loader={isFetchingNextPage ? <Spinner variant="centered" /> : null}
          endMessage={
            codes.length > 0 ? (
              <p className="text-center italic">You've reached the end.</p>
            ) : null
          }
          style={{ overflow: 'unset' }} // this allows the sticky header to work
        >
          <table className="table-auto">
            <thead className="bg-gray-cool-5 z-sticky sticky top-0">
              <tr className="border-gray-cool-60 text-gray-cool-60 border-b-2 text-left [&>th]:px-4 [&>th]:py-2">
                <th scope="col" className="w-10 text-center">
                  <Checkbox
                    aria-label="Include all codes in bulk operation"
                    disabled={disabled}
                    checked={allSelected}
                    onChange={(checked) =>
                      setSelectedIds(
                        checked
                          ? new Set(
                              codesWithoutPrimaryConditionRsgCodes.map(
                                (c) => c.id
                              )
                            )
                          : new Set()
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
                <th scope="col" className="w-[10%]">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-gray-cool-20 divide-y">
              {codes.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="text-gray-cool-60 px-4 py-8 text-center"
                  >
                    <div className="flex flex-col items-center justify-center gap-4">
                      <span className="text-lg font-bold">
                        No codes match your search or filters.
                      </span>
                      {isFilterActive && (
                        <Button
                          variant="tertiary"
                          onClick={onClearFilters}
                          className="p-0!"
                        >
                          Clear search and filters
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                codes.map((code) => (
                  <tr
                    key={`${code.condition_id ?? 'custom-code'}-${code.id}`}
                    className={classNames(
                      'text-gray-cool-60 [&>td]:px-4 [&>td]:py-2',
                      {
                        italic: code.status === 'Excluded',
                      }
                    )}
                  >
                    <td className="text-center">
                      {code.is_primary_condition_rsg ? (
                        <Tooltip
                          position="right"
                          label="Reportable Condition Trigger Codes (RCTC) must be included for proper processing of the eCR."
                        >
                          <LockIcon />
                        </Tooltip>
                      ) : (
                        <Checkbox
                          aria-label={`Include ${code.code} in bulk operation`}
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
                      )}
                    </td>
                    <td>{code.code}</td>
                    <td>{code.system_name}</td>
                    <td>{code.description}</td>
                    <td>
                      <SourceCell configurationId={id} code={code} />
                    </td>
                    <td>{code.status}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </InfiniteScroll>
      </div>
    </div>
  );
}

function LockIcon() {
  return (
    <svg
      data-testid="lock-icon"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="#71767a"
    >
      <path
        data-dc-tpl="743"
        d="M18 8h-1V6A5 5 0 0 0 7 6v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2zM9 6a3 3 0 0 1 6 0v2H9V6zm3 11a2 2 0 1 1 0-4 2 2 0 0 1 0 4z"
      />
    </svg>
  );
}

interface SourceCellProps {
  configurationId: string;
  code: CodeResponse;
}

function SourceCell({ configurationId, code }: SourceCellProps) {
  if (!code.is_custom) return code.source.join(', ');

  return (
    <div className="flex flex-col items-center gap-2 xl:flex-row">
      <span>Custom code</span>
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

type AddCodeSetsButtonProps = Pick<
  GetConfigurationResponse,
  'included_conditions'
> & {
  setIsDrawerOpen: (open: boolean) => void;
};

function AddCodeSetsButton({
  included_conditions,
  setIsDrawerOpen,
}: AddCodeSetsButtonProps) {
  return (
    <>
      <Button
        variant="unstyled"
        className="border-blue-cool-50! hover:bg-blue-cool-5! h-8 rounded-md border-2! bg-white px-3 text-sm! whitespace-nowrap hover:cursor-pointer"
        onClick={() => setIsDrawerOpen(true)}
      >
        <div className="flex flex-row items-center gap-2">
          <span className="bg-blue-cool-50 inline-flex h-5 min-w-5 items-center justify-center rounded-2xl font-bold text-white">
            {included_conditions.filter((ic) => ic.associated).length}
          </span>
          <span className="text-blue-cool-70 font-bold">
            Condition code sets
          </span>
          <CodeSetButtonSymbol />
        </div>
      </Button>
    </>
  );
}

function CodeSetButtonSymbol() {
  return (
    <svg
      className="fill-blue-cool-50"
      width="18"
      height="18"
      viewBox="0 0 24 24"
    >
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
        <div data-testid="codes-included-display">
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
