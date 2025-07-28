import { Title } from '../../components/Title';
import { Button } from '../../components/Button';
import { Search } from '../../components/Search';
import { ConfigurationsTable } from '../../components/ConfigurationsTable';

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
        id: 'chlamydia-id',
      },
      {
        name: 'Disease caused by Enterovirus',
        status: ConfigurationStatus.off,
        id: 'enterovirus-id',
      },
      {
        name: 'Human immunodeficiency virus infection (HIV)',
        status: ConfigurationStatus.off,
        id: 'hiv-id',
      },
      {
        name: 'Syphilis',
        status: ConfigurationStatus.on,
        id: 'syphilis-id',
      },
      {
        name: 'Viral hepatitis, type A',
        status: ConfigurationStatus.on,
        id: 'viral-hep-id',
      },
    ],
  };

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
        <Button className="m-0!">Set up new condition</Button>
      </div>
      <ConfigurationsTable columns={tableData.columns} data={tableData.data} />
    </section>
  );
}
