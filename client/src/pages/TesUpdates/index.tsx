import { Title } from '@components/Title';
import { useState } from 'react';
import { Button } from '@components/Button';
import classNames from 'classnames';
import { Spinner } from '@components/Spinner';
import { useGetTesUpdates } from '../../api/tes/tes';
import { TesVersionDetails } from './TesVersionDetails';
import { TesUpdate } from '../../api/schemas';
import { UpdateConfigurations } from './UpdateConfigurations';
import { BreakoutContainer } from '@components/Layout';

type UPDATE_STEP = 'summary' | 'action';

export interface TesDiffInformation {
  selected_update: TesUpdate;
  prev_update: TesUpdate | null;
}

export function TesUpdates() {
  const { data: tesUpdates, isPending, isError } = useGetTesUpdates();
  const [tesDiff, setTesDiff] = useState<TesDiffInformation | null>(null);
  const [tesStage, setTesStage] = useState<UPDATE_STEP>('summary');

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error occurred!';

  if (!tesDiff) {
    const newestUpdate = tesUpdates.data.tes_updates[0];
    const prevUpdate =
      tesUpdates.data.tes_updates.length >= 2
        ? tesUpdates.data.tes_updates[1]
        : null;

    setTesDiff({
      selected_update: newestUpdate,
      prev_update: prevUpdate,
    });
  }

  const fetchedTesUpdates = tesUpdates.data.tes_updates;

  return (
    <div className="my-8 flex flex-col">
      {tesStage === 'summary' && (
        <>
          <div className="mb-4 flex justify-between py-4">
            <Title>TES Updates</Title>
            {/*<Button onClick={() => setTesStage('action')}>*/}
            {/*  Update configurations*/}
            {/*</Button>*/}
          </div>

          <div className="flex h-200">
            <UpdateInformation
              tesDiff={tesDiff}
              setTesDiff={setTesDiff}
              fetchedTesUpdates={fetchedTesUpdates}
            />
          </div>
        </>
      )}
      {tesStage === 'action' && (
        <>
          <BreakoutContainer
            background="bg-blue-cool-70"
            className="py-3 text-left text-white"
            maxWidth="max-w-7xl"
          >
            <div className="flex items-center gap-5">
              <Button
                className="cursor-pointer"
                variant="unstyled"
                onClick={() => setTesStage('summary')}
              >
                TES Updates
              </Button>
              {' > Updates'}
            </div>
          </BreakoutContainer>
          <UpdateConfigurations />
        </>
      )}
    </div>
  );
}
interface UpdateInformationProps {
  tesDiff: TesDiffInformation | null;
  setTesDiff: React.Dispatch<React.SetStateAction<TesDiffInformation | null>>;
  fetchedTesUpdates: TesUpdate[];
}

function UpdateInformation({
  tesDiff,
  setTesDiff,
  fetchedTesUpdates,
}: UpdateInformationProps) {
  const dateOptions: Intl.DateTimeFormatOptions = {
    month: '2-digit',
    day: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  };

  return (
    <>
      <div className="bg-blue-cool-5 border-gray-cool-20! flex min-w-30 flex-col overflow-y-auto border-y border-l md:min-w-52">
        <h2 className="text-gray-cool-60 border-gray-cool-20! border-r px-6 pt-4 pb-6 text-sm font-medium uppercase">
          UPDATES HISTORY
        </h2>

        {fetchedTesUpdates.map((t, i) => {
          return (
            <Button
              variant="unstyled"
              key={t.id}
              className={classNames('px-6 py-2 hover:cursor-pointer', {
                'border-l-blue-cool-50 border-y-gray-cool-20! border-y border-l-8 bg-white':
                  t.id === tesDiff?.selected_update?.id,
                'text-blue-cool-60 border-gray-cool-20! border-r px-6 py-2':
                  t.id !== tesDiff?.selected_update?.id,
              })}
              onClick={() =>
                setTesDiff({
                  selected_update: t,
                  prev_update: fetchedTesUpdates[i + 1],
                })
              }
            >
              <div className="text-left">
                <div className="font-bold">Version {t.version}</div>
                {new Date(t.created_at).toLocaleString('en-US', dateOptions)}
              </div>
            </Button>
          );
        })}
        {/* element here to allow border for the un-filled portion of the sidebar */}
        <div
          className="border-gray-cool-20! grow border-r"
          aria-hidden="true"
        />
      </div>
      {tesDiff && <TesVersionDetails selectedUpdate={tesDiff} />}
    </>
  );
}
