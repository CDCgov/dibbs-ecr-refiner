import { Title } from '@components/Title';
import { Button } from '@components/Button';
import { Search } from '@components/Search';
import { ConfigurationsTable } from '@components/ConfigurationsTable';
import {
  useCreateConfiguration,
  useGetConfigurations,
} from '../../api/configurations/configurations';
import { useToast } from '../../hooks/useToast';
import { useMemo, useState } from 'react';
import { useGetConditions } from '../../api/conditions/conditions';
import { GetConditionsResponse, UserResponse } from '../../api/schemas';
import { Link, useNavigate } from 'react-router';
import { useApiErrorFormatter } from '../../hooks/useErrorFormatter';
import { useSearch } from '../../hooks/useSearch';
import { Spinner } from '@components/Spinner';
import classNames from 'classnames';
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
import { useGetReleases } from '../../api/releases/releases.ts';
import { updateDismissedNotification } from '../../api/user/user.ts';

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
}

export function Configurations({ user }: ConfigurationsProps) {
  const { data: response, isPending, isError } = useGetConfigurations();
  const configs = useMemo(() => response?.data ?? [], [response?.data]);

  const { data: releaseFetchResult } = useGetReleases();
  const latestRelease = releaseFetchResult?.data.releases?.[0];

  const dismissedMostRecentAppUpdate =
    user.dismissed_notifications?.most_recent_app_update;

  const showAppUpdateBanner =
    latestRelease &&
    (!dismissedMostRecentAppUpdate ||
      new Date(latestRelease.created_at) >
        new Date(dismissedMostRecentAppUpdate));

  const { searchText, setSearchText, results } = useSearch(configs, {
    keys: [{ name: 'name', weight: 1 }],
  });

  const [isOpen, setIsOpen] = useState(false);

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error!';

  const hasMultipleConfigs = configs.length > 0;

  return (
    <>
      {showAppUpdateBanner && latestRelease && (
        <AppUpdateBanner latestReleaseCreatedAt={latestRelease.created_at} />
      )}

      <section className="mx-auto p-3">
        <div className="flex flex-col gap-4 py-10">
          <Title>Configurations</Title>
          <p>
            Configurations define which patient data is included in refined
            eCR’s for each reportable condition
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
  latestReleaseCreatedAt,
}: {
  latestReleaseCreatedAt: string;
}) {
  const [dismissed, setDismissed] = useState(false);

  function handleViewUpdates() {
    void updateDismissedNotification({
      key: 'most_recent_app_update',
      value: latestReleaseCreatedAt,
    }).catch((error) => {
      console.error('Failed to update dismissed notification', error);
    });
  }

  function handleDismiss(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();

    void updateDismissedNotification({
      key: 'most_recent_app_update',
      value: latestReleaseCreatedAt,
    }).catch((error) => {
      console.error('Failed to dismiss notification', error);
    });

    setDismissed(true);
  }

  if (dismissed) return null;

  return (
    <div className="drop-shadow-nav bg-blue-100 px-4 py-3">
      <div className="mx-auto flex max-w-screen-xl items-center">
        {/* Center content */}
        <div className="flex flex-1 items-center justify-center gap-4">
          <div className="flex items-center gap-2">
            <Icon.Info size={3} aria-hidden className="text-blue-40v" />

            <span className="font-public-sans text-[1rem] leading-[1.4rem] font-bold text-blue-500 lining-nums proportional-nums">
              There are new updates to eCR Refiner.
            </span>
          </div>

          <Link
            to="/app-updates"
            onClick={handleViewUpdates}
            className="font-public-sans text-violet-warm-60 border-violet-warm-60 flex h-[44px] items-center justify-center rounded-[4px] border-[2px] bg-white px-[20px] text-center text-[1rem] leading-[1.4rem] font-bold lining-nums proportional-nums no-underline"
          >
            View updates
          </Link>
        </div>

        {/* Dismiss (far right) */}
        <button
          type="button"
          onClick={handleDismiss}
          aria-label="Dismiss notification"
          className="ml-4 flex h-[44px] w-[44px] items-center justify-center rounded hover:bg-blue-200 focus:outline-none"
        >
          <Icon.Close size={3} aria-hidden className="text-blue-500" />
        </button>
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
    useState<GetConditionsResponse | null>(null);
  const [query, setQuery] = useState('');

  const { mutate: createConfig } = useCreateConfiguration();
  const navigate = useNavigate();
  const formatError = useApiErrorFormatter();

  const conditions = response?.data || [];

  const filteredConditions =
    query === ''
      ? conditions
      : conditions.filter((condition) => {
          return condition.display_name
            .toLowerCase()
            .includes(query.toLowerCase());
        });

  function reset() {
    onClose();
    setSelectedCondition(null);
  }

  return (
    <Modal open={open} onClose={reset} position="top">
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
              virtual={{ options: filteredConditions }}
              onChange={setSelectedCondition}
              onClose={() => setQuery('')}
            >
              <ComboboxInput<GetConditionsResponse>
                aria-label="Select condition"
                displayValue={(condition) => condition?.display_name ?? ''}
                onChange={(event) => setQuery(event.target.value)}
                hasValue={!!selectedCondition}
                onClear={() => {
                  setSelectedCondition(null);
                  setQuery('');
                }}
              />
              <ComboboxOptions anchor="bottom">
                {({ option: condition }) => (
                  <ComboboxOption key={condition.id} value={condition}>
                    {condition.display_name}
                  </ComboboxOption>
                )}
              </ComboboxOptions>
            </Combobox>
          </Field>
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
