import { Spinner } from '../../components/Spinner';
import { Title } from '../../components/Title';

export function Uploading() {
  return (
    <div className="bg-blue-cool-5 border-blue-cool-20 flex w-[44rem] flex-col items-center rounded border border-dashed px-20 py-8">
      <div className="flex flex-col items-center gap-3">
        <Title>Uploading...</Title>
        <Spinner size={50} />
      </div>
    </div>
  );
}
