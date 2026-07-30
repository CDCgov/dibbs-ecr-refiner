import { Title } from '@components/Title';
import { useState } from 'react';
import { Button } from '@components/Button';
import classNames from 'classnames';
import { TesUpdate } from '../../api/schemas/tesUpdate';
import { Spinner } from '@components/Spinner';
import { useGetTesUpdates } from '../../api/tes/tes';
import { TesVersionDetails } from './TesVersionDetails';

export function TesUpdates() {
  const { data: tesUpdates, isPending, isError } = useGetTesUpdates();
  const [selectedUpdate, setSelectedUpdate] = useState<TesUpdate | null>(null);

  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error occurred!';

  if (!selectedUpdate) {
    setSelectedUpdate(tesUpdates.data.tes_updates[0]);
  }
  const dateOptions: Intl.DateTimeFormatOptions = {
    month: '2-digit',
    day: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  };

  return (
    <div className="my-8 flex flex-col gap-6 px-2 md:px-20">
      <Title>TES Updates</Title>

      <div className="flex">
        <div className="bg-blue-cool-5 border-gray-cool-20! flex h-160 max-h-160 min-w-30 flex-col overflow-y-scroll border-y border-l md:min-w-52">
          <h2 className="text-gray-cool-60 border-gray-cool-20! border-r px-6 pt-4 pb-6 text-sm font-medium uppercase">
            UPDATES HISTORY
          </h2>

          {tesUpdates.data.tes_updates.map((t) => {
            return (
              <Button
                variant="unstyled"
                key={t.id}
                className={classNames('px-6 py-2 hover:cursor-pointer', {
                  'border-l-blue-cool-50 border-y-gray-cool-20! border-y border-l-8 bg-white':
                    t.id === selectedUpdate?.id,
                  'text-blue-cool-60 border-gray-cool-20! border-r px-6 py-2':
                    t.id !== selectedUpdate?.id,
                })}
                onClick={() => setSelectedUpdate(t)}
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
        {selectedUpdate && (
          <TesVersionDetails selectedUpdate={selectedUpdate} />
        )}
      </div>
    </div>
  );
}
