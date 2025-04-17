import { Link } from 'react-router';
import UploadSvg from '../../assets/upload.svg';

export default function UploadZip() {
  return (
    <div className="flex flex-col min-w-screen gap-20 px-20">
      <Link className="hover:underline" to="/">
        &#60;-- Return to landing page
      </Link>
      <div className="flex justify-center">
        <div className="min-w-[44rem] px-44 py-8 bg-blue-100 rounded-lg border-1 border-blue-300 border-dashed inline-flex flex-col justify-start items-center gap-6 overflow-hidden">
          <img src={UploadSvg} alt="Upload zipfile" />
          <p className="text-black text-base font-normal">
            We will upload a test file for you to view the refinement results
          </p>
          <button className="text-white px-5 py-3 bg-blue-300 rounded inline-flex justify-center items-center gap-2.5 overflow-hidden cursor-pointer">
            Run test
          </button>
          <a
            className="justify-start text-blue-300 text-base font-bold hover:underline"
            href=""
          >
            Download test file
          </a>
        </div>
      </div>
    </div>
  );
}
