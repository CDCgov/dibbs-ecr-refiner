import { useParams } from 'react-router';
import { Sections } from './Sections';
import { Title } from '@components/Title';
import { Button } from '@components/Button';
import { useToast } from '../../../hooks/useToast';
import { Steps, StepsContainer } from '../Steps';
import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { useRef, useState, forwardRef } from 'react';

import classNames from 'classnames';
import {
  getGetConfigurationQueryKey,
  useDisassociateConditionWithConfiguration,
  useGetConfiguration,
} from '../../../api/configurations/configurations';
import { GetConfigurationResponse } from '../../../api/schemas';
import { AddConditionCodeSetsDrawer } from './AddConditionCodeSets';
import { useQueryClient } from '@tanstack/react-query';
import { useApiErrorFormatter } from '../../../hooks/useErrorFormatter';
import { ConfigurationTitleBar } from '../ConfigurationTitleBar';
import { Spinner } from '@components/Spinner';
import { VersionMenu } from './VersionMenu';
import { DraftBanner } from './DraftBanner';
import { ConfigLockBanner } from './ConfigLockBanner';
import { Status } from './Status';
import { useConfigLockRelease } from '../../../hooks/useConfigLockRelease';
import { ImportCustomCodes } from './CustomCodes/ImportCustomCodes';
import { Icon } from '@trussworks/react-uswds';
import { ConditionCodeTable, CustomCodesDetail } from './CustomCodes/index';
import { TesLink } from '../TesLink';

export type CsvImportStep = 'intro' | 'preview' | 'error';
type CsvImportView = `csv_${CsvImportStep}`;
type TableView = 'none' | 'codeset' | 'custom' | 'sections' | CsvImportView;

const toCsvImportView = (step: CsvImportStep): CsvImportView => `csv_${step}`;

const isCsvImportView = (view: TableView): view is CsvImportView =>
  view.startsWith('csv_');

export function ConfigBuild() {
  const { id } = useParams<{ id: string }>();

  // release lock on beforeunload
  useConfigLockRelease(id);

  const {
    data: configuration,
    isPending,
    isError,
  } = useGetConfiguration(id ?? '');

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return 'Error!';

  const { is_locked: disabledForConcurrency } = configuration.data;
  const disabledForPrevVersion = configuration.data.status !== 'draft';
  const isDisabled = disabledForConcurrency || disabledForPrevVersion;

  // sort so the default code set always displays first
  const sortedCodeSets = configuration.data.code_sets.sort((a) => {
    return a.display_name === configuration.data.display_name ? -1 : 1;
  });

  return (
    <>
      <TitleContainer>
        <Title>{configuration.data.display_name}</Title>
        <Status version={configuration.data.active_version} />
      </TitleContainer>
      <NavigationContainer>
        <VersionMenu
          id={configuration.data.id}
          currentVersion={configuration.data.version}
          status={configuration.data.status}
          versions={configuration.data.all_versions}
          step="build"
        />
        <StepsContainer>
          <Steps configurationId={configuration.data.id} />
        </StepsContainer>
      </NavigationContainer>
      {disabledForPrevVersion ? (
        <DraftBanner
          draftId={configuration.data.draft_id}
          conditionId={configuration.data.condition_id}
          latestVersion={configuration.data.latest_version}
          step="build"
        />
      ) : null}
      {disabledForConcurrency ? (
        <ConfigLockBanner
          lockedByName={configuration.data.locked_by?.name}
          lockedByEmail={configuration.data.locked_by?.email}
        />
      ) : null}
      <SectionContainer>
        <div className="content flex flex-wrap justify-between">
          <ConfigurationTitleBar
            step="build"
            condition={configuration.data.display_name}
          />
          <Export id={configuration.data.id} />
        </div>

        <Builder
          id={configuration.data.id}
          code_sets={sortedCodeSets}
          included_conditions={configuration.data.included_conditions}
          custom_codes={configuration.data.custom_codes}
          section_processing={configuration.data.section_processing}
          display_name={configuration.data.display_name}
          disabled={isDisabled}
        />
      </SectionContainer>
    </>
  );
}

type ExportBuilderProps = {
  id: string;
};

export function Export({ id }: ExportBuilderProps) {
  return (
    <a
      className="text-blue-cool-60 mt-8 mb-6 self-end font-bold hover:cursor-pointer hover:underline"
      href={`/api/v1/configurations/${id}/export`}
      download
    >
      Export configuration
    </a>
  );
}

type BuilderProps = Pick<
  GetConfigurationResponse,
  | 'id'
  | 'code_sets'
  | 'custom_codes'
  | 'included_conditions'
  | 'section_processing'
  | 'display_name'
> & { disabled: boolean };

function Builder({
  id,
  code_sets,
  custom_codes,
  included_conditions,
  section_processing,
  display_name: default_condition_name,
  disabled,
}: BuilderProps) {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [tableView, setTableView] = useState<TableView>('none');
  const [selectedCodesetId, setSelectedCodesetId] = useState<string | null>(
    null
  );
  const [selectedCodesetName, setSelectedCodesetName] = useState<string | null>(
    null
  );

  const codeSetButtonRefs = useRef<Record<string, HTMLButtonElement | null>>(
    {}
  );

  // initialize table with the first code set if 1) nothing is loaded and 2) the data is loaded
  if (tableView === 'none' && code_sets[0] && code_sets[0].condition_id) {
    onCodesetClick(code_sets[0].display_name, code_sets[0].condition_id);
  }

  function onCodesetClick(name: string, id: string) {
    setSelectedCodesetName(name);
    setSelectedCodesetId(id);
    setTableView('codeset');
  }

  function onCustomCodeClick() {
    setSelectedCodesetName(null);
    setSelectedCodesetId(null);
    setTableView('custom');
  }

  function onCsvImportClick() {
    setSelectedCodesetName(null);
    setSelectedCodesetId(null);
    setTableView(toCsvImportView('intro'));
  }

  function setCodesetListItemFocus(deletedId: string) {
    // No change needed if we're not viewing the code set
    if (deletedId !== selectedCodesetId) return;

    const deletedItemIndex = code_sets.findIndex(
      (c) => c.condition_id === deletedId
    );

    /**
     * This shouldn't happen since we can't delete the primary condition code set.
     * Just in case 🙂
     */
    if (deletedItemIndex <= 0) return;

    const previousCodeSetId = code_sets[deletedItemIndex - 1].condition_id;

    codeSetButtonRefs.current[previousCodeSetId]?.click();
  }

  return (
    <div className="bg-blue-cool-5 h-140 rounded-lg p-4">
      <div className="flex h-full flex-col gap-4 sm:flex-row">
        <div className="flex flex-col py-2 pt-4 md:w-[20rem] md:gap-10">
          <div>
            <OptionsLabelContainer>
              <OptionsLabel htmlFor="open-codesets">
                CONDITION CODE SETS
              </OptionsLabel>
              {!disabled && (
                <Button
                  variant="secondary"
                  className="mr-0! flex h-8 flex-row items-center px-3! py-2!"
                  id="open-codesets"
                  aria-label="Add new code set to configuration"
                  onClick={() => setIsDrawerOpen(!isDrawerOpen)}
                  disabled={disabled}
                >
                  ADD
                </Button>
              )}
            </OptionsLabelContainer>
            <OptionsListContainer>
              <OptionsList>
                {code_sets.map((codeSet, i) => (
                  <li
                    key={codeSet.display_name}
                    className={classNames(
                      'group drop-shadow-base relative flex items-center overflow-visible rounded-sm hover:bg-stone-50',
                      {
                        'bg-white': selectedCodesetId === codeSet.condition_id,
                      }
                    )}
                  >
                    <ConditionCodeSetButton
                      ref={(btn) => {
                        codeSetButtonRefs.current[codeSet.condition_id] = btn;
                      }}
                      codeSetName={codeSet.display_name}
                      codeSetTotalCodes={codeSet.total_codes}
                      onViewCodeSet={() =>
                        onCodesetClick(
                          codeSet.display_name,
                          codeSet.condition_id
                        )
                      }
                      aria-controls={
                        selectedCodesetId ? 'codeset-table' : undefined
                      }
                    />

                    <DeleteCodeSetButton
                      index={i}
                      configurationId={id}
                      conditionId={codeSet.condition_id}
                      conditionName={codeSet.display_name}
                      onClick={() =>
                        setCodesetListItemFocus(codeSet.condition_id)
                      }
                      disabled={disabled}
                    />
                  </li>
                ))}
              </OptionsList>
            </OptionsListContainer>
          </div>
          <div>
            <OptionsLabelContainer>
              <OptionsLabel>MORE OPTIONS</OptionsLabel>
            </OptionsLabelContainer>
            <OptionsListContainer>
              <OptionsList>
                <li key="custom-codes">
                  <Button
                    variant="unstyled"
                    className={classNames(
                      'flex h-full w-full flex-col justify-between gap-3 rounded p-1 text-left hover:cursor-pointer hover:bg-stone-50 sm:flex-row sm:gap-0 sm:p-4',
                      {
                        'bg-white': tableView === 'custom',
                      }
                    )}
                    onClick={onCustomCodeClick}
                    aria-controls={
                      tableView === 'custom' ? 'custom-table' : undefined
                    }
                    aria-pressed={tableView === 'custom'}
                  >
                    <span>Custom codes</span>
                    <span>{custom_codes.length}</span>
                  </Button>
                </li>
                <li key="sections">
                  <Button
                    variant="unstyled"
                    className={classNames(
                      'flex h-full w-full flex-col justify-between gap-3 rounded p-1 text-left hover:cursor-pointer hover:bg-stone-50 sm:flex-row sm:gap-0 sm:p-4',
                      {
                        'bg-white': tableView === 'sections',
                      }
                    )}
                    onClick={() => {
                      setSelectedCodesetId(null);
                      setTableView('sections');
                    }}
                    aria-controls={
                      tableView === 'sections' ? 'sections-table' : undefined
                    }
                    aria-pressed={tableView === 'sections'}
                  >
                    <span>Sections</span>
                  </Button>
                </li>
              </OptionsList>
            </OptionsListContainer>
          </div>
        </div>
        <div className="flex h-full! max-h-138! w-full! flex-col items-start overflow-y-scroll rounded-lg bg-white p-1 pt-4 sm:w-2/3 sm:pt-0 md:p-6">
          {selectedCodesetId && tableView === 'codeset' ? (
            <>
              <ConditionCodeTable
                defaultCondition={selectedCodesetName}
                conditionId={selectedCodesetId}
              />
            </>
          ) : tableView === 'custom' ? (
            <div className="min-h-full min-w-full">
              <h3 className="mb-2 text-xl font-bold">Custom codes</h3>
              <CustomCodeGroupingParagraph />
              <div className="mt-4! flex items-center gap-3">
                <Button
                  onClick={() => setIsModalOpen(true)}
                  variant="secondary"
                  aria-label="Add new custom code"
                  disabled={disabled}
                >
                  Add code
                </Button>

                <Button onClick={onCsvImportClick} variant="tertiary">
                  Import from CSV
                </Button>
              </div>
              <CustomCodesDetail
                isOpen={isModalOpen}
                setIsOpen={setIsModalOpen}
                configurationId={id}
                customCodes={custom_codes}
                disabled={disabled}
              />
            </div>
          ) : tableView === 'sections' ? (
            <Sections
              configurationId={id}
              sections={section_processing}
              disabled={disabled}
            />
          ) : isCsvImportView(tableView) ? (
            <ImportCustomCodes
              configurationId={id}
              disabled={disabled}
              onSuccess={() => setTableView('custom')}
              onStepChange={(newStep) => setTableView(toCsvImportView(newStep))}
            />
          ) : null}
        </div>
      </div>
      <AddConditionCodeSetsDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        conditions={included_conditions}
        configurationId={id}
        reportable_condition_display_name={default_condition_name}
        disabled={disabled}
      />
    </div>
  );
}

function CustomCodeGroupingParagraph() {
  return (
    <p>
      Add codes that are not included in the code sets from the <TesLink />
    </p>
  );
}

type ConditionCodeSetButtonProps = {
  codeSetName: string;
  codeSetTotalCodes: number;
  onViewCodeSet: () => void;
} & React.ButtonHTMLAttributes<HTMLButtonElement>;

const ConditionCodeSetButton = forwardRef<
  HTMLButtonElement,
  ConditionCodeSetButtonProps
>(
  (
    {
      codeSetName,
      codeSetTotalCodes,
      onViewCodeSet,
      ...props
    }: ConditionCodeSetButtonProps,
    ref
  ) => {
    return (
      <Button
        ref={ref}
        variant="unstyled"
        className="group flex h-full w-full flex-row items-center justify-between gap-3 rounded p-1 text-left align-middle hover:cursor-pointer sm:p-4"
        onClick={onViewCodeSet}
        aria-label={`View TES code set information for ${codeSetName}`}
        {...props}
      >
        <span aria-hidden>{codeSetName}</span>
        <span aria-hidden className="group-hover:hidden">
          {codeSetTotalCodes}
        </span>
        <span className="sr-only">
          {codeSetName}, {codeSetTotalCodes} codes in code set
        </span>
      </Button>
    );
  }
);

interface DeleteCodeSetButtonProps {
  index: number;
  configurationId: string;
  conditionId: string;
  conditionName: string;
  onClick: () => void;
  disabled: boolean;
}

function DeleteCodeSetButton({
  index,
  configurationId,
  conditionId,
  conditionName,
  onClick,
  disabled,
}: DeleteCodeSetButtonProps) {
  const { mutate: disassociateMutation, isPending } =
    useDisassociateConditionWithConfiguration();

  const showToast = useToast();
  const queryClient = useQueryClient();
  const formatError = useApiErrorFormatter();

  function handleDisassociateCondition(conditionId: string) {
    disassociateMutation(
      {
        configurationId,
        conditionId,
      },
      {
        onSuccess: async (resp) => {
          showToast({
            heading: 'Condition code set removed',
            body: resp.data.condition_name,
          });

          await queryClient.invalidateQueries({
            queryKey: getGetConfigurationQueryKey(configurationId),
          });

          onClick(); // set focus to previous code set button
        },
        onError: (error) => {
          const errorDetail =
            formatError(error) || error.message || 'Unknown error';
          showToast({
            variant: 'error',
            heading: 'Error removing condition',
            body: errorDetail,
          });
        },
      }
    );
  }

  if (isPending) {
    return <Spinner size={20} className="mr-2" />;
  }

  if (disabled) {
    return null;
  }

  return index === 0 ? (
    <span className="text-gray-cool-40 mr-2 hidden italic group-hover:block">
      Default
    </span>
  ) : (
    <Button
      variant="unstyled"
      className="text-gray-cool-40 sr-only pr-4! group-hover:not-sr-only hover:cursor-pointer focus:not-sr-only disabled:cursor-not-allowed"
      aria-label={`Delete code set ${conditionName}`}
      onClick={() => handleDisassociateCondition(conditionId)}
      disabled={disabled}
    >
      <Icon.Delete
        className={disabled ? 'text-gray-cool-40' : 'fill-red-700!'}
        size={3}
        aria-hidden
      />
    </Button>
  );
}

type OptionsLabelsProps = {
  children: React.ReactNode;
  htmlFor?: string;
};

function OptionsLabel({ children, htmlFor }: OptionsLabelsProps) {
  const styles = '!text-gray-600 text-base font-bold';

  if (!htmlFor) return <span className={styles}>{children}</span>;

  return (
    <label className={styles} htmlFor={htmlFor}>
      {children}
    </label>
  );
}

function OptionsLabelContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex w-full items-center justify-between">{children}</div>
  );
}

function OptionsListContainer({ children }: { children: React.ReactNode }) {
  return <div className="max-h-60 overflow-y-scroll pt-2">{children}</div>;
}

function OptionsList({ children }: { children: React.ReactNode }) {
  return <ul className="flex flex-col gap-2">{children}</ul>;
}
