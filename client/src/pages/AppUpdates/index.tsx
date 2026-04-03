import { Link } from '@trussworks/react-uswds';
import { Spinner } from '../../components/Spinner';
import { useGetReleasesData } from '../../api/info/info';
import { Title } from '../../components/Title';
import Markdown from 'react-markdown';
export function AppUpdates() {
  const { data: releaseFetchResult, isPending, isError } = useGetReleasesData();
  if (isPending) return <Spinner variant="centered" />;
  if (isError) return 'Error!';

  const releaseContentToRender = releaseFetchResult.data.releases;
  releaseContentToRender.push(releaseContentToRender[0]);
  return (
    <div className="mx-20 my-10">
      <Title className="mb-2!">App updates</Title>
      <p className="mb-6">Review the latest updates to eCR Refiner</p>
      <section className="bg-base-lightest mx-auto rounded-b-lg px-2 py-2">
        {releaseContentToRender.map((d, i) => {
          // if (d.prerelease) return <></>;
          const summary = d?.body;

          const summaryHeaderValuePairs: Record<string, string> =
            JSON.parse(summary);
          const dateInfo = new Date(d.created_at);
          return (
            <div className="bg-white px-4 py-4">
              <h3 className="mb-1 text-base font-bold text-black!">
                {dateInfo.toLocaleDateString('en-US', {
                  month: 'long',
                  year: 'numeric',
                })}
              </h3>
              <Link target="_blank" href={d.html_url}>
                {d.name}
              </Link>
              {
                /* the two sections have the summary information we want, so only use that content */
                Object.entries(summaryHeaderValuePairs)
                  .slice(0, 2)
                  .map(([, summary_content], content_idx) => {
                    return (
                      <div className="mt-2 pb-4 pl-5">
                        {content_idx == 0 ? (
                          <Markdown>{summary_content}</Markdown>
                        ) : (
                          <>
                            <h3 className="text-bold -ml-5">Major changes</h3>
                            <Markdown>{summary_content}</Markdown>
                          </>
                        )}
                      </div>
                    );
                  })
              }
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
