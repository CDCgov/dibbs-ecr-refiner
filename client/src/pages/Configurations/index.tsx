import { Title } from '@components/Title';
import { Button } from '@components/Button';
import { ConfigurationsTable } from '@components/ConfigurationsTable';
import {
  useCreateConfiguration,
  useGetConfigurations,
} from '../../api/configurations/configurations';
import { useToast } from '../../hooks/useToast';
import { useMemo, useState } from 'react';
import { useGetConditions } from '../../api/conditions/conditions';
import {
  ConditionSummary,
  NotificationKeys,
  UserResponse,
} from '../../api/schemas';
import { useNavigate } from 'react-router';
import { useApiErrorFormatter } from '../../hooks/useErrorFormatter';
import { Spinner } from '@components/Spinner';
import {
  Modal,
  ModalBody,
  ModalHeader,
  ModalTitle,
  ModalFooter,
} from '@components/Modal';
import {
  Combobox,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from '@components/Combobox';
import { Label } from '@components/Label';
import { Field } from '@components/Field';
import { Icon } from '@trussworks/react-uswds';
import { useUpdateUserNotifications } from '../../api/app-notifications/app-notifications';
import { useSearch } from '../../hooks/useSearch';
import { RangeTuple } from 'fuse.js';
import classNames from 'classnames';
import { Search } from '@components/Search';

enum ConfigurationStatus {
  on = 'on',
  off = 'off',
}

interface ConfigurationsData {
  name: string;
  status: ConfigurationStatus;
  id: string;
}

interface ConfigurationsColumns {
  [key: string]: string;
}

interface ConfigurationsTable {
  columns: ConfigurationsColumns;
  data: ConfigurationsData[];
}

interface ConfigurationsProps {
  user: UserResponse;
  refreshUser: () => void;
}

const MIN_CONFIG_SEARCH_TEXT_LENGTH = 3;

export function Configurations({ user, refreshUser }: ConfigurationsProps) {
  const { data: response, isPending, isError } = useGetConfigurations();
  const configs = useMemo(() => response?.data ?? [], [response?.data]);

  const { searchText, setSearchText, results } = useSearch(configs, {
    keys: [{ name: 'name', weight: 1 }],
  });

  const [isOpen, setIsOpen] = useState(false);

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error!';

  const hasMultipleConfigs = configs.length > 0;

  return (
    <>
      <AppUpdateBanner
        isVisible={
          user.notifications.to_render[
            NotificationKeys.most_recent_app_update
          ] ?? false
        }
        refreshUser={refreshUser}
      />
      <section className="mx-auto p-3">
        <div className="flex flex-col gap-4 py-10">
          <Title>Configurations</Title>
          <p>
            Configurations define which patient data is included in refined eCRs
            for each reportable condition
          </p>
        </div>
        <div
          className={classNames(
            'flex flex-col gap-10 sm:flex-row sm:items-start',
            {
              'justify-between': hasMultipleConfigs,
              'justify-end': !hasMultipleConfigs,
            }
          )}
        >
          {hasMultipleConfigs ? (
            <Search
              placeholder="Search configurations"
              id="search-configurations"
              name="search"
              onChange={(e) => setSearchText(e.target.value)}
            />
          ) : null}

          <Button className="m-0!" onClick={() => setIsOpen(true)}>
            Set up new configuration
          </Button>
          <NewConfigModal open={isOpen} onClose={() => setIsOpen(false)} />
        </div>
        <ConfigurationsTable
          data={searchText ? results.map((r) => r.item) : configs}
        />
      </section>
    </>
  );
}

function AppUpdateBanner({
  isVisible,
  refreshUser,
}: {
  isVisible: boolean;
  refreshUser: () => void;
}) {
  const navigate = useNavigate();
  const { mutateAsync } = useUpdateUserNotifications();

  if (!isVisible) {
    return null;
  }

  async function dismissNotification() {
    try {
      await mutateAsync({
        data: {
          key: NotificationKeys.most_recent_app_update,
        },
      });
      refreshUser();
    } catch (error) {
      console.error('Failed to update user notifications', error);
    }
  }
  async function handleViewUpdates(e: React.MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
    await dismissNotification();
    void navigate('/app-updates');
  }
  async function handleDismiss() {
    await dismissNotification();
  }

  return (
    <div className="drop-shadow-nav bg-blue-100 px-4 py-3">
      <div className="mx-auto flex max-w-7xl items-center">
        <div className="flex flex-1 items-center justify-center gap-4">
          <div className="flex items-center gap-2">
            <Icon.Info size={3} aria-hidden className="text-blue-40v" />
            <span className="font-public-sans text-[1rem] leading-[1.4rem] font-bold text-blue-500 lining-nums proportional-nums">
              There are new updates to eCR Refiner.
            </span>
          </div>
          <Button
            variant="secondary"
            to="/app-updates"
            onClick={(e) => handleViewUpdates(e)}
          >
            View updates
          </Button>
        </div>

        <Button
          type="button"
          onClick={handleDismiss}
          aria-label="Dismiss notification"
          variant="unstyled"
          className="ml-4 flex h-11 w-11 items-center justify-center rounded hover:cursor-pointer hover:opacity-75 focus:outline-none"
        >
          <Icon.Close size={3} aria-hidden className="text-blue-500" />
        </Button>
      </div>
    </div>
  );
}

interface NewConfigModalProps {
  open: boolean;
  onClose: () => void;
}

function NewConfigModal({ open, onClose }: NewConfigModalProps) {
  const showToast = useToast();
  const { data: response, isPending, isError } = useGetConditions();

  const [selectedCondition, setSelectedCondition] =
    useState<ConditionSummary | null>(null);

  const { mutate: createConfig } = useCreateConfiguration();
  const navigate = useNavigate();
  const formatError = useApiErrorFormatter();

  const conditions = response?.data || [];
  const { searchText, setSearchText, results } = useSearch(
    conditions,
    {
      keys: [
        { name: 'display_name' },
        { name: 'rsg_codes.display' },
        { name: 'rsg_codes.code' },
      ],
      threshold: 0.25,
      distance: 500, // Broaden the distance so Fuse doesn't penalize long strings
      includeMatches: true,
      findAllMatches: true,
    },
    true
  );
  const searchTextLongEnough =
    searchText.length > MIN_CONFIG_SEARCH_TEXT_LENGTH;
  const hasSearchResultsToDisplay = searchTextLongEnough && results;

  function reset() {
    onClose();
    setSelectedCondition(null);
  }

  return (
    <Modal open={open} onClose={reset} position="center" maxWidth="xl">
      <ModalHeader>
        <ModalTitle>Set up new configuration</ModalTitle>
      </ModalHeader>
      <ModalBody>
        <p className="sr-only">
          Select a reportable condition you'd like to configure.
        </p>
        {isPending ? (
          <Spinner />
        ) : isError ? (
          <p className="text-state-error-dark">
            Failed to load conditions. Please try again.
          </p>
        ) : (
          <Field>
            <Label>Select condition</Label>
            <Combobox
              value={selectedCondition}
              virtual={{
                options: searchTextLongEnough
                  ? results.map((r) => r.item)
                  : conditions,
              }}
              onChange={setSelectedCondition}
              onClose={() => setSearchText('')}
            >
              <ComboboxInput<ConditionSummary>
                aria-label="Select condition"
                displayValue={(condition) => condition?.display_name ?? ''}
                onChange={(event) =>
                  setSearchText(prepareSearchTextForFuse(event.target.value))
                }
                hasValue={!!selectedCondition}
                onClear={() => {
                  setSelectedCondition(null);
                  setSearchText('');
                }}
                placeholder="Start typing to search (3 characters minimum)"
              />
              <ComboboxOptions anchor="bottom">
                {({ option: condition }) => (
                  <ComboboxOption key={condition.id} value={condition}>
                    {hasSearchResultsToDisplay
                      ? results
                          .filter((r) => r.item.id === condition.id)
                          .map(({ item, matches }) => {
                            const conditionDisplayMatch = matches?.find(
                              (m) => m.key === 'display_name'
                            );
                            const rsgMatches = matches?.filter(
                              (m) =>
                                m.key === 'rsg_codes.display' ||
                                m.key === 'rsg_codes.code'
                            );

                            return (
                              <div key={item.id}>
                                <p className="pb-2 font-bold">
                                  {conditionDisplayMatch
                                    ? highlightMatches(
                                        item.display_name,
                                        conditionDisplayMatch?.indices
                                      )
                                    : item.display_name}
                                </p>

                                <div>
                                  {rsgMatches?.map((r) => {
                                    const matchedCode =
                                      item.rsg_codes[r.refIndex as number];
                                    const isDisplayMatch =
                                      r.key === 'rsg_codes.display';
                                    const isCodeMatch =
                                      r.key === 'rsg_codes.code';
                                    return (
                                      <div className="flex justify-between">
                                        <div>⤷</div>
                                        <p className="ml-1 flex-2 pb-2">
                                          {isDisplayMatch
                                            ? highlightMatches(
                                                matchedCode.display,
                                                r?.indices
                                              )
                                            : `${matchedCode.display}`}
                                        </p>
                                        <p className="flex-1 text-right">
                                          {isCodeMatch
                                            ? highlightMatches(
                                                matchedCode.code,
                                                r?.indices
                                              )
                                            : matchedCode.code}
                                        </p>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            );
                          })
                      : condition.display_name}
                  </ComboboxOption>
                )}
              </ComboboxOptions>
            </Combobox>
          </Field>
        )}

        {selectedCondition && (
          <div>
            <p className="pb-2">Selected condition group</p>

            <div className="border-gray-cool-30! rounded-sm border px-2 py-2">
              <p className="font-bold">{selectedCondition.display_name}</p>
              <table className="w-full border-separate border-spacing-y-0.5">
                <colgroup>
                  <col className="w-[65%]" />
                  <col className="w-[35%]" />
                </colgroup>
                <thead className="sr-only">
                  <tr>
                    <th scope="col">Display name</th>
                    <th scope="col">Code</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedCondition.rsg_codes.map((c) => {
                    return (
                      <tr key={c.code}>
                        <td>{c.display}</td>
                        <td className="text-right align-top">{c.code}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </ModalBody>
      <ModalFooter align="right">
        <Button
          variant="primary"
          disabled={!selectedCondition}
          onClick={() => {
            if (!selectedCondition) return;
            createConfig(
              { data: { condition_id: selectedCondition.id } },
              {
                onSuccess: async (resp) => {
                  await navigate(`/configurations/${resp.data.id}/build`);

                  showToast({
                    heading: 'New configuration created',
                    body: selectedCondition?.display_name ?? '',
                  });
                  reset();
                },
                onError: (e) => {
                  showToast({
                    heading: 'Configuration could not be created',
                    variant: 'error',
                    body: formatError(e),
                  });
                },
              }
            );
          }}
        >
          Set up configuration
        </Button>
      </ModalFooter>
    </Modal>
  );
}

function prepareSearchTextForFuse(s: string) {
  if (s.length < MIN_CONFIG_SEARCH_TEXT_LENGTH) {
    return '';
  }

  const NUMERIC_ONLY_STRING = new RegExp(/^\d+/i);
  if (NUMERIC_ONLY_STRING.test(s)) {
    // on return exact prefix matches when search string is a code search (purely numeric)
    return `^${s}`;
  }
  return s;
}

function highlightMatches(
  text: string,
  regions: readonly RangeTuple[] | undefined
) {
  if (!regions || !regions.length) return text;

  const chunks = [];
  let lastIndex = 0;

  // Fuse.js returns sorted, non-overlapping [start, end] pairs
  for (const [start, end] of regions) {
    // Add any unmatched text before this region
    if (start > lastIndex) {
      chunks.push(text.slice(lastIndex, start));
    }
    // Wrap the matched range in a <mark> tag
    chunks.push(<mark key={start}>{text.slice(start, end + 1)}</mark>);
    lastIndex = end + 1;
  }

  // Add any remaining text after the last match
  if (lastIndex < text.length) {
    chunks.push(text.slice(lastIndex));
  }

  return chunks;
}
