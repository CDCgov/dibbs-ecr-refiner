import { useState } from 'react';
import { Title } from '@components/Title';
import { SimulatorUploadResponse } from '../../api/schemas';
import { Diff } from '@components/Diff';
import { Select, SelectContainer } from '@components/Select';
import { Field } from '@components/Field';
import { Label } from '@components/Label';

type SuccessProps = Pick<
  SimulatorUploadResponse,
  'refined_conditions' | 'refined_download_key' | 'unrefined_eicr'
>;

type Condition = SuccessProps['refined_conditions'][0];

export function Success({
  refined_conditions,
  unrefined_eicr,
  refined_download_key,
}: SuccessProps) {
  // defaults to first condition found
  const [selectedCondition, setSelectedCondition] = useState<Condition>(
    refined_conditions[0]
  );

  function onChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const value = e.currentTarget.value;
    const newSelectedCondition = refined_conditions.find(
      (c) => c.code === value
    );

    if (!newSelectedCondition) return selectedCondition;

    setSelectedCondition(newSelectedCondition);
  }

  return (
    <div>
      <div className="flex place-items-center justify-between gap-4 pr-2">
        <Title>eCR refinement results</Title>
        <SelectContainer>
          <Field>
            <Label className="text-bold">CONDITION:</Label>
            <Select defaultValue={selectedCondition.code} onChange={onChange}>
              {refined_conditions.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.display_name}
                </option>
              ))}
            </Select>
          </Field>
        </SelectContainer>
      </div>
      <Diff
        condition={selectedCondition}
        unrefined_eicr={unrefined_eicr}
        refined_download_key={refined_download_key}
        renderDiff={selectedCondition.render_diff}
      />
    </div>
  );
}
