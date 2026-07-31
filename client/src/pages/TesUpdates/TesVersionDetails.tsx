import { ExternalLink } from '@components/ExternalLink';
import { TesUpdate } from '../../api/schemas';
import { useGetTesUpdateDiff } from '../../api/tes/tes';
import { Spinner } from '@components/Spinner';

interface TesVersionProps {
  selectedUpdate: TesUpdate;
}

export function TesVersionDetails({ selectedUpdate }: TesVersionProps) {
  const {
    data: response,
    isPending,
    isError,
    // todo: don't hard code this
  } = useGetTesUpdateDiff({ cur_version: '6.0.0', prev_version: '5.0.0' });

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error!';

  return (
    <div className="border-gray-cool-20! h-160 grow overflow-y-scroll border-y border-r bg-white p-8">
      <h3 className="font-bold">
        What's changed in Version {selectedUpdate?.version}
      </h3>
      <p className="pb-6">
        These code sets come from the{' '}
        <ExternalLink href="https://tes.tools.aimsplatform.org/">
          TES (Terminology Exchange Service)
        </ExternalLink>
      </p>

      <table className="w-full">
        <thead className="border-b-gray-cool-20 border-b">
          <tr className="text-gray-cool-60 w-1/2 text-left font-bold">
            <th className="px-2 py-3" scope="col">
              Condition code set
            </th>
            <th className="px-2 py-3">Change</th>
          </tr>
        </thead>
        <tbody className="divide-gray-cool-20 divide-y">
          {response &&
            response.data.map((r) => {
              return (
                <tr key={r.canonical_url}>
                  <td className="px-2 py-3">{r.display_name}</td>
                  <td className="px-2 py-3">
                    {r.added_code_total} added, {r.removed_code_total} removed
                  </td>
                </tr>
              );
            })}
        </tbody>
      </table>
    </div>
  );
}
