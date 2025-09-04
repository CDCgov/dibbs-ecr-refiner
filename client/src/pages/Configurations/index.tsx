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
  ModalToggleButton,
  Modal,
  ModalHeading,
  ModalFooter,
  Label,
  ComboBox,
  ModalRef,
  ComboBoxRef,
} from '@trussworks/react-uswds';
import { useRef, useState } from 'react';
import { useGetConditions } from '../../api/conditions/conditions';
import { GetConditionsResponse } from '../../api/schemas';
import { useNavigate } from 'react-router';
import { useApiErrorFormatter } from '../../hooks/useErrorFormatter';

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
  const { data: response, isLoading } = useGetConfigurations();
  const modalRef = useRef<ModalRef>(null);

  if (isLoading || !response?.data) return 'Loading...';

  return (
    <section className="mx-auto p-3">
      <div className="flex flex-col gap-4 py-10">
        <Title>Your reportable condition configurations</Title>
        <p>
          Set up reportable configurations here to specifiy the data you'd like
          to retain in the refined eCRs for that condition.
        </p>
      </div>
      <div className="flex flex-col justify-between gap-10 sm:flex-row sm:items-start">
        <Search
          placeholder="Search configurations"
          id="search-configurations"
          name="search"
          type="text"
        />
        <ModalToggleButton
          modalRef={modalRef}
          opener
          className="!bg-violet-warm-60 hover:!bg-violet-warm-70 !m-0"
        >
          Set up new condition
        </ModalToggleButton>
        <NewConfigModal modalRef={modalRef} />
      </div>
      <ConfigurationsTable
        columns={{ name: 'Reportable condition', status: 'Status' }}
        data={response.data.map((config) => ({
          id: config.id,
          name: config.name,
          status: config.is_active ? 'on' : 'off',
        }))}
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
  const { data: response, isLoading } = useGetConditions();
  const [selectedCondition, setSelectedCondition] =
    useState<GetConditionsResponse | null>(null);

  const { mutateAsync } = useCreateConfiguration();
  const navigate = useNavigate();
  const formatError = useApiErrorFormatter();

  return (
    <Modal
      ref={modalRef}
      id="add-configuration-modal"
      aria-labelledby="add-configuration-modal-heading"
      aria-describedby="add-configuration-modal-description"
      className="pb-5 !align-top"
    >
      <ModalHeading
        id="add-configuration-modal-heading"
        className="font-merriweather !text-3xl !leading-18 font-bold text-black"
      >
        Set up new condition
      </ModalHeading>
      <p id="add-configuration-modal-description" className="sr-only">
        Select a reportable condition you'd like to configure.
      </p>
      <Label htmlFor="new-condition" className="!leading-6" data-focus="true">
        Condition
      </Label>
      {isLoading || !response?.data ? (
        'Loading...'
      ) : (
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
      )}
      <ModalFooter className="flex justify-self-end">
        <Button
          variant={`${selectedCondition ? 'primary' : 'disabled'}`}
          disabled={!selectedCondition}
          onClick={async () => {
            if (!selectedCondition) return;
            try {
              await mutateAsync(
                { data: { condition_id: selectedCondition.id } },
                {
                  onSuccess: async (resp) => {
                    await navigate(`/configurations/${resp.data.id}/build`);
                    comboBoxRef.current?.clearSelection();
                    modalRef.current?.toggleModal();
                    showToast({
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
            } catch {
              // no-op: handled in onError
            }
          }}
        >
          Add condition
        </Button>
      </ModalFooter>
    </Modal>
  );
}
