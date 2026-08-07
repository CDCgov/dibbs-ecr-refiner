import { Title } from '@components/Title';

export function Overrides() {
  return (
    <div className="flex px-10 md:px-20">
      <div className="flex flex-1 flex-col py-10">
        <div className="mb-6">
          <div className="flex flex-col gap-2">
            <Title>Overrides</Title>
            <p>
              This feature will allow you to configure custom overrides for
              reportable conditions processing.
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
          <h2 className="mb-4 text-2xl font-semibold text-gray-700">
            Coming Soon
          </h2>
          <p className="text-gray-600">
            The Overrides functionality is currently under development and will
            be available in a future release.
          </p>
        </div>
      </div>
    </div>
  );
}
