import classNames from 'classnames';
import { NavLink, NavLinkProps } from 'react-router';

export default function NavigationBar() {
  return (
    <nav
      aria-label="Primary navigation"
      className="!text-md flex justify-end gap-4 text-white"
    >
      <NavigationLink to="/configurations" title="Configurations" />
      <NavigationLink to="/testing" title="Testing" />
    </nav>
  );
}

type NavigationLinkProps = Pick<NavLinkProps, 'to' | 'title'>;

/**
 * NavigationLink is a function that wraps React Router's NavLink in a super generic way.
 */
function NavigationLink({ to, title }: NavigationLinkProps) {
  return (
    <NavLink to={to} className="text-blue-cool-5">
      {({ isActive }) => (
        <span
          className={classNames(
            'hover:border-blue-cool-30 mx-6 inline-block py-1 hover:border-b-4 ',
            {
              'border-blue-cool-30 border-b-4 font-semibold': isActive,
            }
          )}
        >
          {title}
        </span>
      )}
    </NavLink>
  );
}
