import { ExternalLink } from '@components/ExternalLink';
import { useGetTesDiffDetails } from '../../api/tes/tes';
import { Spinner } from '@components/Spinner';
import { TesDiffInformation } from '.';
import { Button } from '@components/Button';
import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
} from '@components/Table';

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

      <Table>
        <TableHead className="border-b-gray-cool-20 border-b">
          <TableRow className="text-gray-cool-60 w-1/2 text-left font-bold">
            <TableHeaderCell className="px-2 py-3" scope="col">
              Condition code set
            </TableHeaderCell>
            <TableHeaderCell className="px-2 py-3">Change</TableHeaderCell>
            <TableHeaderCell className="px-2 py-3" />
          </TableRow>
        </TableHead>
        <TableBody className="divide-gray-cool-20 divide-y">
          {response.data.map((r) => {
            const shouldShowNewConditionPill =
              // don't show pill if oldVersion is undefined (the "baseline" config)
              // since everything in that version would be a new condition
              r.is_new && oldVersion != '';
            return (
              <TableRow key={r.canonical_url}>
                <TableCell className="px-2 py-3">
                  {r.display_name}{' '}
                  {shouldShowNewConditionPill ? <NewConditionPill /> : null}
                </TableCell>
                <TableCell className="px-2 py-3">
                  {r.added_code_total} added, {r.removed_code_total} removed
                </TableCell>
                <TableCell>
                  <ExportLink
                    canonical_url={r.canonical_url}
                    cur_version={newVersion}
                    prev_version={oldVersion}
                  />
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
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
  canonical_url: string;
  cur_version: string;
  prev_version: string;
}
function ExportLink({
  canonical_url,
  cur_version,
  prev_version,
}: ExportLinkProps) {
  const params = new URLSearchParams({
    canonical_url: canonical_url,
    cur_version: cur_version,
    prev_version: prev_version,
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
