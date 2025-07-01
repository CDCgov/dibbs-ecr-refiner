import { NavLink } from 'react-router';

export default function NavigationBar() {
  return (
    <nav
      aria-label="Primary navigation"
      className="usa-nav flex min-w-[632px] flex-row place-content-end text-center text-lg text-white"
    >
      <NavigationLink location="/" title="Configurations" />
      <NavigationLink location="/testing" title="Testing" />
    </nav>
  );
}

interface NavigationLinkProps {
  location: string;
  title: string;
}

/**
 * NavigationLink is a function that wraps React Router's NavLink in a super generic way.
 */
function NavigationLink({ location, title }: NavigationLinkProps) {
  return (
    <NavLink to={location}>
      {({ isActive /* , isPending, isTransitioning  */ }) => (
        <span
          className={`mx-6 inline-block py-1 ${isActive ? 'border-b-4' : ''}`}
        >
          {title}
        </span>
      )}
    </NavLink>
  );
}
