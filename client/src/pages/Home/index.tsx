import { Link } from 'react-router';
import DibbsLogo from '../../assets/dibbs-logo.svg';
import VideoPlaceholder from '../../assets/video-placeholder.svg';
import { Button } from '../../components/Button';

export function Home() {
  return (
    <div>
      <div className="p-10">
        <header className="flex items-center gap-20">
          <Link to="/">
            <h1 className="flex gap-3">
              <img src={DibbsLogo} alt="DIBBs" />
              <span className="font-merriweather text-2xl">eCR Refiner</span>
            </h1>
          </Link>
        </header>
      </div>
      <main>
        <div className="flex flex-col justify-center gap-16 p-30 md:flex-row">
          <div className="flex flex-col gap-8">
            <div className="flex max-w-[28rem] flex-col items-start gap-4">
              <h1 className="font-merriweather text-4xl font-bold">
                Focus on what matters.
              </h1>
              <p className="text-xl font-normal">
                eCR Refiner tailors each case report to show only the data you
                need—reducing file size, increasing efficiency, and safeguarding
                sensitive patient information.
              </p>
            </div>
            <div>
              <Button color="blue" to="/demo">
                Try it out
              </Button>
            </div>
          </div>
          <div>
            <img src={VideoPlaceholder} alt="" />
          </div>
        </div>
        <HowItWorks />
      </main>
    </div>
  );
}

// TODO: Revist this when there's content
function HowItWorks() {
  return (
    <div className="justify-items-center bg-blue-100 px-34 py-20">
      <div>
        <h2 className="text-4xl font-bold text-black">How it works</h2>
      </div>
    </div>
  );
}
