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
} from '@trussworks/react-uswds';
import { SyntheticEvent, useRef, useState } from 'react';

enum ConfigurationStatus {
  on = 'on',
  off = 'off',
}

export function Configurations() {
  const tableData = {
    columns: { name: 'Reportable condition', status: 'Status' },
    data: [
      {
        name: 'Chlamydia trachomatis infection',
        status: ConfigurationStatus.on,
        id: 'asdf-zxcv-qwer-hjkl',
      },
      {
        name: 'Disease caused by Enterovirus',
        status: ConfigurationStatus.off,
        id: 'asdf-zxcv-qwer-hjkl',
      },
      {
        name: 'Human immunodeficiency virus infection (HIV)',
        status: ConfigurationStatus.off,
        id: 'asdf-zxcv-qwer-hjkl',
      },
      {
        name: 'Syphilis',
        status: ConfigurationStatus.on,
        id: 'asdf-zxcv-qwer-hjkl',
      },
      {
        name: 'Viral hepatitis, type A',
        status: ConfigurationStatus.on,
        id: 'asdf-zxcv-qwer-hjkl',
      },
    ],
  };

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

  const [formValid, setFormValid] = useState(false);

  function handleSubmit(e: SyntheticEvent) {
    // e.preventDefault();
  }
  function handleChange(e: string | undefined) {
    setFormValid(e !== undefined);
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
          aria-describedby="add-configuration-modal-description"
          className="pb-5 !align-top"
        >
          <ModalHeading
            id="add-configuration-modal-heading"
            className="font-merriweather !text-3xl !leading-18 font-bold text-black"
          >
            Set up new condition
          </ModalHeading>
          <Form onSubmit={handleSubmit}>
            <Label htmlFor="new-condition" className="!leading-6">
              Condition
            </Label>
            <ComboBox
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
      <ConfigurationsTable columns={tableData.columns} data={tableData.data} />
    </section>
  );
}
