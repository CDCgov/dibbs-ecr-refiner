import { Title } from '../../components/Title';
import { Button } from '../../components/Button';
import { Search } from '../../components/Search';
import { ConfigurationsTable } from '../../components/ConfigurationsTable';

import {
  ModalToggleButton,
  Modal,
  ModalHeading,
  ModalFooter,
  ModalRef,
  Form,
  Label,
  ComboBox,
  ComboBoxRef,
} from '@trussworks/react-uswds';
import { SyntheticEvent, useRef, useState } from 'react';

enum ConfigurationStatus {
  on = 'on',
  off = 'off',
}

interface SelectedCondition {
  value: string;
  label: string;
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
  const [table, setTable] = useState<ConfigurationsTable>({
    columns: { name: 'Reportable condition', status: 'Status' },
    data: [],
  });

  const conditionData = {
    // TODO: Figure out what this data should look like and require using real
    // UUIDs since keys need to be unique.
    '3d7fb83d-d664-4b82-a0fb-3f8decd307cc': 'Anaplasmosis',
    '1be0a722-ead6-4a54-ad90-e83c139ceb3c': 'Chlamydia trachomatis infection',
    '0c157c35-b9a2-431f-badc-9ee0ea12003f': 'Gonorrhea',
    'f0365ece-3ec7-486a-ba73-7f5d1de64ca8': 'HIV',
    '985fc9f8-86dc-4e12-95f1-b7457b3497ca': 'Syphilis',
  };

  const conditionList = Object.entries(conditionData).map(([id, name]) => ({
    value: id,
    label: name,
  }));

  const modalRef = useRef<ModalRef>(null);
  const listRef = useRef<ComboBoxRef>(null);

  const [formValid, setFormValid] = useState<boolean>(false);
  const [condition, setCondition] = useState<SelectedCondition | undefined>(
    undefined
  );

  function handleSubmit(e: SyntheticEvent) {
    e.preventDefault();
    if (!condition) {
      return;
    }

    const newData: ConfigurationsData = {
      name: condition.label,
      id: condition.value,
      status: ConfigurationStatus.off,
    };
    setTable((prevTable) => ({
      ...prevTable,
      data: [...prevTable.data, newData],
    }));

    modalRef.current?.toggleModal();
    listRef.current?.clearSelection();
  }
  function handleChange(selectedValue: string | undefined) {
    if (selectedValue) {
      const selectedOption = conditionList.find(
        (option) => option.value === selectedValue
      );
      setCondition(selectedOption);
      setFormValid(true);
    } else {
      setCondition(undefined);
      setFormValid(false);
    }
  }

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
          id={'search-configurations'}
          name={'search'}
          type={'text'}
        />
        <ModalToggleButton
          modalRef={modalRef}
          opener
          className="!bg-violet-warm-60 hover:!bg-violet-warm-70 !m-0"
        >
          Set up new condition
        </ModalToggleButton>
        <Modal
          ref={modalRef}
          id="add-configuration-modal"
          aria-labelledby="add-configuration-modal-heading"
          className="pb-5 !align-top"
        >
          <ModalHeading
            id="add-configuration-modal-heading"
            className="font-merriweather !text-3xl !leading-18 font-bold text-black"
          >
            Set up new condition
          </ModalHeading>
          <Form onSubmit={handleSubmit}>
            <Label
              htmlFor="new-condition"
              className="!leading-6"
              data-focus="true"
            >
              Condition
            </Label>
            <ComboBox
              ref={listRef}
              id="new-condition"
              name="new-condition"
              options={conditionList}
              onChange={handleChange}
            />
            <ModalFooter className="flex justify-self-end">
              <Button
                type="submit"
                className={`!m-0 ${formValid ? 'button-enabled' : 'button-disabled'}`}
                disabled={!formValid}
              >
                Add condition
              </Button>
            </ModalFooter>
          </Form>
        </Modal>
      </div>
      <ConfigurationsTable columns={table.columns} data={table.data} />
    </section>
  );
}
