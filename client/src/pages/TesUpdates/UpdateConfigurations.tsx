import { Table } from '@components/Table';
import { Title } from '@components/Title';
import { useGetConfigurationsToUpdate } from '../../api/tes/tes';
import { Spinner } from '@components/Spinner';
import { Checkbox } from '@components/Checkbox';
import { Button } from '@components/Button';
import { useState } from 'react';

export function UpdateConfigurations() {
  const { data: response, isPending, isError } = useGetConfigurationsToUpdate();

  const [selectedConfigurations, setSelectedConfigurations] = useState<
    string[]
  >([]);

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error!';

  const drafts_to_create = response.data.drafts_to_create;
  const existing_drafts = response.data.existing_drafts;

  function handleIndividualSelection(configurationId: string) {
    if (selectedConfigurations.includes(configurationId)) {
      setSelectedConfigurations(
        selectedConfigurations.filter((c) => c !== configurationId)
      );
    } else {
      setSelectedConfigurations([...selectedConfigurations, configurationId]);
    }
  }

  function handleBulkSelection(
    selectionType: 'existing_drafts' | 'drafts_to_create'
  ) {
    const draftsToHandle = (
      selectionType === 'drafts_to_create' ? drafts_to_create : existing_drafts
    ).map((d) => d.configuration_id);

    const someDraftInSelection = draftsToHandle.some((c) => {
      return selectedConfigurations.includes(c);
    });

    if (someDraftInSelection) {
      // deselect all
      setSelectedConfigurations(
        selectedConfigurations.filter((s) => !draftsToHandle.includes(s))
      );
    } else {
      // add all the relevant items in
      setSelectedConfigurations((prev) => [
        ...new Set([...prev, ...draftsToHandle]),
      ]);
    }
  }

  return (
    <div>
      <Title className="pb-4">Update configurations</Title>
      <h2 className="mb-1 text-[1.25rem]">Update to latest release</h2>
      <p className="max-w-[35%]">
        Update existing drafts and/or create a for existing configurations to
        apply the latest TES release. Drafts will need to be activated in order
        to receive the most up to date eCRs.
      </p>
      <div className="mt-4 bg-white px-10 py-6 lg:max-w-[75%]">
        <Table className="mt-0 mb-4 border-none">
          <caption className="text-lg! font-bold">
            Update existing drafts
          </caption>
          <thead>
            <tr>
              <th
                scope="col"
                className="flex items-center gap-2 bg-white! pl-0! font-bold"
              >
                <Checkbox
                  onClick={() => {
                    handleBulkSelection('existing_drafts');
                  }}
                  checked={existing_drafts.some((c) =>
                    selectedConfigurations.includes(c.configuration_id)
                  )}
                  aria-label="Bulk select existing drafts"
                />
                Configuration
              </th>
              <th scope="col" className="bg-white! pl-0! font-bold">
                Current TES version
              </th>
              <th scope="col" className="bg-white! pl-0! font-bold">
                Code sets
              </th>
            </tr>
          </thead>
          <tbody>
            {existing_drafts.map((d) => {
              return (
                <tr key={d.configuration_id}>
                  <td className="flex items-center gap-2 pl-0!">
                    <Checkbox
                      onClick={() => {
                        handleIndividualSelection(d.configuration_id);
                      }}
                      checked={selectedConfigurations.includes(
                        d.configuration_id
                      )}
                      aria-label={`Select ${d.configuration_name}`}
                    />
                    {d.configuration_name}
                  </td>
                  <td className="pl-0!">{d.configuration_tes_version}</td>
                  <td className="pl-0!">{d.codesets_to_update.join(', ')}</td>
                </tr>
              );
            })}
          </tbody>
        </Table>

        <Table className="mt-0 mb-4 border-none">
          <caption className="mb-0 text-lg! font-bold">
            Create Draft To Update
          </caption>
          <thead>
            <tr>
              <th
                scope="col"
                className="flex items-center gap-2 bg-white! pl-0! font-bold"
              >
                {' '}
                <Checkbox
                  checked={drafts_to_create.some((c) =>
                    selectedConfigurations.includes(c.configuration_id)
                  )}
                  onClick={() => {
                    handleBulkSelection('drafts_to_create');
                  }}
                  aria-label="Bulk select drafts to create"
                />
                Configuration
              </th>
              <th scope="col" className="bg-white! pl-0! font-bold">
                Current TES version
              </th>
              <th scope="col" className="bg-white! pl-0! font-bold">
                Code sets
              </th>
            </tr>
          </thead>
          <tbody>
            {drafts_to_create.map((d) => {
              return (
                <tr key={d.configuration_id}>
                  <td className="flex items-center gap-2 pl-0!">
                    <Checkbox
                      onClick={() => {
                        handleIndividualSelection(d.configuration_id);
                      }}
                      checked={selectedConfigurations.includes(
                        d.configuration_id
                      )}
                      aria-label={`Select ${d.configuration_name}`}
                    />
                    {d.configuration_name}
                  </td>
                  <td className="pl-0!">{d.configuration_tes_version}</td>
                  <td className="pl-0!">{d.codesets_to_update.join(', ')}</td>
                </tr>
              );
            })}
          </tbody>
        </Table>

        <Button>Apply updates</Button>
      </div>
    </div>
  );
}
