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
  Modal,
  ModalHeading,
  ModalFooter,
  Label,
  ComboBox,
  ModalRef,
  ComboBoxRef,
} from '@trussworks/react-uswds';
import { useMemo, useRef, useState } from 'react';
import { useGetConditions } from '../../api/conditions/conditions';
import { GetConditionsResponse } from '../../api/schemas';
import { useNavigate } from 'react-router';
import { useApiErrorFormatter } from '../../hooks/useErrorFormatter';
import { useSearch } from '../../hooks/useSearch';
import { CONFIGURATION_CONFIRMATION_CTA, CONFIGURATION_CTA } from './utils';
import { Spinner } from '../../components/Spinner';
import classNames from 'classnames';
import { ModalToggleButton } from '../../components/Button/ModalToggleButton';

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

  const modalRef = useRef<ModalRef>(null);

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error!';

  const hasMultipleConfigs = configs.length > 0;

  return (
    <section className="mx-auto p-3">
      <div className="flex flex-col gap-4 py-10">
        <Title>Your reportable condition configurations</Title>
        <p>
          Set up reportable condition configurations here to specify the data
          you'd like to retain in the refined eCRs for that condition.
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

        <ModalToggleButton
          modalRef={modalRef}
          opener
          className="bg-violet-warm-60! hover:bg-violet-warm-70! m-0!"
        >
          {CONFIGURATION_CTA}
        </ModalToggleButton>
        <NewConfigModal modalRef={modalRef} />
      </div>
      <ConfigurationsTable
        data={searchText ? results.map((r) => r.item) : configs}
      />
    </section>
  );
}

interface NewConfigModalProps {
  modalRef: React.RefObject<ModalRef | null>;
}

function NewConfigModal({ modalRef }: NewConfigModalProps) {
  const showToast = useToast();
  const comboBoxRef = useRef<ComboBoxRef>(null);
  const { data: response, isPending, isError } = useGetConditions();
  const [selectedCondition, setSelectedCondition] =
    useState<GetConditionsResponse | null>(null);

  const { mutate: createConfig } = useCreateConfiguration();
  const navigate = useNavigate();
  const formatError = useApiErrorFormatter();

  return (
    <Modal
      ref={modalRef}
      id="add-configuration-modal"
      aria-labelledby="add-configuration-modal-heading"
      aria-describedby="add-configuration-modal-description"
      className="!align-top md:p-0 md:pb-5"
    >
      <ModalHeading
        id="add-configuration-modal-heading"
        className="font-merriweather !text-3xl !leading-18 font-bold text-black"
      >
        {CONFIGURATION_CTA}
      </ModalHeading>
      <p id="add-configuration-modal-description" className="sr-only">
        Select a reportable condition you'd like to configure.
      </p>
      {isPending ? (
        <Spinner />
      ) : isError ? (
        <p className="text-state-error-dark">
          Failed to load conditions. Please try again.
        </p>
      ) : (
        <>
          <Label
            htmlFor="new-condition"
            className="!leading-6"
            data-focus="true"
          >
            Select condition
          </Label>
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
        </>
      )}
      <ModalFooter className="flex justify-self-end">
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
                  modalRef.current?.toggleModal();
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
                  modalRef.current?.toggleModal();
                  setSelectedCondition(null);
                },
              }
            );
          }}
        >
          {CONFIGURATION_CONFIRMATION_CTA}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
