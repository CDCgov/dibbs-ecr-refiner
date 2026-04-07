import { Title } from '../../components/Title';
import { Button } from '../../components/Button';
import { Search } from '../../components/Search';
import { ConfigurationsTable } from '../../components/ConfigurationsTable';
import {
  useCreateConfiguration,
  useGetConfigurations,
} from '../../api/configurations/configurations';
import { useToast } from '../../hooks/useToast';

import {
  Label as USWDSLabel,
  ComboBox,
  ComboBoxRef,
} from '@trussworks/react-uswds';
import { useMemo, useRef, useState } from 'react';
import { useGetConditions } from '../../api/conditions/conditions';
import { GetConditionsResponse } from '../../api/schemas';
import { useNavigate } from 'react-router';
import { useApiErrorFormatter } from '../../hooks/useErrorFormatter';
import { useSearch } from '../../hooks/useSearch';
import { Spinner } from '../../components/Spinner';
import classNames from 'classnames';
import {
  Modal,
  ModalBody,
  ModalHeader,
  ModalTitle,
  ModalFooter,
} from '../../components/Modal';

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

export function Configurations() {
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
    <section className="mx-auto p-3">
      <div className="flex flex-col gap-4 py-10">
        <Title>Configurations</Title>
        <p>
          Configurations define which patient data is included in refined eCR’s
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
          Set up a new configuration
        </Button>
        <NewConfigModal open={isOpen} onClose={() => setIsOpen(false)} />
      </div>
      <ConfigurationsTable
        data={searchText ? results.map((r) => r.item) : configs}
      />
    </section>
  );
}

interface NewConfigModalProps {
  open: boolean;
  onClose: () => void;
}

function NewConfigModal({ open, onClose }: NewConfigModalProps) {
  const showToast = useToast();
  const comboBoxRef = useRef<ComboBoxRef>(null);
  const { data: response, isPending, isError } = useGetConditions();
  const [selectedCondition, setSelectedCondition] =
    useState<GetConditionsResponse | null>(null);

  const { mutate: createConfig } = useCreateConfiguration();
  const navigate = useNavigate();
  const formatError = useApiErrorFormatter();

  return (
    <Modal open={open} onClose={onClose} position="top">
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
          <div>
            <USWDSLabel
              htmlFor="new-condition"
              className="leading-6!"
              data-focus="true"
            >
              Select condition
            </USWDSLabel>
            <ComboBox
              id="new-condition"
              ref={comboBoxRef}
              name="new-condition"
              options={response?.data.map((condition) => ({
                value: condition.id,
                label: condition.display_name,
              }))}
              onChange={(conditionId) => {
                const found =
                  response.data.find((c) => c.id === conditionId) ?? null;
                setSelectedCondition(found);
              }}
            />
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
                  comboBoxRef.current?.clearSelection();
                  showToast({
                    heading: 'New configuration created',
                    body: selectedCondition?.display_name ?? '',
                  });
                  setSelectedCondition(null);
                },
                onError: (e) => {
                  showToast({
                    heading: 'Configuration could not be created',
                    variant: 'error',
                    body: formatError(e),
                  });
                  comboBoxRef.current?.clearSelection();
                  setSelectedCondition(null);
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
