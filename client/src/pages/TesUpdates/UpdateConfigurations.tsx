import { Table } from '@components/Table';
import { Title } from '@components/Title';
import { useGetConfigurationsToUpdate } from '../../api/tes/tes';
import { Spinner } from '@components/Spinner';
import { Checkbox } from '@components/Checkbox';
import { Button } from '@components/Button';

export function UpdateConfigurations() {
  const {
    data: response,
    isPending,
    isError,
    // todo don't hard code this
  } = useGetConfigurationsToUpdate({ cur_tes_version: '6.0.0' });

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error!';

  const drafts_to_create = response.data.drafts_to_create;
  const existing_drafts = response.data.existing_drafts;

  return (
    <div>
      <Title className="pb-4">Update configurations</Title>
      <h2 className="text-[1.25rem]">Update to latest release</h2>
      <p>
        Update existing drafts and/or create a for existing configurations to
        apply the latest TES release. Drafts will need to be activated in order
        to receive the most up to date eCRs.
      </p>
      <div className="bg-white px-10 py-6">
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
                <Checkbox />
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
                    <Checkbox />
                    {d.configuration_name}
                  </td>{' '}
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
                <Checkbox />
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
                    <Checkbox />
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
