import { NavLink } from 'react-router';

export default function NavigationBar() {
  return (
    <nav
      aria-label="Primary navigation"
      className="usa-nav flex justify-end !text-lg text-white"
    >
      <NavigationLink location="/" title="Configurations" />
      <NavigationLink location="/testing" title="Testing" />
    </nav>
  );
}

type NavigationLinkProps = Pick<NavLinkProps, 'to' | 'title'>;

/**
 * NavigationLink is a function that wraps React Router's NavLink in a super generic way.
 */
function NavigationLink({ location, title }: NavigationLinkProps) {
  return (
    <NavLink to={location}>
      {({ isActive }) => (
        <span
          className={classNames('mx-6 inline-block py-1', {
            'border-b-4': isActive,
          })}
        >
          {title}
        </span>
      )}
    </NavLink>
  );
}
