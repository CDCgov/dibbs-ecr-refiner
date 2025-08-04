import { Title } from '../../components/Title';
import { Button } from '../../components/Button';
import { Search } from '../../components/Search';
import { ConfigurationsTable } from '../../components/ConfigurationsTable';
import { useGetConfigurations } from '../../api/configurations/configurations';

export function Configurations() {
  const { data, isLoading } = useGetConfigurations();

  if (isLoading || !data?.data) return 'Loading...';

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
        <Button className="m-0!">Set up new condition</Button>
      </div>
      <ConfigurationsTable
        columns={{ name: 'Reportable condition', status: 'Status' }}
        data={data.data.map(({ id, name, is_active }) => ({
          id,
          name,
          status: is_active ? 'on' : 'off',
        }))}
      />
    </section>
  );
}
