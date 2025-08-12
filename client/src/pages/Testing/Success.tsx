import { useState } from 'react';
import SuccessSvg from '../../assets/green-check.svg';
import { Label, Select } from '@trussworks/react-uswds';
import { Title } from '../../components/Title';
import { RefinedTestingDocument } from '../../api/schemas';
import { Button } from '../../components/Button';
import { Diff } from '../../components/Diff';

type SuccessProps = Pick<
  RefinedTestingDocument,
  'conditions' | 'refined_download_url' | 'unrefined_eicr'
>;

type Condition = SuccessProps['conditions'][0];

export function Success({
  conditions,
  unrefined_eicr,
  refined_download_url,
}: SuccessProps) {
  // defaults to first condition found
  const [selectedCondition, setSelectedCondition] = useState<Condition>(
    conditions[0]
  );

  function onChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const value = e.currentTarget.value;
    const newSelectedCondition = conditions.find((c) => c.code === value);

    if (!newSelectedCondition) return selectedCondition;

    setSelectedCondition(newSelectedCondition);
  }

  return (
    <div>
      <div className="flex items-center gap-4">
        <Title>eCR refinement results</Title>
        <Label htmlFor="condition-select" className="text-bold">
          CONDITION:
        </Label>
        <Select
          id="condition-select"
          name="condition-select"
          defaultValue={selectedCondition.code}
          onChange={onChange}
        >
          {conditions.map((c) => (
            <option key={c.code} value={c.code}>
              {c.display_name}
            </option>
          ))}
        </Select>
      </div>
      <Diff
        condition={selectedCondition}
        unrefinedEicr={unrefined_eicr}
        presignedDownloadUrl={refined_download_url}
      />
    </div>
  );
}
