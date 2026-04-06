import { Link } from '@trussworks/react-uswds';
import { Spinner } from '../../components/Spinner';
import { Title } from '../../components/Title';
import Markdown from 'react-markdown';
import { useGetReleases } from '../../api/releases/releases';

export function AppUpdates() {
  const { data: releaseFetchResult, isPending, isError } = useGetReleases();
  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error!';

  const releaseContentToRender = releaseFetchResult.data.releases;
  return (
    <div className="mx-20 my-10">
      <Title className="mb-2!">App updates</Title>
      <p className="mb-6">Review the latest updates to eCR Refiner</p>
      <section className="bg-base-lightest mx-auto rounded-b-lg px-2 py-2">
        {releaseContentToRender.map((d, i) => {
          const summary = d?.release_notes;

          const summaryHeaderValuePairs = summary;
          const dateInfo = new Date(d.created_at);
          return (
            <div key={d.id} className="bg-white px-4 py-4">
              <h3 className="mb-1 text-base font-bold text-black!">
                {dateInfo.toLocaleDateString('en-US', {
                  month: 'long',
                  year: 'numeric',
                })}
              </h3>
              <Link target="_blank" href={d.url}>
                {d.name}
              </Link>
              {summaryHeaderValuePairs.map((summaryContent, summaryIndex) => {
                const content = summaryContent;

                return (
                  <div key={content['id']} className="mt-2 pb-4 pl-5">
                    {summaryIndex == 0 && (
                      <Markdown>{content['content']}</Markdown>
                    )}
                    {summaryIndex == 1 && (
                      <>
                        <h3 className="text-bold -ml-5">Major changes</h3>
                        <Markdown>{content['content']}</Markdown>
                      </>
                    )}
                  </div>
                );
              })}
              {i !== releaseContentToRender.length - 1 && (
                <hr className="bg-base-lighter h-0.5! border-none"></hr>
              )}
            </div>
          );
        })}
      </section>
    </div>
  );
}
