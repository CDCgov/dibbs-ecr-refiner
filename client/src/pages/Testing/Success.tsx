import { useState } from 'react';
import { Label, Select } from '@trussworks/react-uswds';
import { Title } from '@components/Title';
import { IndependentTestUploadResponse } from '../../api/schemas';
import { Diff } from '@components/Diff';

type SuccessProps = Pick<
  IndependentTestUploadResponse,
  'refined_conditions' | 'refined_download_key' | 'unrefined_eicr'
> & {
  renderDict: { [conditionName: string]: boolean };
};

type Condition = SuccessProps['refined_conditions'][0];

export function Success({
  refined_conditions,
  unrefined_eicr,
  refined_download_key,
  renderDict,
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
      <div className="flex place-items-center justify-between gap-4">
        <Title>eCR refinement results</Title>
        <div className="w-80">
          <Label htmlFor="condition-select" className="text-bold">
            CONDITION:
          </Label>
          <Select
            id="condition-select"
            name="condition-select"
            defaultValue={selectedCondition.code}
            onChange={onChange}
          >
            {refined_conditions.map((c) => (
              <option key={c.code} value={c.code}>
                {c.display_name}
              </option>
            ))}
          </Select>
        </div>
      </div>
      <Diff
        condition={selectedCondition}
        unrefined_eicr={unrefined_eicr}
        refined_download_key={refined_download_key}
        renderDiff={renderDict[selectedCondition.display_name]}
      />
    </div>
  );
}
