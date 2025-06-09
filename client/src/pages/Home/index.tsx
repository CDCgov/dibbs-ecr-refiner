import IllustrationImg from '../../assets/home/illustration.svg';
import { Button } from '../../components/Button';

export function Home() {
  return (
    <>
      <div className="bg-blue-cool-10 flex flex-col items-center justify-center gap-16 py-30 lg:flex-row">
        <div className="flex flex-col gap-8 p-10 xl:p-0">
          <div className="flex max-w-[36rem] flex-col items-start gap-4">
            <h1 className="font-merriweather !m-0 !text-5xl font-bold">
              Focus on what matters.
            </h1>
            <p className="text-2xl font-normal">
              eCR Refiner tailors each case report to retain only the data
              jurisdictions need — providing tools for reducing file size,
              increasing data relevancy, and safeguarding sensitive patient
              information.
            </p>
          </div>
          <div>
            <Button className="usa-button usa-button--big" to="/demo">
              Try it out
            </Button>
          </div>
        </div>
        <img src={IllustrationImg} alt="" />
      </div>
      <HowItWorks />
    </>
  );
}

function HowItWorks() {
  return (
    <div className="flex flex-col items-center gap-13 px-10 py-10 xl:px-34">
      <h2 className="text-4xl font-bold text-black">How it works</h2>
      <ol className="flex flex-col gap-6 md:justify-between lg:flex-row">
        <li className="flex items-start gap-6 lg:w-1/3">
          <Number>1</Number>
          <p>
            This early conceptual demonstration of the power of the eCR Refiner
            takes as input a single electronic initial case report (eICR) and
            reportability response (RR) file pair.
          </p>
        </li>
        <li className="flex items-start gap-6 lg:w-1/3">
          <Number>2</Number>
          <p>
            The Refiner extracts the reportable condition(s) from the RR and
            looks up relevant clinical concept codes from APHL's Terminology
            Exchange Service (TES) for each reportable condition.
          </p>
        </li>
        <li className="flex items-start gap-6 lg:w-1/3">
          <Number>3</Number>
          <p>
            The Refiner splits the original eICR into child eICRs - one per
            reportable condition in the RR - and applies a filter that retains
            only the information associated with the relevant clinical concept
            codes identified in the TES for that condition.
          </p>
        </li>
      </ol>
    </div>
  );
}

function Number({ children }: { children: React.ReactNode }) {
  return (
    <>
      <div className="inline-flex min-h-16 min-w-16 flex-col items-center justify-center gap-2.5 rounded-[500px] p-2.5 outline outline-2 outline-offset-[-2px] outline-blue-300">
        <div className="justify-start self-stretch text-center text-3xl font-bold text-blue-300">
          {children}
        </div>
      </div>
    </>
  );
}
