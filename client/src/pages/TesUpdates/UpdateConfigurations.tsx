import { Table } from '@components/Table';
import { Title } from '@components/Title';
import { useGetConfigurationsToUpdate } from '../../api/tes/tes';
import { Spinner } from '@components/Spinner';

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

  console.log(drafts_to_create, existing_drafts);

  return (
    <div>
      <div className="bg-blue-cool-70 -mx-20 -mt-8 mb-8 px-20 py-3 text-white">
        {'Tes Updates > Updates'}{' '}
      </div>
      <Title className="pb-4">Update configurations</Title>
      <h2 className="text-[1.25rem]">Update to latest release</h2>
      <p>
        Update existing drafts and/or create a for existing configurations to
        apply the latest TES release. Drafts will need to be activated in order
        to receive the most up to date eCRs.
      </p>

      <h3>Update existing drafts</h3>
      <Table fullWidth>
        <thead>
          <tr>
            <th scope="col" className="bg-white! font-bold">
              Configuration
            </th>
            <th scope="col" className="bg-white! font-bold">
              Current TES version
            </th>
            <th scope="col" className="bg-white! font-bold">
              Code sets
            </th>
          </tr>
        </thead>
        <tbody>
          {drafts_to_create.map((d) => {
            return (
              <tr key={d.configuration_id}>
                <td>{d.configuration_name}</td>
                <td>{d.configuration_tes_version}</td>
                <td>{d.codesets_to_update.join(', ')}</td>
              </tr>
            );
          })}
        </tbody>
      </Table>

      <h3>Create Draft To Update</h3>
      <Table fullWidth>
        <thead>
          <tr>
            <th scope="col" className="bg-white! font-bold">
              Configuration
            </th>
            <th scope="col" className="bg-white! font-bold">
              Current TES version
            </th>
            <th scope="col" className="bg-white! font-bold">
              Code sets
            </th>
          </tr>
        </thead>
        <tbody>
          {existing_drafts.map((d) => {
            return (
              <tr key={d.configuration_id}>
                <td>{d.configuration_name}</td>
                <td>{d.configuration_tes_version}</td>
                <td>{d.codesets_to_update.join(', ')}</td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    </div>
  );
}
