import { useParams } from 'react-router';
import NotFound from '../NotFound';
import { Title } from '../../components/Title';
import { Button } from '../../components/Button';

export default function ConfigurationDetail() {
  const { id } = useParams<{ id: string }>();

  if (!id) return <NotFound />;

  return (
    <div>
      <div className="flex flex-col gap-4 bg-white px-8 pt-8 pb-6 shadow-lg sm:flex-row sm:justify-between sm:px-20">
        <div>
          <Title>Name</Title>
          <p>{id}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary">Export</Button>
          <Button>Test &gt;</Button>
        </div>
      </div>
      <section className="px-8 pt-8 pb-6 sm:px-20">
        <div>test</div>
      </section>
    </div>
  );
}
