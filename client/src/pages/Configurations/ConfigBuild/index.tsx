import { useParams } from 'react-router';
import { Title } from '../../../components/Title';
import { Button } from '../../../components/Button';
import { useToast } from '../../../hooks/useToast';
import { Steps, StepsContainer } from '../Steps';
import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { useEffect, useState } from 'react';
import classNames from 'classnames';
import { Search } from '../../../components/Search';
import { Icon, Label, Select } from '@trussworks/react-uswds';
import { useSearch } from '../../../hooks/useSearch';
import { useGetConfiguration } from '../../../api/configurations/configurations';
import { GetConfigurationResponse } from '../../../api/schemas';
import { useGetCondition } from '../../../api/conditions/conditions';

export default function ConfigBuild() {
  // Fetch config by ID on page load for each of these steps
  // build -> test -> activate
  const { id } = useParams<{ id: string }>();
  const {
    data: response,
    isLoading,
    isError,
  } = useGetConfiguration(id ?? '', {
    query: { enabled: !!id },
  });

  if (isLoading || !response?.data) return 'Loading...';
  if (isError) return 'Error!';

  return (
    <div>
      <TitleContainer>
        <Title>{response.data.display_name}</Title>
      </TitleContainer>
      <NavigationContainer>
        <StepsContainer>
          <Steps configurationId={response?.data.id} />
          <Button to={`/configurations/${id}/test`}>
            Next: Test configuration
          </Button>
        </StepsContainer>
      </NavigationContainer>
      <SectionContainer>
        <Builder code_sets={response.data.code_sets} />
      </SectionContainer>
    </div>
  );
}

type BuilderProps = Pick<GetConfigurationResponse, 'code_sets'>;

function Builder({ code_sets }: BuilderProps) {
  const [selectedCodesetId, setSelectedCodesetId] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [customCodes, setCustomCodes] = useState<
    { code: string; system: string; name: string }[]
  >([]);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [modalInitialData, setModalInitialData] = useState<{
    code: string;
    system: string;
    name: string;
  } | null>(null);

  const handleAddOrEditCustomCode = (data: {
    code: string;
    system: string;
    name: string;
  }) => {
    if (editingIndex !== null) {
      // update existing row
      setCustomCodes((prev) =>
        prev.map((item, idx) => (idx === editingIndex ? data : item))
      );
    } else {
      // add new row
      setCustomCodes((prev) => [...prev, data]);
    }
    setEditingIndex(null);
    setModalInitialData(null);
    setIsModalOpen(false);
  };

  function onClick(id: string) {
    setSelectedCodesetId(id);
  }

  const isCustomCodes = selectedCodesetId === 'custom';

  return (
    <div className="bg-blue-cool-5 h-[35rem] rounded-lg p-2">
      <div className="flex h-full flex-col gap-4 sm:flex-row">
        <div className="flex flex-col gap-4 py-4 sm:w-1/3 md:px-2">
          <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-0">
            <label
              className="text-gray-cool-60 font-bold"
              htmlFor="open-codesets"
            >
              CONDITION CODE SETS
            </label>
            <button
              className="text-blue-cool-60 flex flex-row items-center font-bold hover:cursor-pointer"
              id="open-codesets"
              aria-label="Add new code set to configuration"
            >
              <Icon.Add size={3} aria-hidden />
              <span>ADD</span>
            </button>
          </div>
          <div className="max-h-[10rem] overflow-y-auto md:max-h-[34.5rem]">
            <ul className="flex flex-col gap-2">
              {code_sets.map((codeSet) => (
                <li key={codeSet.display_name}>
                  <button
                    className={classNames(
                      'flex h-full w-full flex-col justify-between gap-3 rounded p-1 text-left hover:cursor-pointer hover:bg-stone-50 sm:flex-row sm:gap-0 sm:p-4',
                      {
                        'bg-white': selectedCodesetId === codeSet.condition_id,
                      }
                    )}
                    onClick={() => onClick(codeSet.condition_id)}
                    aria-controls={
                      selectedCodesetId ? 'codeset-table' : undefined
                    }
                    aria-pressed={selectedCodesetId === codeSet.condition_id}
                  >
                    <span>{codeSet.display_name}</span>
                    <span>{codeSet.total_codes}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-0">
              <label
                className="text-gray-cool-60 font-bold"
                htmlFor="open-codesets"
              >
                MORE OPTIONS
              </label>
            </div>
          </div>
          <div className="max-h-[10rem] overflow-y-auto md:max-h-[34.5rem]">
            <ul className="mt-2 flex flex-col gap-2">
              <li>
                <button
                  className={classNames(
                    'flex h-full w-full flex-col justify-between gap-3 rounded p-1 text-left hover:cursor-pointer hover:bg-stone-50 sm:flex-row sm:gap-0 sm:p-4',
                    { 'bg-white': isCustomCodes }
                  )}
                  onClick={() => {
                    onClick('custom');
                  }}
                >
                  <span>Custom codes</span>
                  <span>{customCodes.length}</span>
                </button>
              </li>
            </ul>
          </div>
        </div>
        <div className="flex max-h-[34.5rem] flex-col items-start gap-4 overflow-y-auto rounded-lg bg-white p-1 pt-4 sm:w-2/3 sm:pt-0 md:p-6">
          {selectedCodesetId && selectedCodesetId != 'custom' ? (
            <div>
              <ConditionCodeGroupingParagraph />
              <ConditionCodeTable conditionId={selectedCodesetId} />
            </div>
          ) : selectedCodesetId === 'custom' ? (
            <div>
              <CustomCodeGroupingParagraph />
              <Button
                className="margin-top-1em"
                variant="secondary"
                id="open-codesets"
                aria-label="Add new custom code to configuration"
                onClick={() => setIsModalOpen(true)}
              >
                <span>Add code</span>
              </Button>
              {customCodes.length > 0 && (
                <table className="margin-top-2em w-full border-separate border-spacing-y-4">
                  <tbody>
                    {customCodes.map((c, i) => (
                      <tr key={i}>
                        <td>{c.code}</td>
                        <td>{c.system}</td>
                        <td>{c.name}</td>
                        <td>
                          <button
                            className="usa-button usa-button--unstyled text-blue-60"
                            onClick={() => {
                              setEditingIndex(i);
                              setModalInitialData(c);
                              setIsModalOpen(true);
                            }}
                          >
                            Edit
                          </button>
                          <span> | </span>
                          <button
                            className="usa-button usa-button--unstyled text-red-60"
                            onClick={() =>
                              setCustomCodes((prev) =>
                                prev.filter((_, idx) => idx !== i)
                              )
                            }
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          ) : null}
        </div>
      </div>
      <AddCustomCodeModal
        open={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingIndex(null);
          setModalInitialData(null);
        }}
        onSubmit={handleAddOrEditCustomCode}
        initialData={modalInitialData}
      />
    </div>
  );
}

function ConditionCodeGroupingParagraph() {
  return (
    <p>
      These condition code sets come from the default groupings in the{' '}
      <a
        className="text-blue-cool-60 hover:text-blue-cool-50 underline"
        href="https://tes.tools.aimsplatform.org/auth/signin"
        target="_blank"
        rel="noopener"
      >
        TES (Terminology Exchange Service).
      </a>
    </p>
  );
}

function CustomCodeGroupingParagraph() {
  return (
    <p>
      Add codes that are not included in the code sets from the{' '}
      <a
        className="text-blue-cool-60 hover:text-blue-cool-50 underline"
        href="https://tes.tools.aimsplatform.org/auth/signin"
        target="_blank"
        rel="noopener"
      >
        TES (Terminology Exchange Service).
      </a>
    </p>
  );
}

interface ConditionCodeTableProps {
  conditionId: string;
}

function ConditionCodeTable({ conditionId }: ConditionCodeTableProps) {
  const { data: response, isLoading, isError } = useGetCondition(conditionId);
  const [selectedCodeSystem, setSelectedCodeSystem] = useState<string>('all');

  const codes = response?.data.codes ?? [];

  const filteredCodes = codes.filter((code) => {
    return selectedCodeSystem === 'all' || code.system === selectedCodeSystem;
  });

  const { searchText, setSearchText, results } = useSearch(filteredCodes, {
    keys: [
      { name: 'code', weight: 0.7 },
      { name: 'description', weight: 0.3 },
    ],
    includeScore: true,
  });

  // Decide which data to display
  const visibleCodes = searchText ? results.map((r) => r.item) : filteredCodes;

  if (isLoading || !response?.data) return 'Loading...';
  if (isError) return 'Error!';

  function handleCodeSystemSelect(event: React.ChangeEvent<HTMLSelectElement>) {
    setSelectedCodeSystem(event.target.value);
  }

  return (
    <div className="min-w-full">
      <div className="border-bottom-[1px] mb-4 flex min-w-full flex-col items-start gap-6 sm:flex-row sm:items-end">
        <Search
          onChange={(e) => setSearchText(e.target.value)}
          id="code-search"
          name="code-search"
          type="search"
          placeholder="Search code set"
        />
        <div>
          <Label htmlFor="code-system-select">Code system</Label>
          <Select
            id="code-system-select"
            name="code-system-select"
            value={selectedCodeSystem}
            onChange={handleCodeSystemSelect}
          >
            <option key="all-code-systems" value="all">
              All code systems
            </option>
            {response.data.available_systems.map((system) => (
              <option key={system} value={system}>
                {system}
              </option>
            ))}
          </Select>
        </div>
      </div>
      <hr className="border-blue-cool-5 w-full border-[1px]" />
      <div role="region">
        <table
          id="codeset-table"
          className="w-full border-separate border-spacing-y-4"
          aria-label={`Codes in set with ID ${conditionId}`}
        >
          <thead className="sr-only">
            <tr>
              <th>Code</th>
              <th>Code system</th>
              <th>Condition</th>
            </tr>
          </thead>
          <tbody>
            {visibleCodes.map((code) => (
              <ConditionCodeRow
                key={`${code.system}-${code.code}`}
                codeSystem={code.system}
                code={code.code}
                text={code.description}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

interface ConditionCodeRowProps {
  code: string;
  codeSystem: string;
  text: string;
}

function ConditionCodeRow({ code, codeSystem, text }: ConditionCodeRowProps) {
  return (
    <tr>
      <td className="w-1/6">{code}</td>
      <td className="w-1/6"> {codeSystem}</td>
      <td className="w-4/6">{text}</td>
    </tr>
  );
}

interface AddCustomCodeModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: { code: string; system: string; name: string }) => void;
  initialData?: { code: string; system: string; name: string } | null;
}

export function AddCustomCodeModal({
  open,
  onClose,
  onSubmit,
  initialData,
}: AddCustomCodeModalProps) {
  const [code, setCode] = useState(initialData?.code ?? '');
  const [system, setSystem] = useState(initialData?.system ?? '');
  const [name, setName] = useState(initialData?.name ?? '');

  // Reset when modal opens with new initial data
  useEffect(() => {
    if (open) {
      setCode(initialData?.code ?? '');
      setSystem(initialData?.system ?? '');
      setName(initialData?.name ?? '');
    }
  }, [open, initialData]);

  const showToast = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ code, system, name });
    onClose();
    showToast({ heading: 'Custom code added', body: code });
  };

  if (!open) return null;

  return (
    <div className="usa-modal-overlay is-visible flex items-center justify-center">
      <div
        className="usa-modal usa-modal--lg width-auto"
        role="dialog"
        aria-labelledby="add-custom-code-title"
      >
        <div className="usa-modal__content width-auto">
          <main className="usa-modal__main">
            <button
              type="button"
              className="usa-button usa-modal__close"
              aria-label="Close this window"
              onClick={onClose}
            >
              <span aria-hidden="true">×</span>
            </button>
            <h2 id="add-custom-code-title" className="usa-modal__heading">
              Add custom code
            </h2>

            <form className="usa-form usa-prose" onSubmit={handleSubmit}>
              <div className="usa-form-group">
                <label className="usa-label" htmlFor="code">
                  Code #
                </label>
                <input
                  className="usa-input"
                  id="code"
                  name="code"
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                />
              </div>

              <div className="usa-form-group">
                <label className="usa-label" htmlFor="system">
                  Code system
                </label>
                <select
                  className="usa-select"
                  id="system"
                  name="system"
                  value={system}
                  onChange={(e) => setSystem(e.target.value)}
                >
                  <option value="">- Select -</option>
                  <option value="ICD-10">ICD-10</option>
                  <option value="SNOMED">SNOMED</option>
                  <option value="LOINC">LOINC</option>
                  <option value="RXNORM">RxNorm</option>
                  <option value="LOCAL">Local</option>
                </select>
              </div>

              <div className="usa-form-group">
                <label className="usa-label" htmlFor="name">
                  Code name
                </label>
                <input
                  className="usa-input"
                  id="name"
                  name="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>

              <div className="usa-modal__footer">
                <button
                  type="submit"
                  className="usa-button"
                  disabled={!code || !system || !name}
                >
                  Add custom code
                </button>
              </div>
            </form>
          </main>
        </div>
      </div>
    </div>
  );
}
