import { Title } from '../../components/Title';
import { Button } from '../../components/Button';
import { Search } from '../../components/Search';

export function Configurations() {
  return (
    <section className="mx-auto p-3">
      <div className="flex flex-col gap-4 py-10">
        <Title>Your reportable condition configurations</Title>
        <p>
          Set up reportable configurations herer to specifiy the data you'd like
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
        <div>
          <Button>Set up new condition</Button>
        </div>
      </div>
    </section>
  );
}
