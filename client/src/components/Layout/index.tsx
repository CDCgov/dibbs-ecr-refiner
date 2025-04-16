import { Link } from 'react-router';

interface LayoutProps {
  children: React.ReactNode;
}
export function Layout({ children }: LayoutProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        minWidth: '100%',
        padding: '1rem',
      }}
    >
      <header>
        <h1>DIBBs eCR Refiner</h1>
      </header>
      <nav style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
        <Link to="/">Home</Link>
        <Link to="/about">About</Link>
      </nav>
      <main>{children}</main>
      <footer>footer</footer>
    </div>
  );
}
