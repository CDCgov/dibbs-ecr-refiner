import { useGetTesUpdates } from '../../api/tes-updates/tes-updates';

export function TesUpdates() {
  const { data: tesUpdates, isPending, isError } = useGetTesUpdates();
  if (isPending) return 'Loading...';
  if (isError) return 'Error occurred!';

  return (
    <>
      {tesUpdates.data.tes_updates.map((t) => {
        return (
          <div key={t.id}>
            <span>{t.created_at}</span>
            <span>{t.version}</span>
          </div>
        );
      })}
    </>
  );
}
