import { Link } from 'react-router';

export function LandingPageLink() {
  return (
    <Link
      className="flex items-center gap-2 self-start text-blue-300 underline-offset-4 hover:underline"
      to="/"
    >
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="fill-blue-300"
      >
        <path
          fill-rule="evenodd"
          clip-rule="evenodd"
          d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z"
        />
      </svg>
      <span>Return to landing page</span>
    </Link>
  );
}
