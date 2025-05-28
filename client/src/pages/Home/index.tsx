import { Link } from 'react-router';
import DibbsLogo from '../../assets/dibbs-logo.svg';
import PlaceholderImg from '../../assets/home/placeholder.png';

export function Home() {
  return (
    <div>
      <div className="p-10">
        <header className="flex items-center">
          <Link to="/">
            <h1 className="flex gap-3">
              <img src={DibbsLogo} alt="DIBBs" />
              <span className="font-merriweather text-2xl">eCR Refiner</span>
            </h1>
          </Link>
        </header>
      </div>
      <main>
        <div className="flex flex-col items-center justify-center gap-16 p-6 md:flex-row md:p-16">
          <div className="flex flex-col gap-8">
            <div className="flex max-w-[28rem] flex-col items-start gap-4">
              <h1 className="font-merriweather text-4xl font-bold">
                Focus on what matters.
              </h1>
              <p className="text-xl font-normal">
                This demo application is a proof-of-concept for the eCR Refiner,
                a collaborative effort between the Centers for Disease Control
                (CDC) and the Association of Public Health Labs (APHL) to create
                a centrally-accessible web application for eCR refinement hosted
                on APHL's Information Management System (AIMS). The eCR Refiner
                tailors each case report to retain only the data jurisdictions
                need — providing tools for reducing file size, increasing data
                relevancy, and safeguarding sensitive patient information. The
                filtering capability showcased in this proof-of-concept will be
                expanded to include user-defined elements such as custom codes,
                section-based filtering, and time-based filtering.
              </p>
            </div>
            <div>
              <Link className="usa-button" to="/demo">
                Try it out
              </Link>
            </div>
          </div>
          <div>
            <img className="max-h-[500px]" src={PlaceholderImg} alt="" />
          </div>
        </div>
        <HowItWorks />
      </main>
    </div>
  );
}

function HowItWorks() {
  return (
    <div className="flex flex-col items-center gap-6 gap-13 bg-blue-100 px-6 py-20 lg:px-34">
      <h2 className="text-4xl font-bold text-black">How it works</h2>
      <ol className="flex flex-col gap-10 md:flex-row md:justify-between">
        <li className="flex items-start gap-6">
          <Number>1</Number>
          <p>
            This early conceptual demonstration of the power of the eCR Refiner
            takes as input a single electronic initial case report (eICR) and
            reportability response (RR) file pair.
          </p>
        </li>
        <li className="flex items-start gap-6">
          <Number>2</Number>
          <p>
            The Refiner extracts the reportable condition(s) from the RR and
            looks up relevant clinical concept codes from APHL's Terminology
            Exchange Service (TES) for each reportable condition.
          </p>
        </li>
        <li className="flex items-start gap-6">
          <Number>3</Number>
          <p>
            The Refiner splits the original eICR into child eICRs - one per
            reportable condition in the RR - and applies a filter that retains
            only the information associated with the relevant clinical concept
            codes identified in the TES.
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
