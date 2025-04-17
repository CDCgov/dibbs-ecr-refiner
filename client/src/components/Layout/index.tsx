import { Link } from 'react-router';

interface LayoutProps {
  children: React.ReactNode;
}
export function Layout({ children }: LayoutProps) {
  return (
    <div className="p-2 text-white bg-blue-500 min-h-screen flex flex-col gap-4">
      <header className="flex gap-10 items-end">
        <h1 className="text-2xl">DIBBs eCR Refiner</h1>
        <nav className="flex gap-4">
          <Link className="p-1 hover:underline" to="/">
            Home
          </Link>
          <Link className="p-1 hover:underline" to="/about">
            About
          </Link>
        </nav>
      </header>
      <main className="flex flex-1 p-6">{children}</main>
    </div>
  );
}
