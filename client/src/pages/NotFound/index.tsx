import { Link } from 'react-router';

export default function NotFound() {
  return (
    <main>
      <p>Page not found</p>
      <Link to="/" className="font-bold text-blue-300 hover:underline">
        Return to homepage
      </Link>
    </main>
  );
}
