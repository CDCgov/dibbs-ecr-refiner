import { ExternalLink } from '@components/ExternalLink';
import {
  useExportConditionDiff,
  useGetTesDiffDetails,
} from '../../api/tes/tes';
import { Spinner } from '@components/Spinner';
import { TesDiffInformation } from '.';
import { Button } from '@components/Button';

interface TesVersionProps {
  selectedUpdate: TesDiffInformation;
}

export function TesVersionDetails({ selectedUpdate }: TesVersionProps) {
  const newVersion = selectedUpdate.selected_update.version;
  const oldVersion = selectedUpdate.prev_update
    ? selectedUpdate.prev_update.version
    : '';

  const {
    data: response,
    isPending,
    isError,
  } = useGetTesDiffDetails({
    cur_version: newVersion,
    prev_version: oldVersion,
  });

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error!';

  return (
    <div className="border-gray-cool-20! grow overflow-y-scroll border-y border-r bg-white p-8">
      <h3 className="font-bold">
        What's changed in Version {selectedUpdate?.selected_update.version}
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
            <th className="px-2 py-3" />
          </tr>
        </thead>
        <tbody className="divide-gray-cool-20 divide-y">
          {response.data.map((r) => {
            const shouldShowNewConditionPill =
              // don't show pill if oldVersion is undefined (the "baseline" config)
              // since everything in that version would be a new condition
              r.is_new && oldVersion != '';
            return (
              <tr key={r.canonical_url}>
                <td className="px-2 py-3">
                  {r.display_name}{' '}
                  {shouldShowNewConditionPill ? <NewConditionPill /> : null}
                </td>
                <td className="px-2 py-3">
                  {r.added_code_total} added, {r.removed_code_total} removed
                </td>
                <td>
                  <ExportLink
                    cond_canonical_url={r.canonical_url}
                    cur_tes_version={newVersion}
                    prev_tes_version={oldVersion}
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function NewConditionPill() {
  return (
    <span className="bg-state-success-lighter rounded-2xl px-2 py-1 font-mono text-sm">
      New condition
    </span>
  );
}

interface ExportLinkProps {
  cond_canonical_url: string;
  cur_tes_version: string;
  prev_tes_version: string;
}
function ExportLink({
  cond_canonical_url,
  cur_tes_version,
  prev_tes_version,
}: ExportLinkProps) {
  const params = new URLSearchParams({
    cond_canonical_url: cond_canonical_url,
    cur_tes_version: cur_tes_version,
    prev_tes_version: prev_tes_version,
  });

  return (
    <Button
      href={`/api/v1/tes/export?${params.toString()}`}
      anchorProps={{ download: true }}
      variant="tertiary"
    >
      Export as CSV
    </Button>
  );
}
