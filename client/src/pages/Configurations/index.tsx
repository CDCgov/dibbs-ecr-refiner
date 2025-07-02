import { Title } from '../../components/Title';
import { Button } from '../../components/Button';
import { Search } from '../../components/Search';

const title = `Your reportable condition configurations`;
const subtitle = `Set up reportable configurations herer to specifiy the data you'd like to retain in the refined eCRs for that condition.`;

export function Configurations() {
  return (
    <section className="mx-auto p-3">
      <div className="flex flex-col gap-4 py-10">
        <Title>{title}</Title>
        <p>{subtitle}</p>
      </div>
      <div className="flex flex-col justify-between gap-10 sm:flex-row sm:items-start">
        <Search placeholder="Search configurations" />
        <div>
          <Button>Set up new condition</Button>
        </div>
      </div>
    </section>
  );
}
