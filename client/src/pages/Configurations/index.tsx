import { Title } from '../../components/Title';
import { Button } from '../../components/Button';
import { Search } from '../../components/Search';

const title = `Your reportable condition configurations`;
const subtitle = `Set up reportable configurations herer to specifiy the data you'd like to retain in the refined eCRs for that condition.`;

export function Configurations() {
  return (
    <section className="usa-container mx-auto max-w-[1203px]">
      <div className="flex flex-col gap-4 py-10">
        <Title>{title}</Title>
        <p>{subtitle}</p>
      </div>
      <div className="flex flex-row justify-between gap-10">
        <Search placeholder='Search configurations' />
        <Button>Set up new condition</Button>
      </div>
    </section>
  );
}
