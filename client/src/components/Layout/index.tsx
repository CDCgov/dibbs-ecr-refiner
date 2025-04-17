import { Link } from 'react-router';
import DibbsLogo from '../../assets/dibbs-logo.svg';

interface LayoutProps {
  children: React.ReactNode;
}
export function Layout({ children }: LayoutProps) {
  return (
    <div className="p-2 text-white bg-blue-500 min-h-screen flex flex-col gap-10">
      <header className="flex gap-10 items-end">
        <Link to="/">
          <h1 className="flex gap-3">
            <img src={DibbsLogo} alt="DIBBs" />
            <span className="text-2xl">eCR Refiner</span>
          </h1>
        </Link>
        {/* <nav className="flex gap-4">
          <Link className="p-1 hover:underline" to="/">
            Home
          </Link>
          <Link className="p-1 hover:underline" to="/about">
            About
          </Link>
        </nav> */}
      </header>
      <main className="flex flex-1">{children}</main>
    </div>
  );
}
